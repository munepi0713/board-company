"""ニュース画面"""
import pyxel
from src.scenes.scene_base import Scene
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
            if self.frame > 60 or pyxel.btnp(pyxel.KEY_RETURN) or pyxel.btnp(pyxel.KEY_Z):
                self.phase = "news"
                self.frame = 0
                self.text_pos = 0

        elif self.phase == "news":
            # テキストを1文字ずつ表示
            if self.frame % 3 == 0 and self.text_pos < len(self.news_text):
                self.text_pos += 1
            if pyxel.btnp(pyxel.KEY_RETURN) or pyxel.btnp(pyxel.KEY_Z):
                if self.text_pos >= len(self.news_text):
                    self.phase = "end"
                    self.frame = 0
                else:
                    self.text_pos = len(self.news_text)

        elif self.phase == "end":
            if self.frame > 30 or pyxel.btnp(pyxel.KEY_RETURN) or pyxel.btnp(pyxel.KEY_Z):
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
        pyxel.rect(16, 16, SCREEN_WIDTH - 32, 140, 0)
        pyxel.rectb(16, 16, SCREEN_WIDTH - 32, 140, 10)

        # BOARD NEWS ヘッダー
        pyxel.rect(40, 20, 176, 16, 1)
        pyxel.rectb(40, 20, 176, 16, 10)
        title = "BOARD NEWS"
        tx = (SCREEN_WIDTH - len(title) * 4) // 2
        pyxel.text(tx, 25, title, 10)

        # キャスター（ダミー）
        cx, cy = 60, 60
        # 体
        pyxel.rect(cx - 8, cy, 16, 20, 12)
        # 頭
        pyxel.circ(cx, cy - 6, 8, 15)
        # 目
        pyxel.pset(cx - 3, cy - 7, 0)
        pyxel.pset(cx + 3, cy - 7, 0)
        # 口（口パクアニメーション）
        if self.phase == "news" and self.text_pos < len(self.news_text):
            if self.frame % 8 < 4:
                pyxel.line(cx - 2, cy - 2, cx + 2, cy - 2, 0)
            else:
                pyxel.rect(cx - 2, cy - 3, 4, 3, 0)
        else:
            pyxel.line(cx - 2, cy - 2, cx + 2, cy - 2, 0)

        # スタジオ装飾
        pyxel.rect(100, 50, 110, 80, 1)
        pyxel.rectb(100, 50, 110, 80, 5)

        # ニューステキスト表示エリア
        if self.phase == "sponsor":
            sp1 = self.sponsors[0] if len(self.sponsors) > 0 else "EXGRACE SOFT"
            sp2 = self.sponsors[1] if len(self.sponsors) > 1 else "EXGRACE SOFT"
            pyxel.text(108, 60, "Presented by:", 7)
            pyxel.text(108, 75, sp1[:12], 10)
            pyxel.text(108, 90, sp2[:12], 10)

        elif self.phase == "news":
            # テキストを表示
            display = self.news_text[:self.text_pos]
            lines = self._wrap(display, 22)
            for i, line in enumerate(lines[:5]):
                pyxel.text(108, 56 + i * 10, line, 7)

        elif self.phase == "end":
            pyxel.text(108, 70, "Thank you for", 7)
            pyxel.text(108, 82, "watching!", 7)

        # 下部：ターン情報
        pyxel.rect(16, 170, SCREEN_WIDTH - 32, 24, 0)
        pyxel.rectb(16, 170, SCREEN_WIDTH - 32, 24, 7)
        pyxel.text(24, 176, f"Turn {self.game_state.turn_number}  [Enter]", 7)

        # プレイヤー情報
        y = 200
        for i, p in enumerate(self.game_state.players):
            if not p.is_bankrupt:
                pyxel.text(8 + (i % 2) * 128, y + (i // 2) * 10,
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
