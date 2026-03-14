"""エンディング画面"""
import pyxel
from src.scenes.scene_base import Scene
from src.ui.input_helper import btnp
from src.ui.font import draw_text
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
        draw_text(200, 32, "ゲーム終了！", 10)
        pyxel.line(80, 46, 432, 46, 7)

        # 優勝者
        winner = gs.winner
        if winner:
            draw_text(140, 60, f"優勝: P{winner.id} {winner.name}", 10)
            assets = gs.get_player_total_assets(winner)
            draw_text(140, 76, f"総資産: {assets}$", 11)

            # 勝者のダミーキャラ（大きめ）
            cx = SCREEN_WIDTH // 2
            pyxel.circ(cx, 120, 16, winner.color)
            pyxel.rect(cx - 12, 136, 24, 32, winner.color)
            pyxel.text(cx - 2, 146, str(winner.id), 7)
        else:
            draw_text(200, 70, "優勝者なし！", 8)

        # 成績表
        draw_text(32, 200, "-- 結果発表 --", 7)

        # 順位表示
        rankings = []
        for p in gs.players:
            assets = gs.get_player_total_assets(p)
            rankings.append((p, assets))
        rankings.sort(key=lambda x: x[1], reverse=True)

        headers = ["順位", "プレイヤー", "所持金", "総資産"]
        hx = [32, 80, 240, 360]
        for i, h in enumerate(headers):
            draw_text(hx[i], 220, h, 13)

        for rank, (p, assets) in enumerate(rankings):
            y = 240 + rank * 18
            color = 10 if p == winner else (5 if p.is_bankrupt else 7)
            status = " (破産)" if p.is_bankrupt else ""
            draw_text(hx[0], y, f"{rank + 1}.", color)
            draw_text(hx[1], y, f"P{p.id}:{p.name[:6]}{status}", color)
            draw_text(hx[2], y, f"${p.money}", color)
            draw_text(hx[3], y, f"${assets}", color)

        # 統計
        stat_y = 240 + len(rankings) * 18 + 16
        draw_text(32, stat_y, f"総ターン数: {gs.turn_number}", 5)

        # フッター
        if self.frame > 60:
            if self.frame % 60 < 40:
                draw_text(200, SCREEN_HEIGHT - 24, "ENTERキーで戻る", 13)
