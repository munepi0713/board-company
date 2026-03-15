"""メインボード画面"""
import random
import pyxel
from src.scenes.scene_base import Scene
from src.ui.input_helper import btnp
from src.ui.font import draw_text
from src.core.rules import SCREEN_WIDTH, SCREEN_HEIGHT, LAND_FEE_RATE, COMPANY_FEE_RATE
from src.core.game_state import GameState, GamePhase
from src.core.company_model import Company
from src.core.card_logic import get_random_card, get_shop_cards, get_normal_cards
from src.core.event_logic import check_events, apply_event
from src.core.ai import AIPlayer
from src.views.view_base import ViewManager
from src.views.projection import project_to_screen
from src.views.billboard import draw_building_on_screen, draw_player_on_screen
from src.ui.dialog import Dialog, ConfirmDialog
from src.ui.menu import Menu
from src.ui.hud import HUD
from src.ui.animation import DiceAnimation, MoveAnimation, TileZoomAnimation
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
    TILE_ZOOM_IN = "tile_zoom_in"
    TILE_ZOOM_OUT = "tile_zoom_out"


class MainBoardScene(Scene):
    def __init__(self):
        super().__init__()
        self.game_state = None
        self.view_manager = None
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
        self.commands = ["サイコロ", "データ", "カード"]
        self.ai_timer = 0
        self.moving_player_pos = None
        self.pending_action = None
        self.tile_zoom = TileZoomAnimation()
        self.zoom_image_idx = 2  # blt3d用イメージバンク
        self.move_from_tile = None  # 移動アニメーション用: 元マスID
        self.move_to_tile = None    # 移動アニメーション用: 先マスID

    def enter(self, **kwargs):
        self.game_state = kwargs.get("game_state")
        self.company_types = kwargs.get("company_types", [])
        self.characters = kwargs.get("characters", [])

        self.view_manager = ViewManager(self.game_state.board)

        # 初回スナップショット（ニュース比較用）
        if not self.game_state.news_snapshot:
            self.game_state.take_news_snapshot()

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
        self.tile_zoom.finish_zoom()
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

        # ニュース判定（同一ターンで二度表示しない）
        if gs.is_news_turn() and not gs.news_done:
            gs.news_done = True
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

        # ビュー切り替え（Vキー）
        if btnp(pyxel.KEY_V):
            self.view_manager.toggle_view()

        # アニメーション更新
        self.dice_anim.update()
        self.move_anim.update()
        self.tile_zoom.update()

        # 視線追従: 現在プレイヤーの位置にカメラを追従させる
        self._update_camera_follow()

        # ズームアニメーション中
        if self.sub_phase == SubPhase.TILE_ZOOM_IN:
            return
        if self.sub_phase == SubPhase.TILE_ZOOM_OUT:
            return

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

    def _update_camera_follow(self):
        """現在のプレイヤー位置にカメラを追従させる"""
        gs = self.game_state
        if gs is None or self.view_manager is None:
            return
        player = gs.current_player
        bv = self.view_manager.board_view

        # 移動アニメーション中は補間位置を追従
        if (self.sub_phase == SubPhase.MOVE_ANIM
                and self.move_from_tile is not None
                and self.move_to_tile is not None):
            fix, fiy = bv.tile_image_pos(self.move_from_tile)
            tix, tiy = bv.tile_image_pos(self.move_to_tile)
            prog = self.move_anim.progress
            tx = fix + (tix - fix) * prog
            ty = fiy + (tiy - fiy) * prog
            self.tile_zoom.set_follow_target(tx, ty)
        else:
            tx, ty = bv.tile_image_pos(player.position)
            self.tile_zoom.set_follow_target(tx, ty)

        self.tile_zoom.update_follow()

    def _execute_command(self, cmd_index):
        if cmd_index == 0:  # サイコロ
            self._roll_dice()
        elif cmd_index == 1:  # データ
            self._show_data()
        elif cmd_index == 2:  # カード
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
            items = [f"ルート{chr(65 + i)}" for i in range(len(next_tiles))]
            self.sub_phase = SubPhase.BRANCH
            self.menu.show(items, 120, 200, on_select=self._on_branch_select, title="ルート選択")
            return

        if len(next_tiles) == 0:
            self._on_movement_complete()
            return

        # 移動アニメーション
        self.move_from_tile = player.position
        next_id = next_tiles[0]
        self.move_to_tile = next_id
        from_pos = self.view_manager.board_view.tile_screen_pos(player.position)
        to_pos = self.view_manager.board_view.tile_screen_pos(next_id)
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
        self.move_from_tile = player.position
        next_id = tile.next_tiles[index]
        self.move_to_tile = next_id
        from_pos = self.view_manager.board_view.tile_screen_pos(player.position)
        to_pos = self.view_manager.board_view.tile_screen_pos(next_id)
        player.position = next_id
        player.remaining_moves -= 1
        player.stats.tiles_moved += 1
        self.sub_phase = SubPhase.MOVE_ANIM
        self.move_anim.start_move(from_pos, to_pos)

    def _on_movement_complete(self):
        """移動完了→ズームイン→マス処理"""
        gs = self.game_state
        player = gs.current_player
        tile = gs.board.get_tile(player.position)

        # ズームイン開始（対象マスへ）
        tx, ty = self.view_manager.board_view.tile_image_pos(tile.id)
        self.sub_phase = SubPhase.TILE_ZOOM_IN
        self.tile_zoom.start_zoom_in(
            tx, ty,
            on_complete=lambda: self._on_zoom_in_complete()
        )

    def _on_zoom_in_complete(self):
        """ズームイン完了→マスアクション実行"""
        gs = self.game_state
        player = gs.current_player
        tile = gs.board.get_tile(player.position)
        action = gs.get_tile_action_type(tile, player)
        self.sub_phase = SubPhase.TILE_ACTION

        if action == "plus":
            player.add_money(tile.plus_minus_amount)
            self.dialog.show(
                f"+{tile.plus_minus_amount}$ もらった！",
                lambda: self._end_player_action()
            )
        elif action == "minus":
            player.pay(tile.plus_minus_amount)
            self.dialog.show(
                f"-{tile.plus_minus_amount}$ 支払った...",
                lambda: self._end_player_action()
            )
        elif action == "card_get":
            if player.can_hold_card:
                card = get_random_card()
                player.add_card(card)
                self.dialog.show(
                    f"カード入手: {card.name}",
                    lambda: self._end_player_action()
                )
            else:
                self.dialog.show("カードがいっぱい！(7/7)", lambda: self._end_player_action())
        elif action == "card_shop":
            self._open_card_shop()
        elif action == "empty_land":
            if player.is_human:
                self.confirm.show(
                    f"土地を買う？({tile.land_price}$)",
                    lambda yes: self._on_buy_land(yes, tile)
                )
            else:
                self._ai_handle_tile(tile, action)
        elif action == "own_land_no_company":
            if player.is_human:
                self.confirm.show(
                    "会社を建てる？",
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
                f"土地使用料: {fee}$",
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
                f"会社使用料を受け取った: {fee}$",
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
                f"使用料: {total_fee}$\nバトル開始！",
                lambda: self.change_scene("battle", game_state=gs,
                                          attacker=player, defender=comp_owner,
                                          battle_tile=tile,
                                          company_types=self.company_types,
                                          characters=self.characters)
            )
        else:
            self.dialog.show(f"使用料: {total_fee}$", lambda: self._end_player_action())

    def _on_buy_land(self, yes, tile):
        if yes:
            player = self.game_state.current_player
            if player.pay(tile.land_price):
                tile.land_owner_id = player.id
                player.owned_land_ids.append(tile.id)
                self.confirm.show(
                    "会社を建てる？",
                    lambda y: self._on_build_confirm(y, tile)
                )
            else:
                self.dialog.show("お金が足りない！", lambda: self._end_player_action())
        else:
            self._end_player_action()

    def _on_build_confirm(self, yes, tile):
        if yes:
            affordable = [ct for ct in self.company_types
                          if ct["construction_cost"] <= self.game_state.current_player.money]
            if affordable:
                items = [f"{ct['name']} ({ct['construction_cost']}$)" for ct in affordable]
                self._build_options = affordable
                self.menu.show(items, 40, 160, on_select=self._on_company_select,
                               title="会社を選択")
            else:
                self.dialog.show("お金が足りない！", lambda: self._end_player_action())
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
            self.dialog.show(f"{ct['name']}を建設した！", lambda: self._end_player_action())
        else:
            self.dialog.show("お金が足りない！", lambda: self._end_player_action())

    def _open_card_shop(self):
        player = self.game_state.current_player
        if not player.is_human:
            self._end_player_action()
            return
        cards = get_shop_cards(4)
        items = [f"{c.name} ({c.price}$)" for c in cards]
        items.append("やめる")
        self._shop_cards = cards
        self.menu.show(items, 40, 120, on_select=self._on_shop_select, title="カード売り場")

    def _on_shop_select(self, index):
        if index < 0 or index >= len(self._shop_cards):
            self._end_player_action()
            return
        card = self._shop_cards[index]
        player = self.game_state.current_player
        if player.pay(card.price) and player.can_hold_card:
            player.add_card(card)
            self.dialog.show(f"{card.name}を購入した！", lambda: self._end_player_action())
        else:
            self.dialog.show("購入できない！", lambda: self._end_player_action())

    def _show_data(self):
        player = self.game_state.current_player
        assets = self.game_state.get_player_total_assets(player)
        text = (
            f"{player.name}\n"
            f"所持金: {player.money}$\n"
            f"総資産: {assets}$\n"
            f"土地: {len(player.owned_land_ids)}\n"
            f"カード: {player.card_count}/7"
        )
        self.dialog.show(text)

    def _use_card(self):
        player = self.game_state.current_player
        normal = get_normal_cards(player.cards)
        if not normal:
            self.dialog.show("使えるカードがない！")
            return
        items = [f"{c.name}" for c in normal]
        items.append("やめる")
        self._use_card_list = normal
        self.menu.show(items, 40, 160, on_select=self._on_card_use_select, title="カード使用")

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
            self.dialog.show("テレポートした！", lambda: self._on_movement_complete())
        elif card.id == "slow":
            targets = [p for p in self.game_state.active_players if p.id != player.id]
            if targets:
                target = random.choice(targets)
                target.slow_debuff_turns = 5
                self.dialog.show(f"{target.name}の足が遅くなった！", lambda: self._end_player_action())
            else:
                self._end_player_action()
        elif card.id == "tax_audit":
            target = random.choice(self.game_state.active_players)
            loss = self.game_state.get_player_total_assets(target) // 3
            target.pay(min(loss, target.money))
            self.dialog.show(f"{target.name}に税務調査！ -{loss}$",
                             lambda: self._end_player_action())
        else:
            self._roll_dice()

    def _end_player_action(self):
        if self.tile_zoom.active:
            self.sub_phase = SubPhase.TILE_ZOOM_OUT
            self.tile_zoom.start_zoom_out(
                on_complete=lambda: self._on_zoom_out_complete()
            )
        else:
            self._finish_player_action()

    def _on_zoom_out_complete(self):
        self.tile_zoom.finish_zoom()
        self._finish_player_action()

    def _finish_player_action(self):
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

        # ビュータイプ表示
        view_label = "[V]表示: " + self.view_manager.view_type.upper()
        draw_text(SCREEN_WIDTH - len(view_label) * 8 - 4, 2, view_label, 13)

        # 移動中プレイヤーの補間情報を組み立てる
        move_info = None
        if (self.sub_phase == SubPhase.MOVE_ANIM
                and self.move_from_tile is not None
                and self.move_to_tile is not None):
            move_info = {
                "player_id": player.id,
                "from_tile": self.move_from_tile,
                "to_tile": self.move_to_tile,
                "progress": self.move_anim.progress,
            }

        # オフスクリーン描画 → blt3d でスクリーンに転送
        img = pyxel.images[self.zoom_image_idx]
        is_iso = self.view_manager.view_type == "isometric"
        # 共通パイプライン: TopView描画 → カメラパラメータで見た目を切替
        # アイソメトリック: rot_y=45 パース付き（Mode 7風ダイヤモンド）
        # トップビュー: flat_mode（真上からのカメラ）
        self.tile_zoom.flat_mode = not is_iso
        self.view_manager.board_view.draw_board_to_image(
            img, gs.active_players, move_info
        )
        pos = self.tile_zoom.camera_pos
        rot = self.tile_zoom.camera_rot
        fov = self.tile_zoom.fov
        vp_y = -160 if is_iso else 16
        vp_h = 580 if is_iso else 420
        pyxel.blt3d(0, vp_y, SCREEN_WIDTH, vp_h,
                    self.zoom_image_idx, pos, rot, fov=fov)

        # スクリーン上にビルボード描画
        self._draw_billboards(gs, is_iso, move_info)

        # プレイヤー所持金
        self.hud.draw_player_money(gs.players, gs, y=440)

        # コマンドバー
        if gs.phase == GamePhase.PLAYER_COMMAND and player.is_human and self.sub_phase == SubPhase.NONE:
            self.hud.draw_command_bar(self.commands, self.command_selected, y=496)

        # サイコロアニメーション
        if self.sub_phase in (SubPhase.DICE_ANIM, SubPhase.DICE_RESULT):
            self._draw_dice()

        # ダイアログ
        self.dialog.draw()
        self.confirm.draw()
        self.menu.draw()

        # AI表示
        if self.sub_phase == SubPhase.WAITING_AI:
            pyxel.rect(160, 240, 200, 24, 1)
            pyxel.rectb(160, 240, 200, 24, 7)
            draw_text(176, 248, f"{player.name} 思考中...", 7)

    def _project_billboard(self, img_x, img_y, is_iso):
        """イメージ座標からビルボードのスクリーン座標を計算する（ズーム対応）"""
        result = project_to_screen(img_x, img_y, is_iso)
        if result is None:
            return None

        if not self.tile_zoom.active:
            return result

        sx, sy, scale = result
        # ズーム中: ターゲットタイルの通常位置を基準に拡大・移動
        t_result = project_to_screen(self.tile_zoom.target_x, self.tile_zoom.target_y, is_iso)
        if t_result is None:
            return result

        t_sx, t_sy, t_scale = t_result
        prog = self.tile_zoom._eased_progress

        # ズーム倍率（カメラZ比から）
        if is_iso:
            zoom_factor = self.tile_zoom.NORMAL_Z / max(self.tile_zoom.ZOOM_Z, 1)
        else:
            zoom_factor = self.tile_zoom.FLAT_NORMAL_Z / max(self.tile_zoom.FLAT_ZOOM_Z, 1)

        # ビューポート中心（ズーム先の画面中心）
        vp_cx = SCREEN_WIDTH / 2
        vp_cy = 300 if not is_iso else 260

        # 通常位置からの相対オフセットをズーム倍率で拡大
        cur_zoom = 1.0 + (zoom_factor - 1.0) * prog
        dx = (sx - t_sx) * cur_zoom
        dy = (sy - t_sy) * cur_zoom

        # ターゲットを画面中心に向かって移動
        center_x = t_sx + (vp_cx - t_sx) * prog
        center_y = t_sy + (vp_cy - t_sy) * prog

        out_sx = center_x + dx
        out_sy = center_y + dy
        out_scale = scale * cur_zoom

        return (out_sx, out_sy, out_scale)

    def _draw_billboards(self, gs, is_iso, move_info):
        """blt3d描画後にスクリーン上にビルボードを描画する"""
        board = gs.board
        bv = self.view_manager.board_view

        # 全タイルの投影位置を計算し、奥から手前の順に描画（Zソート）
        draw_list = []

        for tile in board.tiles:
            ix, iy = bv.tile_image_pos(tile.id)
            result = self._project_billboard(ix, iy, is_iso)
            if result is None:
                continue
            sx, sy, scale = result
            if sx < -100 or sx > SCREEN_WIDTH + 100 or sy < -100 or sy > SCREEN_HEIGHT + 100:
                continue
            draw_list.append((sy, tile.id, ix, iy, sx, sy, scale))

        # 奥（screen_y小）から手前（screen_y大）の順に描画
        draw_list.sort(key=lambda e: e[0])

        # 建物ビルボード
        for _, tile_id, ix, iy, sx, sy, scale in draw_list:
            tile = board.get_tile(tile_id)
            if tile.has_company:
                owner_color = 7
                for p in gs.active_players:
                    if p.id == tile.company.owner_id:
                        owner_color = p.color
                        break
                draw_building_on_screen(sx, sy, scale, owner_color)

        # プレイヤービルボード
        player_draws = []
        tile_counts = {}
        offsets = [(-8, 0), (8, 0), (-8, 0), (8, 0)]
        for p in gs.active_players:
            if p.is_bankrupt:
                continue
            if move_info and p.id == move_info["player_id"]:
                fix, fiy = bv.tile_image_pos(move_info["from_tile"])
                tix, tiy = bv.tile_image_pos(move_info["to_tile"])
                prog = move_info["progress"]
                mix = fix + (tix - fix) * prog
                miy = fiy + (tiy - fiy) * prog
                result = self._project_billboard(mix, miy, is_iso)
                if result:
                    player_draws.append((result[1], p, result[0], result[1], result[2]))
                continue
            tid = p.position
            if tid not in tile_counts:
                tile_counts[tid] = 0
            idx = tile_counts[tid]
            tile_counts[tid] += 1
            ix, iy = bv.tile_image_pos(tid)
            result = self._project_billboard(ix, iy, is_iso)
            if result is None:
                continue
            sx, sy, scale = result
            # 同一マス上のプレイヤーを横にずらす
            dx = offsets[idx % len(offsets)][0] * scale
            player_draws.append((sy, p, sx + dx, sy, scale))

        player_draws.sort(key=lambda e: e[0])
        for _, p, sx, sy, scale in player_draws:
            if -100 < sx < SCREEN_WIDTH + 100 and -100 < sy < SCREEN_HEIGHT + 100:
                draw_player_on_screen(sx, sy, scale, p.color, p.id)

    def _draw_dice(self):
        # サイコロ表示
        dx, dy = 216, 200
        pyxel.rect(dx, dy, 80, 90, 1)
        pyxel.rectb(dx, dy, 80, 90, 7)

        # サイコロの目
        value = self.dice_anim.display_value if self.sub_phase == SubPhase.DICE_ANIM else self.game_state.dice_value
        cx, cy = dx + 40, dy + 34
        pyxel.rect(cx - 18, cy - 18, 36, 36, 7)
        pyxel.rectb(cx - 18, cy - 18, 36, 36, 0)

        # 目の配置
        dot_positions = {
            1: [(0, 0)],
            2: [(-8, -8), (8, 8)],
            3: [(-8, -8), (0, 0), (8, 8)],
            4: [(-8, -8), (8, -8), (-8, 8), (8, 8)],
            5: [(-8, -8), (8, -8), (0, 0), (-8, 8), (8, 8)],
            6: [(-8, -8), (8, -8), (-8, 0), (8, 0), (-8, 8), (8, 8)],
        }
        for px, py in dot_positions.get(value, []):
            pyxel.circ(cx + px, cy + py, 2, 0)

        if self.sub_phase == SubPhase.DICE_RESULT:
            draw_text(dx + 28, dy + 70, f"{value}！", 10)
