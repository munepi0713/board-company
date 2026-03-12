"""エンディング画面"""
import pyxel
from src.scenes.scene_base import Scene
from src.ui.input_helper import btnp
from src.core.rules import SCREEN_WIDTH, SCREEN_HEIGHT


class EndingScene(Scene):
    def __init__(self):
        super().__init__()
        self.game_state = None
        self.frame = 0

    def enter(self, **kwargs):
        self.game_state = kwargs.get("game_state")
        self.frame = 0

    def update(self):
        self.frame += 1
        if btnp(pyxel.KEY_RETURN) or btnp(pyxel.KEY_Z):
            if self.frame > 60:
                self.change_scene("title")

    def draw(self):
        pyxel.cls(0)
        gs = self.game_state

        # タイトル
        pyxel.text(80, 16, "GAME OVER!", 10)
        pyxel.line(40, 26, 216, 26, 7)

        # 優勝者
        winner = gs.winner
        if winner:
            pyxel.text(60, 36, f"Winner: P{winner.id} {winner.name}", 10)
            assets = gs.get_player_total_assets(winner)
            pyxel.text(60, 48, f"Total Assets: {assets}$", 11)

            # 勝者のダミーキャラ（大きめ）
            cx = SCREEN_WIDTH // 2
            pyxel.circ(cx, 72, 10, winner.color)
            pyxel.rect(cx - 8, 82, 16, 20, winner.color)
            pyxel.text(cx - 2, 88, str(winner.id), 7)
        else:
            pyxel.text(80, 40, "No winner!", 8)

        # 成績表
        pyxel.text(16, 110, "-- Results --", 7)

        # 順位表示
        rankings = []
        for p in gs.players:
            assets = gs.get_player_total_assets(p)
            rankings.append((p, assets))
        rankings.sort(key=lambda x: x[1], reverse=True)

        headers = ["Rank", "Player", "Money", "Assets"]
        hx = [16, 48, 120, 170]
        for i, h in enumerate(headers):
            pyxel.text(hx[i], 124, h, 13)

        for rank, (p, assets) in enumerate(rankings):
            y = 136 + rank * 12
            color = 10 if p == winner else (5 if p.is_bankrupt else 7)
            status = " (Bankrupt)" if p.is_bankrupt else ""
            pyxel.text(hx[0], y, f"{rank + 1}.", color)
            pyxel.text(hx[1], y, f"P{p.id}:{p.name[:6]}{status}", color)
            pyxel.text(hx[2], y, f"${p.money}", color)
            pyxel.text(hx[3], y, f"${assets}", color)

        # 統計
        stat_y = 136 + len(rankings) * 12 + 10
        pyxel.text(16, stat_y, f"Total Turns: {gs.turn_number}", 5)

        # フッター
        if self.frame > 60:
            if self.frame % 60 < 40:
                pyxel.text(72, SCREEN_HEIGHT - 16, "Press ENTER", 13)
