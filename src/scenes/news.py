"""ニュース画面"""
import pyxel
from src.scenes.scene_base import Scene
from src.ui.input_helper import btnp
from src.ui.font import draw_text
from src.core.rules import SCREEN_WIDTH, SCREEN_HEIGHT
from src.core.event_logic import check_events, apply_event, get_news_content, get_sponsors


class NewsScene(Scene):
    def __init__(self):
        super().__init__()
        self.game_state = None
        self.company_types = []
        self.characters = []
        self.frame = 0
        self.news_text = ""
        self.sponsors = []
        self.phase = "sponsor"  # sponsor -> news -> end
        self.text_pos = 0  # テキスト表示位置

    def enter(self, **kwargs):
        self.game_state = kwargs.get("game_state")
        self.company_types = kwargs.get("company_types", [])
        self.characters = kwargs.get("characters", [])
        self.frame = 0
        self.text_pos = 0
        if hasattr(self, '_text_done_frame'):
            del self._text_done_frame

        # イベント処理
        events = check_events(self.game_state.turn_number)
        messages = []
        for event in events:
            msg = apply_event(event, self.game_state)
            messages.append(msg)

        self.news_text = get_news_content(events)
        if messages:
            self.news_text = " ".join(messages)
        self.sponsors = get_sponsors(self.game_state)

        # 偶数ターン損益
        if self.game_state.is_even_turn():
            results = self.game_state.process_even_turn_revenue()
            if results:
                self.news_text += " " + " ".join(results)

        self.phase = "sponsor"

    def update(self):
        self.frame += 1

        if self.phase == "sponsor":
            if self.frame > 60 or btnp(pyxel.KEY_RETURN) or btnp(pyxel.KEY_Z):
                self.phase = "news"
                self.frame = 0
                self.text_pos = 0

        elif self.phase == "news":
            # テキストを1文字ずつ表示
            if self.frame % 3 == 0 and self.text_pos < len(self.news_text):
                self.text_pos += 1
            # テキスト表示完了後、自動で次へ進む（90フレーム＝3秒待ち）
            if self.text_pos >= len(self.news_text) and not hasattr(self, '_text_done_frame'):
                self._text_done_frame = self.frame
            if hasattr(self, '_text_done_frame') and self.frame - self._text_done_frame > 90:
                self.phase = "end"
                self.frame = 0
                del self._text_done_frame
            elif btnp(pyxel.KEY_RETURN) or btnp(pyxel.KEY_Z):
                if self.text_pos >= len(self.news_text):
                    self.phase = "end"
                    self.frame = 0
                    if hasattr(self, '_text_done_frame'):
                        del self._text_done_frame
                else:
                    self.text_pos = len(self.news_text)

        elif self.phase == "end":
            if self.frame > 30 or btnp(pyxel.KEY_RETURN) or btnp(pyxel.KEY_Z):
                # 勝利判定
                if self.game_state.check_victory():
                    self.change_scene("ending", game_state=self.game_state)
                else:
                    self.change_scene("main", game_state=self.game_state,
                                      company_types=self.company_types,
                                      characters=self.characters)

    def draw(self):
        pyxel.cls(1)

        # ニューススタジオ背景
        pyxel.rect(32, 32, SCREEN_WIDTH - 64, 280, 0)
        pyxel.rectb(32, 32, SCREEN_WIDTH - 64, 280, 10)

        # ボードニュース ヘッダー
        pyxel.rect(80, 40, 352, 24, 1)
        pyxel.rectb(80, 40, 352, 24, 10)
        title = "ボードニュース"
        tx = (SCREEN_WIDTH - len(title) * 8) // 2
        draw_text(tx, 48, title, 10)

        # キャスター（ダミー）
        cx, cy = 120, 120
        # 体
        pyxel.rect(cx - 14, cy, 28, 36, 12)
        # 頭
        pyxel.circ(cx, cy - 10, 14, 15)
        # 目
        pyxel.pset(cx - 5, cy - 12, 0)
        pyxel.pset(cx + 5, cy - 12, 0)
        # 口（口パクアニメーション）
        if self.phase == "news" and self.text_pos < len(self.news_text):
            if self.frame % 8 < 4:
                pyxel.line(cx - 3, cy - 4, cx + 3, cy - 4, 0)
            else:
                pyxel.rect(cx - 3, cy - 5, 6, 4, 0)
        else:
            pyxel.line(cx - 3, cy - 4, cx + 3, cy - 4, 0)

        # スタジオ装飾
        pyxel.rect(200, 90, 220, 160, 1)
        pyxel.rectb(200, 90, 220, 160, 5)

        # ニューステキスト表示エリア
        if self.phase == "sponsor":
            sp1 = self.sponsors[0] if len(self.sponsors) > 0 else "EXGRACE SOFT"
            sp2 = self.sponsors[1] if len(self.sponsors) > 1 else "EXGRACE SOFT"
            draw_text(216, 110, "提供:", 7)
            draw_text(216, 140, sp1[:12], 10)
            draw_text(216, 165, sp2[:12], 10)

        elif self.phase == "news":
            # テキストを表示
            display = self.news_text[:self.text_pos]
            lines = self._wrap(display, 20)
            for i, line in enumerate(lines[:8]):
                draw_text(216, 100 + i * 14, line, 7)

        elif self.phase == "end":
            draw_text(216, 130, "ご視聴ありがとう", 7)
            draw_text(216, 150, "ございました！", 7)

        # 下部：ターン情報
        pyxel.rect(32, 340, SCREEN_WIDTH - 64, 30, 0)
        pyxel.rectb(32, 340, SCREEN_WIDTH - 64, 30, 7)
        draw_text(48, 350, f"ターン {self.game_state.turn_number}  [Enter]", 7)

        # プレイヤー情報
        y = 390
        for i, p in enumerate(self.game_state.players):
            if not p.is_bankrupt:
                draw_text(16 + (i % 2) * 256, y + (i // 2) * 14,
                          f"P{p.id}:{p.name[:4]} ${p.money}", p.color)

    def _wrap(self, text, max_chars):
        lines = []
        while text:
            if len(text) <= max_chars:
                lines.append(text)
                break
            lines.append(text[:max_chars])
            text = text[max_chars:]
        return lines
