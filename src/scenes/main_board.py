"""メインボード画面"""
import random
import pyxel
from src.scenes.scene_base import Scene
from src.ui.input_helper import btnp
from src.core.rules import SCREEN_WIDTH, SCREEN_HEIGHT, LAND_FEE_RATE, COMPANY_FEE_RATE
from src.core.game_state import GameState, GamePhase
from src.core.company_model import Company
from src.core.card_logic import get_random_card, get_shop_cards, get_normal_cards
from src.core.event_logic import check_events, apply_event, get_news_content, get_sponsors
from src.core.ai import AIPlayer
from src.views.topview.board_view import TopViewBoardView
from src.views.topview.player_view import TopViewPlayerView
from src.ui.dialog import Dialog, ConfirmDialog
from src.ui.menu import Menu
from src.ui.hud import HUD
from src.ui.animation import DiceAnimation, MoveAnimation
from src.utils.save_manager import save_game


class SubPhase:
    NONE = "none"
    DICE_ANIM = "dice_anim"
    DICE_RESULT = "dice_result"
    MOVING = "moving"
    MOVE_ANIM = "move_anim"
    BRANCH = "branch"
    TILE_ACTION = "tile_action"
    DIALOG = "dialog"
    CONFIRM = "confirm"
    MENU = "menu"
    EVENT_DISPLAY = "event_display"
    REVENUE_DISPLAY = "revenue_display"
    WAITING_AI = "waiting_ai"
    CARD_SELECT = "card_select"


