"""ダイアログ表示"""
import pyxel
from src.core.rules import SCREEN_WIDTH, SCREEN_HEIGHT


class Dialog:
    """メッセージダイアログ"""

    def __init__(self):
        self.visible = False
        self.text = ""
        self.on_close = None
        self._lines = []

    def show(self, text: str, on_close=None):
        self.visible = True
        self.text = text
        self.on_close = on_close
        # テキストを折り返し
        self._lines = self._wrap_text(text, 30)

    def update(self):
        if not self.visible:
            return
        if pyxel.btnp(pyxel.KEY_RETURN) or pyxel.btnp(pyxel.KEY_Z):
            self.visible = False
            if self.on_close:
                self.on_close()

    def draw(self):
        if not self.visible:
            return
        x = 8
        h = max(30, len(self._lines) * 10 + 16)
        y = SCREEN_HEIGHT - h - 8
        w = SCREEN_WIDTH - 16

        # 背景
        pyxel.rect(x, y, w, h, 1)
        pyxel.rectb(x, y, w, h, 7)

        # テキスト
        for i, line in enumerate(self._lines):
            pyxel.text(x + 6, y + 6 + i * 10, line, 7)

        # Enter表示
        pyxel.text(x + w - 40, y + h - 10, "[Enter]", 13)

    def _wrap_text(self, text: str, max_chars: int) -> list:
        lines = []
        while text:
            if len(text) <= max_chars:
                lines.append(text)
                break
            lines.append(text[:max_chars])
            text = text[max_chars:]
        return lines


class ConfirmDialog:
    """はい/いいえ確認ダイアログ"""

    def __init__(self):
        self.visible = False
        self.text = ""
        self.selected = 0  # 0=はい, 1=いいえ
        self.on_result = None
        self._lines = []

    def show(self, text: str, on_result=None):
        self.visible = True
        self.text = text
        self.selected = 0
        self.on_result = on_result
        self._lines = []
        while text:
            if len(text) <= 28:
                self._lines.append(text)
                break
            self._lines.append(text[:28])
            text = text[28:]

    def update(self):
        if not self.visible:
            return
        if pyxel.btnp(pyxel.KEY_LEFT) or pyxel.btnp(pyxel.KEY_RIGHT):
            self.selected = 1 - self.selected
        if pyxel.btnp(pyxel.KEY_RETURN) or pyxel.btnp(pyxel.KEY_Z):
            self.visible = False
            if self.on_result:
                self.on_result(self.selected == 0)

    def draw(self):
        if not self.visible:
            return
        x = 8
        h = max(40, len(self._lines) * 10 + 26)
        y = SCREEN_HEIGHT - h - 8
        w = SCREEN_WIDTH - 16

        pyxel.rect(x, y, w, h, 1)
        pyxel.rectb(x, y, w, h, 7)

        for i, line in enumerate(self._lines):
            pyxel.text(x + 6, y + 6 + i * 10, line, 7)

        btn_y = y + h - 14
        # はい
        yes_color = 10 if self.selected == 0 else 7
        pyxel.text(x + 60, btn_y, "[O.K.]", yes_color)
        # いいえ
        no_color = 10 if self.selected == 1 else 7
        pyxel.text(x + 120, btn_y, "[Cancel]", no_color)

        # カーソル
        if self.selected == 0:
            pyxel.text(x + 52, btn_y, ">", 10)
        else:
            pyxel.text(x + 112, btn_y, ">", 10)
