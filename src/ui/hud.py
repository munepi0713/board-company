"""HUD（所持金・ターン表示）"""
import pyxel
from src.core.rules import SCREEN_WIDTH


class HUD:
    """ゲーム中のHUD表示"""

    def draw_turn_info(self, turn_number: int, player_name: str):
        """ターン情報を上部に表示"""
        pyxel.rect(0, 0, SCREEN_WIDTH, 10, 1)
        pyxel.text(2, 2, f"Turn:{turn_number:02d}  {player_name}", 7)

    def draw_player_money(self, players: list, game_state=None, y: int = 210):
        """全プレイヤーの所持金を表示"""
        pyxel.rect(0, y, SCREEN_WIDTH, len(players) * 8 + 4, 1)
        pyxel.line(0, y, SCREEN_WIDTH, y, 7)
        for i, p in enumerate(players):
            if p.is_bankrupt:
                text = f"P{p.id}:{p.name[:4]} BANKRUPT"
                color = 2
            else:
                assets = game_state.get_player_total_assets(p) if game_state else p.money
                text = f"P{p.id}:{p.name[:4]} ${p.money} (${assets})"
                color = p.color
            pyxel.text(4 + (i % 2) * 128, y + 2 + (i // 2) * 8, text, color)

    def draw_command_bar(self, commands: list, selected: int, y: int = 244):
        """コマンドバーを表示"""
        pyxel.rect(0, y, SCREEN_WIDTH, 12, 1)
        pyxel.line(0, y, SCREEN_WIDTH, y, 7)
        cx = 8
        for i, cmd in enumerate(commands):
            color = 10 if i == selected else 7
            prefix = ">" if i == selected else " "
            pyxel.text(cx, y + 3, f"{prefix}{cmd}", color)
            cx += len(cmd) * 4 + 20
