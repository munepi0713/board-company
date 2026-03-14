"""タイトル画面"""
import pyxel
from src.scenes.scene_base import Scene
from src.ui.input_helper import btnp
from src.ui.font import draw_text
from src.core.rules import SCREEN_WIDTH, SCREEN_HEIGHT


class TitleScene(Scene):
    def __init__(self):
        super().__init__()
        self.selected = 0
        self.menu_items = ["はじめから", "つづきから"]
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

        # タイトルロゴ
        title = "ボードカンパニー"
        tx = (SCREEN_WIDTH - len(title) * 8) // 2
        # 影
        draw_text(tx + 1, 121, title, 1)
        draw_text(tx, 120, title, 10)

        # サブタイトル
        sub = "- 会社経営ボードゲーム -"
        sx = (SCREEN_WIDTH - len(sub) * 8) // 2
        draw_text(sx, 150, sub, 7)

        # ボード風の装飾（ダミー）
        for i in range(8):
            x = 100 + i * 40
            y = 190 + (i % 3) * 8
            col = [3, 9, 11, 2, 10, 3, 9, 11][i]
            pyxel.rect(x, y, 28, 28, col)
            pyxel.rectb(x, y, 28, 28, 1)

        # メニュー
        for i, item in enumerate(self.menu_items):
            y = 280 + i * 24
            color = 10 if i == self.selected else 7
            prefix = "> " if i == self.selected else "  "
            text = f"{prefix}{item}"
            x = (SCREEN_WIDTH - len(text) * 8) // 2
            draw_text(x, y, text, color)

        # コピーライト
        copy_text = "(C) EXGRACE SOFT"
        cx = (SCREEN_WIDTH - len(copy_text) * 4) // 2
        pyxel.text(cx, SCREEN_HEIGHT - 24, copy_text, 5)

        # 点滅テキスト
        if self.frame % 60 < 40:
            hint = "ENTER / Aボタン でスタート"
            hx = (SCREEN_WIDTH - len(hint) * 8) // 2
            draw_text(hx, 400, hint, 13)
