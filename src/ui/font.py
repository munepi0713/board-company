"""日本語フォントユーティリティ"""
import os
import pyxel

# 美咲ゴシック（8x8ドット日本語フォント）
_FONT_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "data", "fonts", "misaki_gothic.ttf")
_jp_font = None


def get_font():
    """日本語フォントを取得（遅延初期化）"""
    global _jp_font
    if _jp_font is None:
        _jp_font = pyxel.Font(_FONT_PATH)
    return _jp_font


def draw_text(x, y, s, col):
    """日本語対応テキスト描画"""
    pyxel.text(x, y, s, col, get_font())
