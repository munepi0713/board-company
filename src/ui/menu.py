"""メニュー表示・選択"""
import pyxel
from src.ui.input_helper import btnp
from src.ui.font import draw_text


class Menu:
    """縦型メニュー"""

    def __init__(self):
        self.visible = False
        self.items = []
        self.selected = 0
        self.on_select = None
        self.x = 0
        self.y = 0
        self.title = ""

    def show(self, items: list, x: int, y: int, on_select=None, title: str = ""):
        self.visible = True
        self.items = items
        self.selected = 0
        self.on_select = on_select
        self.x = x
        self.y = y
        self.title = title

    def update(self):
        if not self.visible:
            return
        if btnp(pyxel.KEY_UP):
            self.selected = (self.selected - 1) % len(self.items)
        if btnp(pyxel.KEY_DOWN):
            self.selected = (self.selected + 1) % len(self.items)
        if btnp(pyxel.KEY_RETURN) or btnp(pyxel.KEY_Z):
            self.visible = False
            if self.on_select:
                self.on_select(self.selected)
        if btnp(pyxel.KEY_ESCAPE) or btnp(pyxel.KEY_X):
            self.visible = False
            if self.on_select:
                self.on_select(-1)  # キャンセル

    def draw(self):
        if not self.visible:
            return

        w = 200
        title_h = 12 if self.title else 0
        h = len(self.items) * 12 + 8 + title_h
        x, y = self.x, self.y

        pyxel.rect(x, y, w, h, 1)
        pyxel.rectb(x, y, w, h, 7)

        if self.title:
            draw_text(x + 4, y + 4, self.title, 10)

        for i, item in enumerate(self.items):
            iy = y + 4 + title_h + i * 12
            label = item if isinstance(item, str) else item.get("label", str(item))
            color = 10 if i == self.selected else 7
            prefix = ">" if i == self.selected else " "
            draw_text(x + 4, iy, f"{prefix}{label}", color)


class HorizontalMenu:
    """横型メニュー"""

    def __init__(self):
        self.visible = False
        self.items = []
        self.selected = 0
        self.on_select = None
        self.x = 0
        self.y = 0

    def show(self, items: list, x: int, y: int, on_select=None):
        self.visible = True
        self.items = items
        self.selected = 0
        self.on_select = on_select
        self.x = x
        self.y = y

    def update(self):
        if not self.visible:
            return
        if btnp(pyxel.KEY_LEFT):
            self.selected = (self.selected - 1) % len(self.items)
        if btnp(pyxel.KEY_RIGHT):
            self.selected = (self.selected + 1) % len(self.items)
        if btnp(pyxel.KEY_RETURN) or btnp(pyxel.KEY_Z):
            self.visible = False
            if self.on_select:
                self.on_select(self.selected)

    def draw(self):
        if not self.visible:
            return

        x = self.x
        y = self.y
        w = sum(len(item) * 8 + 16 for item in self.items) + 8
        pyxel.rect(x, y, w, 14, 1)
        pyxel.rectb(x, y, w, 14, 7)

        cx = x + 4
        for i, item in enumerate(self.items):
            color = 10 if i == self.selected else 7
            prefix = ">" if i == self.selected else " "
            draw_text(cx, y + 4, f"{prefix}{item}", color)
            cx += len(item) * 8 + 16
