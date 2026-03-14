"""戦闘画面"""
import pyxel
from src.scenes.scene_base import Scene
from src.ui.input_helper import btnp
from src.ui.font import draw_text
from src.core.rules import SCREEN_WIDTH, SCREEN_HEIGHT
from src.core.battle_logic import BattleState, BattleBuff
from src.core.card_logic import get_battle_cards
from src.core.ai import AIPlayer


class BattlePhase:
    INTRO = "intro"
    COMMAND = "command"
    EXECUTE = "execute"
    RESULT = "result"
    END = "end"


class BattleScene(Scene):
    def __init__(self):
        super().__init__()
        self.game_state = None
        self.battle = None
        self.company_types = []
        self.characters = []
        self.battle_tile = None
        self.phase = BattlePhase.INTRO
        self.selected = 0
        self.commands = ["攻撃", "防御", "カード", "逃げる"]
        self.message = ""
        self.message_timer = 0
        self.ai_players = {}

    def enter(self, **kwargs):
        self.game_state = kwargs.get("game_state")
        self.company_types = kwargs.get("company_types", [])
        self.characters = kwargs.get("characters", [])
        attacker = kwargs.get("attacker")
        defender = kwargs.get("defender")
        self.battle_tile = kwargs.get("battle_tile")

        self.battle = BattleState(attacker, defender, self.game_state.board)
        self.phase = BattlePhase.INTRO
        self.selected = 0
        self.message = "バトル開始！"
        self.message_timer = 30

        # AI setup
        self.ai_players = {}
        for p in [attacker, defender]:
            if not p.is_human:
                char_data = next(
                    (c for c in self.characters if c["id"] == p.character_id), None
                )
                if char_data:
                    self.ai_players[p.id] = AIPlayer(char_data["ai_params"])
                else:
                    self.ai_players[p.id] = AIPlayer({})

    def update(self):
        if self.message_timer > 0:
            self.message_timer -= 1
            if self.message_timer == 0:
                if self.phase == BattlePhase.INTRO:
                    self.phase = BattlePhase.COMMAND
                    self.battle.determine_turn_order()
                    self._check_ai_turn()
                elif self.phase == BattlePhase.EXECUTE:
                    if self.battle.check_battle_end():
                        self.phase = BattlePhase.END
                        self._handle_battle_end()
                    else:
                        self.battle.next_battle_turn()
                        self.phase = BattlePhase.COMMAND
                        self._check_ai_turn()
                elif self.phase == BattlePhase.END:
                    self._return_to_board()
            return

        if self.phase == BattlePhase.COMMAND:
            current = self._current_fighter()
            if current.is_human:
                if btnp(pyxel.KEY_LEFT):
                    self.selected = (self.selected - 1) % len(self.commands)
                if btnp(pyxel.KEY_RIGHT):
                    self.selected = (self.selected + 1) % len(self.commands)
                if btnp(pyxel.KEY_RETURN) or btnp(pyxel.KEY_Z):
                    self._execute_command(self.selected)

    def _current_fighter(self):
        if self.battle.is_attacker_turn:
            return self.battle.attacker
        return self.battle.defender

    def _current_stats(self):
        if self.battle.is_attacker_turn:
            return self.battle.attacker_stats
        return self.battle.defender_stats

    def _target_stats(self):
        if self.battle.is_attacker_turn:
            return self.battle.defender_stats
        return self.battle.attacker_stats

    def _check_ai_turn(self):
        current = self._current_fighter()
        if not current.is_human:
            ai = self.ai_players.get(current.id)
            if ai:
                action = ai.choose_battle_action(
                    current, self.battle,
                    self.battle.is_attacker_turn
                )
                cmd_map = {"attack": 0, "defend": 1, "card": 2, "flee": 3}
                self.message_timer = 15
                self._execute_command(cmd_map.get(action, 0))

    def _execute_command(self, cmd_index):
        self.phase = BattlePhase.EXECUTE
        actor_stats = self._current_stats()
        target_stats = self._target_stats()
        current = self._current_fighter()

        if cmd_index == 0:  # 攻撃
            damage = self.battle.execute_attack(actor_stats, target_stats)
            self.message = f"{current.name}: {damage}ダメージ！"
        elif cmd_index == 1:  # 防御
            self.battle.execute_defend(actor_stats)
            self.message = f"{current.name}は防御している！"
        elif cmd_index == 2:  # カード
            battle_cards = get_battle_cards(current.cards)
            if battle_cards:
                card = battle_cards[0]
                current.cards.remove(card)
                self._apply_battle_card(card, actor_stats, target_stats)
                self.message = f"{card.name}を使った！"
            else:
                # No cards, just attack
                damage = self.battle.execute_attack(actor_stats, target_stats)
                self.message = f"カードなし！{damage}ダメージ！"
        elif cmd_index == 3:  # 逃げる
            if self.battle.try_flee(actor_stats):
                self.battle.finished = True
                self.battle.fled = True
                penalty = int(current.money * 0.05)
                current.pay(penalty)
                target_player = (
                    self.battle.defender if self.battle.is_attacker_turn
                    else self.battle.attacker
                )
                target_player.add_money(penalty)
                self.message = f"{current.name}は逃げた！(-{penalty}$)"
                self.phase = BattlePhase.END
            else:
                self.message = f"{current.name}は逃げられなかった！"

        self.message_timer = 30

    def _apply_battle_card(self, card, actor_stats, target_stats):
        if card.id == "temp_worker":
            actor_stats.buffs.append(
                BattleBuff("temp_worker", "attack", 1.5, 1)
            )
            self.battle.tick_buffs(actor_stats)
        elif card.id == "training":
            actor_stats.buffs.append(
                BattleBuff("training", "defense", 2.0, 2)
            )
            self.battle.tick_buffs(actor_stats)
        elif card.id == "tv_cm":
            actor_stats.buffs.append(
                BattleBuff("tv_cm", "speed", 2.0, 2)
            )
            self.battle.tick_buffs(actor_stats)
        elif card.id == "repair":
            heal = actor_stats.max_hp // 3
            actor_stats.hp = min(actor_stats.max_hp, actor_stats.hp + heal)
        elif card.id == "headhunt":
            target_stats.buffs.append(
                BattleBuff("headhunt", "attack", 0.7, 999)
            )
            self.battle.tick_buffs(target_stats)
        elif card.id == "compare_cm":
            target_stats.buffs.append(
                BattleBuff("compare_cm", "speed", 0.7, 999)
            )
            self.battle.tick_buffs(target_stats)

    def _handle_battle_end(self):
        if self.battle.fled:
            self.message = "バトル終了（逃走）"
            self.message_timer = 30
            return

        winner = self.battle.winner
        loser = self.battle.loser
        if winner and loser and self.battle_tile and self.battle_tile.company:
            # 勝者が会社を獲得
            company = self.battle_tile.company
            old_owner_id = company.owner_id
            company.owner_id = winner.id
            if self.battle_tile.id in loser.owned_company_ids:
                loser.owned_company_ids.remove(self.battle_tile.id)
            if self.battle_tile.id not in winner.owned_company_ids:
                winner.owned_company_ids.append(self.battle_tile.id)
            self.message = f"{winner.name}の勝利！{company.name}を獲得！"
        else:
            self.message = "バトル終了！"
        self.message_timer = 60

    def _return_to_board(self):
        self.change_scene("main", game_state=self.game_state,
                          company_types=self.company_types,
                          characters=self.characters)

    def draw(self):
        pyxel.cls(0)

        # ヘッダー
        draw_text(200, 8, "=== バトル ===", 8)

        atk = self.battle.attacker
        dfs = self.battle.defender
        atk_s = self.battle.attacker_stats
        dfs_s = self.battle.defender_stats

        # 左側（攻撃者）
        self._draw_fighter(32, 40, atk, atk_s, self.battle.is_attacker_turn)
        # VS
        draw_text(248, 100, "VS", 8)
        # 右側（防御者）
        self._draw_fighter(280, 40, dfs, dfs_s, not self.battle.is_attacker_turn)

        # コマンド
        if self.phase == BattlePhase.COMMAND:
            current = self._current_fighter()
            pyxel.rect(16, 280, 480, 20, 1)
            pyxel.rectb(16, 280, 480, 20, 7)
            cx = 32
            for i, cmd in enumerate(self.commands):
                color = 10 if i == self.selected else 7
                prefix = ">" if i == self.selected else " "
                draw_text(cx, 286, f"{prefix}{cmd}", color)
                cx += 120

        # メッセージ
        if self.message:
            pyxel.rect(16, 330, 480, 30, 1)
            pyxel.rectb(16, 330, 480, 30, 7)
            draw_text(32, 340, self.message, 10)

        # ターン数
        draw_text(16, SCREEN_HEIGHT - 16, f"バトルターン: {self.battle.turn + 1}", 5)

    def _draw_fighter(self, x, y, player, stats, is_active):
        # 名前
        name_color = 10 if is_active else 7
        draw_text(x, y, player.name, name_color)

        # キャラダミー
        pyxel.rect(x + 50, y + 20, 36, 44, player.color)
        pyxel.circ(x + 68, y + 16, 10, player.color)
        pyxel.text(x + 65, y + 36, str(player.id), 7)

        # HP bar
        bar_y = y + 80
        draw_text(x, bar_y, "HP:", 7)
        bar_w = 160
        hp_ratio = max(0, stats.hp / stats.max_hp) if stats.max_hp > 0 else 0
        pyxel.rect(x + 24, bar_y, bar_w, 8, 5)
        hp_color = 11 if hp_ratio > 0.5 else (10 if hp_ratio > 0.25 else 8)
        pyxel.rect(x + 24, bar_y, int(bar_w * hp_ratio), 8, hp_color)
        draw_text(x + 24, bar_y + 12, f"{stats.hp}/{stats.max_hp}", 7)

        # Stats
        stat_y = bar_y + 28
        draw_text(x, stat_y, f"攻撃:{int(stats.attack * stats.attack_multiplier)}", 7)
        draw_text(x, stat_y + 12, f"防御:{int(stats.defense * stats.defense_multiplier)}", 7)
        draw_text(x, stat_y + 24, f"素早:{int(stats.speed * stats.speed_multiplier)}", 7)