class MainBoardScene(Scene):
    def __init__(self):
        super().__init__()
        self.game_state = None
        self.board_view = None
        self.player_view = None
        self.hud = HUD()
        self.dialog = Dialog()
        self.confirm = ConfirmDialog()
        self.menu = Menu()
        self.dice_anim = DiceAnimation()
        self.move_anim = MoveAnimation()
        self.company_types = []
        self.characters = []
        self.ai_players = {}
        self.sub_phase = SubPhase.NONE
        self.command_selected = 0
        self.commands = ["Dice", "Data", "Card"]
        self.ai_timer = 0
        self.moving_player_pos = None
        self.pending_action = None

    def enter(self, **kwargs):
        self.game_state = kwargs.get("game_state")
        self.company_types = kwargs.get("company_types", [])
        self.characters = kwargs.get("characters", [])

        self.board_view = TopViewBoardView(self.game_state.board)
        self.player_view = TopViewPlayerView()

        # AI初期化
        self.ai_players = {}
        for p in self.game_state.players:
            if not p.is_human:
                char_data = next(
                    (c for c in self.characters if c["id"] == p.character_id),
                    None
                )
                if char_data:
                    self.ai_players[p.id] = AIPlayer(char_data["ai_params"])
                else:
                    self.ai_players[p.id] = AIPlayer({})

        self.sub_phase = SubPhase.NONE
        self._start_turn()

    def _start_turn(self):
        gs = self.game_state
        gs.phase = GamePhase.TURN_START

        # オートセーブ
        save_game(gs)

        # イベント判定
        events = check_events(gs.turn_number)
        if events:
            messages = []
            for event in events:
                msg = apply_event(event, gs)
                messages.append(msg)
            gs.event_results = messages

        # ニュース判定
        if gs.is_news_turn():
            self.change_scene("news", game_state=gs,
                              company_types=self.company_types,
                              characters=self.characters)
            return

        # 偶数ターン損益
        if gs.is_even_turn():
            results = gs.process_even_turn_revenue()
            if results:
                gs.event_results.extend(results)

        # 勝利判定
        if gs.check_victory():
            self.change_scene("ending", game_state=gs)
            return

        # イベント表示
        if gs.event_results:
            self.sub_phase = SubPhase.EVENT_DISPLAY
            self._show_event_messages(0)
        else:
            self._start_player_turn()

    def _show_event_messages(self, index):
        if index < len(self.game_state.event_results):
            msg = self.game_state.event_results[index]
            self.dialog.show(msg, lambda: self._show_event_messages(index + 1))
            self.sub_phase = SubPhase.DIALOG
        else:
            self.game_state.event_results = []
            self._start_player_turn()

    def _start_player_turn(self):
        gs = self.game_state
        player = gs.current_player
        gs.phase = GamePhase.PLAYER_COMMAND
        self.command_selected = 0
        self.sub_phase = SubPhase.NONE

        player.tick_slow_debuff()

        if not player.is_human:
            self.sub_phase = SubPhase.WAITING_AI
            self.ai_timer = 15

    def update(self):
        gs = self.game_state
        player = gs.current_player

        # アニメーション更新
        self.dice_anim.update()
        self.move_anim.update()

        # ダイアログ
        if self.dialog.visible:
            self.dialog.update()
            return
        if self.confirm.visible:
            self.confirm.update()
            return
        if self.menu.visible:
            self.menu.update()
            return

        # AI処理
        if self.sub_phase == SubPhase.WAITING_AI:
            self.ai_timer -= 1
            if self.ai_timer <= 0:
                self._ai_act()
            return

        # 移動アニメーション
        if self.sub_phase == SubPhase.MOVE_ANIM:
            if self.move_anim.is_done:
                self._continue_movement()
            return

        # サイコロアニメーション
        if self.sub_phase == SubPhase.DICE_ANIM:
            return

        # サイコロ結果表示
        if self.sub_phase == SubPhase.DICE_RESULT:
            if btnp(pyxel.KEY_RETURN) or btnp(pyxel.KEY_Z):
                self.sub_phase = SubPhase.MOVING
                self._start_movement()
            return

        # プレイヤーコマンド選択
        if gs.phase == GamePhase.PLAYER_COMMAND and player.is_human:
            if btnp(pyxel.KEY_LEFT):
                self.command_selected = (self.command_selected - 1) % len(self.commands)
            if btnp(pyxel.KEY_RIGHT):
                self.command_selected = (self.command_selected + 1) % len(self.commands)
            if btnp(pyxel.KEY_RETURN) or btnp(pyxel.KEY_Z) or btnp(pyxel.KEY_SPACE):
                self._execute_command(self.command_selected)

        # 分岐選択
        if self.sub_phase == SubPhase.BRANCH:
            return  # メニューで処理

    def _execute_command(self, cmd_index):
        if cmd_index == 0:  # Dice
            self._roll_dice()
        elif cmd_index == 1:  # Data
            self._show_data()
        elif cmd_index == 2:  # Card
            self._use_card()

    def _roll_dice(self):
        gs = self.game_state
        value = gs.roll_dice()
        self.sub_phase = SubPhase.DICE_ANIM
        self.dice_anim.start_roll(value, on_complete=lambda: self._on_dice_done())

    def _on_dice_done(self):
        self.sub_phase = SubPhase.DICE_RESULT

    def _start_movement(self):
        player = self.game_state.current_player
        if player.remaining_moves <= 0:
            self._on_movement_complete()
            return

        tile = self.game_state.board.get_tile(player.position)
        next_tiles = tile.next_tiles

        if len(next_tiles) > 1:
            # 分岐
            items = [f"Route {chr(65 + i)}" for i in range(len(next_tiles))]
            self.sub_phase = SubPhase.BRANCH
            self.menu.show(items, 60, 100, on_select=self._on_branch_select, title="Select Route")
            return

        if len(next_tiles) == 0:
            self._on_movement_complete()
            return

        # 移動アニメーション
        from_pos = self.board_view.tile_screen_pos(player.position)
        next_id = next_tiles[0]
        to_pos = self.board_view.tile_screen_pos(next_id)
        player.position = next_id
        player.remaining_moves -= 1
        player.stats.tiles_moved += 1
        self.sub_phase = SubPhase.MOVE_ANIM
        self.move_anim.start_move(from_pos, to_pos)

    def _continue_movement(self):
        player = self.game_state.current_player
        if player.remaining_moves <= 0:
            self._on_movement_complete()
        else:
            self._start_movement()

    def _on_branch_select(self, index):
        if index < 0:
            return
        player = self.game_state.current_player
        tile = self.game_state.board.get_tile(player.position)
        from_pos = self.board_view.tile_screen_pos(player.position)
        next_id = tile.next_tiles[index]
        to_pos = self.board_view.tile_screen_pos(next_id)
        player.position = next_id
        player.remaining_moves -= 1
        player.stats.tiles_moved += 1
        self.sub_phase = SubPhase.MOVE_ANIM
        self.move_anim.start_move(from_pos, to_pos)

    def _on_movement_complete(self):
        """移動完了→マス処理"""
        gs = self.game_state
        player = gs.current_player
        tile = gs.board.get_tile(player.position)
        action = gs.get_tile_action_type(tile, player)

        if action == "plus":
            player.add_money(tile.plus_minus_amount)
            self.dialog.show(
                f"+{tile.plus_minus_amount}$ received!",
                lambda: self._end_player_action()
            )
        elif action == "minus":
            player.pay(tile.plus_minus_amount)
            self.dialog.show(
                f"-{tile.plus_minus_amount}$ paid...",
                lambda: self._end_player_action()
            )
        elif action == "card_get":
            if player.can_hold_card:
                card = get_random_card()
                player.add_card(card)
                self.dialog.show(
                    f"Got card: {card.name}",
                    lambda: self._end_player_action()
                )
            else:
                self.dialog.show("Cards full! (7/7)", lambda: self._end_player_action())
        elif action == "card_shop":
            self._open_card_shop()
        elif action == "empty_land":
            if player.is_human:
                self.confirm.show(
                    f"Buy land? ({tile.land_price}$)",
                    lambda yes: self._on_buy_land(yes, tile)
                )
            else:
                self._ai_handle_tile(tile, action)
        elif action == "own_land_no_company":
            if player.is_human:
                self.confirm.show(
                    "Build a company?",
                    lambda yes: self._on_build_confirm(yes, tile)
                )
            else:
                self._ai_handle_tile(tile, action)
        elif action == "own_land_own_company":
            self.change_scene("management", game_state=gs, tile=tile,
                              company_types=self.company_types,
                              characters=self.characters)
        elif action == "other_land_other_company":
            self._handle_other_company(tile)
        elif action == "other_land_own_company":
            fee = int(tile.land_price * LAND_FEE_RATE)
            player.pay(fee)
            owner = gs._get_player_by_id(tile.land_owner_id)
            if owner:
                owner.add_money(fee)
            self.dialog.show(
                f"Land fee: {fee}$",
                lambda: self.change_scene("management", game_state=gs, tile=tile,
                                          company_types=self.company_types,
                                          characters=self.characters)
            )
        elif action == "own_land_other_company":
            fee = int(tile.company.fixed_revenue * COMPANY_FEE_RATE)
            player.add_money(fee)
            comp_owner = gs._get_player_by_id(tile.company.owner_id)
            if comp_owner:
                comp_owner.pay(fee)
            self.dialog.show(
                f"Company fee received: {fee}$",
                lambda: self._end_player_action()
            )
        else:
            self._end_player_action()

    def _handle_other_company(self, tile):
        gs = self.game_state
        player = gs.current_player

        # 使用料支払い
        company_fee = int(tile.company.fixed_revenue * COMPANY_FEE_RATE)
        land_fee = int(tile.land_price * LAND_FEE_RATE) if tile.land_owner_id is not None else 0

        total_fee = company_fee + land_fee
        player.pay(total_fee)

        comp_owner = gs._get_player_by_id(tile.company.owner_id)
        if comp_owner:
            comp_owner.add_money(company_fee)
        if tile.land_owner_id is not None:
            land_owner = gs._get_player_by_id(tile.land_owner_id)
            if land_owner:
                land_owner.add_money(land_fee)

        # 戦闘開始
        if comp_owner and comp_owner.id != player.id:
            self.dialog.show(
                f"Fee paid: {total_fee}$\nBattle starts!",
                lambda: self.change_scene("battle", game_state=gs,
                                          attacker=player, defender=comp_owner,
                                          battle_tile=tile,
                                          company_types=self.company_types,
                                          characters=self.characters)
            )
        else:
            self.dialog.show(f"Fee paid: {total_fee}$", lambda: self._end_player_action())

    def _on_buy_land(self, yes, tile):
        if yes:
            player = self.game_state.current_player
            if player.pay(tile.land_price):
                tile.land_owner_id = player.id
                player.owned_land_ids.append(tile.id)
                self.confirm.show(
                    "Build a company?",
                    lambda y: self._on_build_confirm(y, tile)
                )
            else:
                self.dialog.show("Not enough money!", lambda: self._end_player_action())
        else:
            self._end_player_action()

    def _on_build_confirm(self, yes, tile):
        if yes:
            affordable = [ct for ct in self.company_types
                          if ct["construction_cost"] <= self.game_state.current_player.money]
            if affordable:
                items = [f"{ct['name']} ({ct['construction_cost']}$)" for ct in affordable]
                self._build_options = affordable
                self.menu.show(items, 20, 80, on_select=self._on_company_select,
                               title="Select Company")
            else:
                self.dialog.show("Not enough money!", lambda: self._end_player_action())
        else:
            self._end_player_action()

    def _on_company_select(self, index):
        if index < 0:
            self._end_player_action()
            return
        ct = self._build_options[index]
        player = self.game_state.current_player
        tile = self.game_state.board.get_tile(player.position)
        if player.pay(ct["construction_cost"]):
            company = Company(
                name=ct["name"],
                company_type=ct["type_id"],
                owner_id=player.id,
                tile_id=tile.id,
                employees=ct["initial_employees"],
                construction_cost=ct["construction_cost"],
                base_revenue=ct["initial_revenue"],
            )
            tile.company = company
            player.owned_company_ids.append(tile.id)
            self.dialog.show(f"Built {ct['name']}!", lambda: self._end_player_action())
        else:
            self.dialog.show("Not enough money!", lambda: self._end_player_action())

    def _open_card_shop(self):
        player = self.game_state.current_player
        if not player.is_human:
            self._end_player_action()
            return
        cards = get_shop_cards(4)
        items = [f"{c.name} ({c.price}$)" for c in cards]
        items.append("Leave")
        self._shop_cards = cards
        self.menu.show(items, 20, 60, on_select=self._on_shop_select, title="Card Shop")

    def _on_shop_select(self, index):
        if index < 0 or index >= len(self._shop_cards):
            self._end_player_action()
            return
        card = self._shop_cards[index]
        player = self.game_state.current_player
        if player.pay(card.price) and player.can_hold_card:
            player.add_card(card)
            self.dialog.show(f"Bought {card.name}!", lambda: self._end_player_action())
        else:
            self.dialog.show("Cannot buy!", lambda: self._end_player_action())

    def _show_data(self):
        player = self.game_state.current_player
        assets = self.game_state.get_player_total_assets(player)
        text = (
            f"{player.name}\n"
            f"Money: {player.money}$\n"
            f"Assets: {assets}$\n"
            f"Lands: {len(player.owned_land_ids)}\n"
            f"Cards: {player.card_count}/7"
        )
        self.dialog.show(text)

    def _use_card(self):
        player = self.game_state.current_player
        normal = get_normal_cards(player.cards)
        if not normal:
            self.dialog.show("No usable cards!")
            return
        items = [f"{c.name}" for c in normal]
        items.append("Cancel")
        self._use_card_list = normal
        self.menu.show(items, 20, 80, on_select=self._on_card_use_select, title="Use Card")

    def _on_card_use_select(self, index):
        if index < 0 or index >= len(self._use_card_list):
            return
        card = self._use_card_list[index]
        player = self.game_state.current_player
        card_idx = player.cards.index(card)
        player.remove_card(card_idx)

        if card.id == "double_dice":
            value = self.game_state.roll_dice()
            self.game_state.current_player.remaining_moves = value * 2
            self.game_state.dice_value = value * 2
            self.sub_phase = SubPhase.DICE_ANIM
            self.dice_anim.start_roll(value, on_complete=lambda: self._on_dice_done())
        elif card.id == "teleport":
            player.position = self.game_state.board.get_random_tile_id()
            self.dialog.show("Teleported!", lambda: self._on_movement_complete())
        elif card.id == "slow":
            targets = [p for p in self.game_state.active_players if p.id != player.id]
            if targets:
                target = random.choice(targets)
                target.slow_debuff_turns = 5
                self.dialog.show(f"{target.name} is slowed!", lambda: self._end_player_action())
            else:
                self._end_player_action()
        elif card.id == "tax_audit":
            target = random.choice(self.game_state.active_players)
            loss = self.game_state.get_player_total_assets(target) // 3
            target.pay(min(loss, target.money))
            self.dialog.show(f"Tax audit on {target.name}! -{loss}$",
                             lambda: self._end_player_action())
        else:
            self._roll_dice()

    def _end_player_action(self):
        gs = self.game_state
        # 勝利判定
        if gs.check_victory():
            self.change_scene("ending", game_state=gs)
            return

        # 次のプレイヤー
        gs.next_player()
        if gs.all_player_done:
            gs.next_turn()
            self._start_turn()
        else:
            self._start_player_turn()

    def _ai_act(self):
        gs = self.game_state
        player = gs.current_player
        ai = self.ai_players.get(player.id)
        if not ai:
            self._roll_dice()
            return

        cmd = ai.choose_command(player, gs)
        if cmd == "card":
            card_idx = ai.choose_card_to_use(player)
            if card_idx >= 0:
                card = player.remove_card(card_idx)
                if card and card.id == "teleport":
                    player.position = gs.board.get_random_tile_id()
                    self._ai_handle_tile_after_move()
                    return
        # Default: roll dice
        self._roll_dice()

    def _ai_handle_tile(self, tile, action):
        gs = self.game_state
        player = gs.current_player
        ai = self.ai_players.get(player.id)
        if not ai:
            self._end_player_action()
            return

        if action == "empty_land":
            if ai.should_buy_land(player, tile, gs):
                if player.pay(tile.land_price):
                    tile.land_owner_id = player.id
                    player.owned_land_ids.append(tile.id)
                    # 会社建設判定
                    ct_id = ai.should_build_company(
                        player,
                        [ct for ct in self.company_types
                         if ct["construction_cost"] <= player.money]
                    )
                    if ct_id:
                        ct = next((c for c in self.company_types if c["type_id"] == ct_id), None)
                        if ct and player.pay(ct["construction_cost"]):
                            company = Company(
                                name=ct["name"],
                                company_type=ct["type_id"],
                                owner_id=player.id,
                                tile_id=tile.id,
                                employees=ct["initial_employees"],
                                construction_cost=ct["construction_cost"],
                                base_revenue=ct["initial_revenue"],
                            )
                            tile.company = company
                            player.owned_company_ids.append(tile.id)
            self._end_player_action()
        elif action == "own_land_no_company":
            ct_id = ai.should_build_company(
                player,
                [ct for ct in self.company_types if ct["construction_cost"] <= player.money]
            )
            if ct_id:
                ct = next((c for c in self.company_types if c["type_id"] == ct_id), None)
                if ct and player.pay(ct["construction_cost"]):
                    company = Company(
                        name=ct["name"],
                        company_type=ct["type_id"],
                        owner_id=player.id,
                        tile_id=tile.id,
                        employees=ct["initial_employees"],
                        construction_cost=ct["construction_cost"],
                        base_revenue=ct["initial_revenue"],
                    )
                    tile.company = company
                    player.owned_company_ids.append(tile.id)
            self._end_player_action()
        else:
            self._end_player_action()

    def _ai_handle_tile_after_move(self):
        gs = self.game_state
        player = gs.current_player
        tile = gs.board.get_tile(player.position)
        action = gs.get_tile_action_type(tile, player)
        self._on_movement_complete()

    def draw(self):
        pyxel.cls(0)
        gs = self.game_state
        player = gs.current_player

        # ターン情報
        self.hud.draw_turn_info(gs.turn_number, f"P{player.id}:{player.name}")

        # ボード描画
        self.board_view.draw_board()

        # プレイヤー描画
        tile_players = {}
        for p in gs.active_players:
            if p.position not in tile_players:
                tile_players[p.position] = []
            tile_players[p.position].append(p)

        for tile_id, players in tile_players.items():
            sx, sy = self.board_view.tile_screen_pos(tile_id)
            for i, p in enumerate(players):
                if self.sub_phase == SubPhase.MOVE_ANIM and p.id == player.id:
                    cx, cy = self.move_anim.current_pos
                    self.player_view.draw_player(p, cx, cy, 0)
                else:
                    self.player_view.draw_player(p, sx, sy, i)

        # プレイヤー所持金
        self.hud.draw_player_money(gs.players, gs, y=196)

        # コマンドバー
        if gs.phase == GamePhase.PLAYER_COMMAND and player.is_human and self.sub_phase == SubPhase.NONE:
            self.hud.draw_command_bar(self.commands, self.command_selected, y=244)

        # サイコロアニメーション
        if self.sub_phase in (SubPhase.DICE_ANIM, SubPhase.DICE_RESULT):
            self._draw_dice()

        # ダイアログ
        self.dialog.draw()
        self.confirm.draw()
        self.menu.draw()

        # AI表示
        if self.sub_phase == SubPhase.WAITING_AI:
            pyxel.rect(80, 120, 100, 16, 1)
            pyxel.rectb(80, 120, 100, 16, 7)
            pyxel.text(90, 124, f"{player.name} thinking...", 7)

    def _draw_dice(self):
        # サイコロ表示
        dx, dy = 108, 100
        pyxel.rect(dx, dy, 40, 50, 1)
        pyxel.rectb(dx, dy, 40, 50, 7)

        # サイコロの目
        value = self.dice_anim.display_value if self.sub_phase == SubPhase.DICE_ANIM else self.game_state.dice_value
        cx, cy = dx + 20, dy + 18
        pyxel.rect(cx - 10, cy - 10, 20, 20, 7)
        pyxel.rectb(cx - 10, cy - 10, 20, 20, 0)

        # 目の配置
        dot_positions = {
            1: [(0, 0)],
            2: [(-4, -4), (4, 4)],
            3: [(-4, -4), (0, 0), (4, 4)],
            4: [(-4, -4), (4, -4), (-4, 4), (4, 4)],
            5: [(-4, -4), (4, -4), (0, 0), (-4, 4), (4, 4)],
            6: [(-4, -4), (4, -4), (-4, 0), (4, 0), (-4, 4), (4, 4)],
        }
        for px, py in dot_positions.get(value, []):
            pyxel.circ(cx + px, cy + py, 1, 0)

        if self.sub_phase == SubPhase.DICE_RESULT:
            pyxel.text(dx + 8, dy + 40, f"{value}!", 10)
