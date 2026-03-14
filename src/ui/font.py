"""テキスト描画ユーティリティ"""
import pyxel


def draw_text(x, y, s, col):
    """テキスト描画"""
    pyxel.text(x, y, s, col)
