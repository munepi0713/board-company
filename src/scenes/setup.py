"""セットアップ画面"""
import random
import pyxel
from src.scenes.scene_base import Scene
from src.ui.input_helper import btnp
from src.ui.font import draw_text
from src.core.rules import SCREEN_WIDTH, SCREEN_HEIGHT
from src.core.player_model import Player
from src.core.game_state import GameState, GamePhase
from src.utils.data_loader import load_map_data, load_characters, load_company_types


class SetupScene(Scene):
    def __init__(self):
        super().__init__()
        self.player_count = 2
        self.characters = []
        self.company_types = []
        self.player_settings = []  # [(is_human, char_index), ...]
        self.cursor_row = 0  # 0=人数, 1-4=プレイヤー設定, 5=OK
        self.cursor_col = 0  # 0=人間/CPU, 1=キャラ選択

    def enter(self, **kwargs):
        self.characters = load_characters()
        self.company_types = load_company_types()
        self.player_count = 2
        self.cursor_row = 0
        self.cursor_col = 0
        self._init_player_settings()

    def _init_player_settings(self):
        self.player_settings = []
        for i in range(4):
            is_human = (i == 0)
            char_index = i % len(self.characters)
            self.player_settings.append([is_human, char_index])

    def update(self):
        if btnp(pyxel.KEY_UP):
            self.cursor_row = max(0, self.cursor_row - 1)
        if btnp(pyxel.KEY_DOWN):
            max_row = self.player_count + 1  # 人数 + プレイヤー数 + OK
            self.cursor_row = min(max_row, self.cursor_row + 1)

        if self.cursor_row == 0:
            # 人数変更
            if btnp(pyxel.KEY_LEFT):
                self.player_count = max(2, self.player_count - 1)
            if btnp(pyxel.KEY_RIGHT):
                self.player_count = min(4, self.player_count + 1)
        elif 1 <= self.cursor_row <= self.player_count:
            idx = self.cursor_row - 1
            if btnp(pyxel.KEY_LEFT):
                if self.cursor_col == 0:
                    self.player_settings[idx][0] = not self.player_settings[idx][0]
                else:
                    self.player_settings[idx][1] = (
                        self.player_settings[idx][1] - 1
                    ) % len(self.characters)
            if btnp(pyxel.KEY_RIGHT):
                if self.cursor_col == 0:
                    self.player_settings[idx][0] = not self.player_settings[idx][0]
                else:
                    self.player_settings[idx][1] = (
                        self.player_settings[idx][1] + 1
                    ) % len(self.characters)
            if btnp(pyxel.KEY_TAB):
                self.cursor_col = 1 - self.cursor_col

        if btnp(pyxel.KEY_RETURN) or btnp(pyxel.KEY_Z):
            if self.cursor_row == self.player_count + 1:
                self._start_game()

    def _start_game(self):
        board, goal = load_map_data()
        game_state = GameState()
        game_state.board = board
        game_state.goal_assets = goal

        # プレイヤー作成
        used_positions = []
        all_tile_ids = [t.id for t in board.tiles]
        for i in range(self.player_count):
            is_human, char_idx = self.player_settings[i]
            char = self.characters[char_idx]
            # ランダムスタート地点
            pos = random.choice(all_tile_ids)
            while pos in used_positions:
                pos = random.choice(all_tile_ids)
            used_positions.append(pos)

            player = Player(
                id=i + 1,
                name=char["name"],
                character_id=char["id"],
                is_human=is_human,
                position=pos,
                color=char.get("color", 8 + i),
            )
            game_state.players.append(player)

        game_state.phase = GamePhase.TURN_START
        self.change_scene("main", game_state=game_state,
                          company_types=self.company_types,
                          characters=self.characters)

    def draw(self):
        pyxel.cls(0)

        draw_text(16, 16, "ゲーム設定", 10)
        pyxel.line(16, 28, SCREEN_WIDTH - 16, 28, 7)

        # 人数
        y = 50
        color = 10 if self.cursor_row == 0 else 7
        draw_text(32, y, f"人数: < {self.player_count} >", color)

        # プレイヤー設定
        for i in range(self.player_count):
            y = 90 + i * 36
            is_active = self.cursor_row == i + 1
            is_human, char_idx = self.player_settings[i]
            char = self.characters[char_idx]
            type_str = "プレイヤー" if is_human else "CPU      "
            name_str = char["name"]

            prefix = ">" if is_active else " "
            type_color = 10 if is_active and self.cursor_col == 0 else 7
            name_color = 10 if is_active and self.cursor_col == 1 else 7

            draw_text(24, y, f"{prefix}P{i + 1}:", 7)
            draw_text(80, y, f"[{type_str}]", type_color)
            draw_text(200, y, f"< {name_str} >", name_color)

            # キャラの色をプレビュー
            pyxel.circ(SCREEN_WIDTH - 40, y + 3, 6, char.get("color", 8))

        # 説明
        draw_text(32, 90 + self.player_count * 36 + 10, "十字キー: 変更", 5)
        draw_text(32, 90 + self.player_count * 36 + 22, "TAB/Y: 列切替", 5)

        # OKボタン
        ok_y = 320
        ok_active = self.cursor_row == self.player_count + 1
        ok_color = 10 if ok_active else 7
        draw_text(200, ok_y, "[決定]", ok_color)
        if ok_active:
            draw_text(192, ok_y, ">", 10)

        # 下部説明
        draw_text(16, SCREEN_HEIGHT - 30, "A/ENTER: 決定  B/ESC: 戻る", 5)
