"""タイトル画面"""
import pyxel
from src.scenes.scene_base import Scene
from src.ui.input_helper import btnp
from src.core.rules import SCREEN_WIDTH, SCREEN_HEIGHT


class TitleScene(Scene):
    def __init__(self):
        super().__init__()
        self.selected = 0
        self.menu_items = ["START", "CONTINUE"]
        self.frame = 0

    def enter(self, **kwargs):
        self.selected = 0
        self.frame = 0

    def update(self):
        self.frame += 1
        if btnp(pyxel.KEY_UP):
            self.selected = (self.selected - 1) % len(self.menu_items)
        if btnp(pyxel.KEY_DOWN):
            self.selected = (self.selected + 1) % len(self.menu_items)
        if btnp(pyxel.KEY_RETURN) or btnp(pyxel.KEY_Z):
            if self.selected == 0:
                self.change_scene("setup")
            elif self.selected == 1:
                # TODO: ロード機能
                self.change_scene("setup")

    def draw(self):
        pyxel.cls(0)

        # タイトルロゴ（ダミー）
        title = "BOARD COMPANY"
        tx = (SCREEN_WIDTH - len(title) * 4) // 2
        # 影
        pyxel.text(tx + 1, 61, title, 1)
        pyxel.text(tx, 60, title, 10)

        # サブタイトル
        sub = "- Company Management Board Game -"
        sx = (SCREEN_WIDTH - len(sub) * 4) // 2
        pyxel.text(sx, 80, sub, 7)

        # ボード風の装飾（ダミー）
        for i in range(8):
            x = 40 + i * 22
            y = 100 + (i % 3) * 5
            col = [3, 9, 11, 2, 10, 3, 9, 11][i]
            pyxel.rect(x, y, 14, 14, col)
            pyxel.rectb(x, y, 14, 14, 1)

        # メニュー
        for i, item in enumerate(self.menu_items):
            y = 150 + i * 16
            color = 10 if i == self.selected else 7
            prefix = "> " if i == self.selected else "  "
            text = f"{prefix}{item}"
            x = (SCREEN_WIDTH - len(text) * 4) // 2
            pyxel.text(x, y, text, color)

        # コピーライト
        copy_text = "(C) EXGRACE SOFT"
        cx = (SCREEN_WIDTH - len(copy_text) * 4) // 2
        pyxel.text(cx, SCREEN_HEIGHT - 16, copy_text, 5)

        # 点滅テキスト
        if self.frame % 60 < 40:
            hint = "Press ENTER / A to start"
            hx = (SCREEN_WIDTH - len(hint) * 4) // 2
            pyxel.text(hx, 200, hint, 13)
