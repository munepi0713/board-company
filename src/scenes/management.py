"""経営画面"""
import pyxel
from src.scenes.scene_base import Scene
from src.ui.input_helper import btnp
from src.ui.font import draw_text
from src.core.rules import SCREEN_WIDTH, SCREEN_HEIGHT


class ManagementScene(Scene):
    def __init__(self):
        super().__init__()
        self.game_state = None
        self.tile = None
        self.company_types = []
        self.characters = []
        self.selected = 0
        self.commands = [
            {"label": "社員教育", "key": "educate"},
            {"label": "宣伝", "key": "advertise"},
            {"label": "雇用", "key": "hire"},
            {"label": "解雇", "key": "fire"},
            {"label": "清算", "key": "liquidate"},
            {"label": "終了", "key": "done"},
        ]
        self.used_commands = set()
        self.hire_count = 10
        self.fire_count = 10
        self.input_mode = None  # 'hire' or 'fire'
        self.message = ""

    def enter(self, **kwargs):
        self.game_state = kwargs.get("game_state")
        self.tile = kwargs.get("tile")
        self.company_types = kwargs.get("company_types", [])
        self.characters = kwargs.get("characters", [])
        self.selected = 0
        self.used_commands = set()
        self.input_mode = None
        self.hire_count = 10
        self.fire_count = 10
        self.message = ""

    def update(self):
        company = self.tile.company
        player = self.game_state.current_player

        if self.input_mode == "hire":
            if btnp(pyxel.KEY_UP):
                self.hire_count = min(self.hire_count + 10, 100)
            if btnp(pyxel.KEY_DOWN):
                self.hire_count = max(self.hire_count - 10, 1)
            if btnp(pyxel.KEY_RETURN) or btnp(pyxel.KEY_Z):
                cost = company.hire(self.hire_count)
                player.pay(cost)
                self.used_commands.add("hire")
                self.message = f"{self.hire_count}人雇用した (+{cost}$)"
                self.input_mode = None
            if btnp(pyxel.KEY_ESCAPE) or btnp(pyxel.KEY_X):
                self.input_mode = None
            return

        if self.input_mode == "fire":
            if btnp(pyxel.KEY_UP):
                self.fire_count = min(self.fire_count + 10, company.employees)
            if btnp(pyxel.KEY_DOWN):
                self.fire_count = max(self.fire_count - 10, 1)
            if btnp(pyxel.KEY_RETURN) or btnp(pyxel.KEY_Z):
                company.fire(self.fire_count)
                self.used_commands.add("fire")
                self.message = f"{self.fire_count}人解雇した"
                self.input_mode = None
            if btnp(pyxel.KEY_ESCAPE) or btnp(pyxel.KEY_X):
                self.input_mode = None
            return

        if btnp(pyxel.KEY_UP):
            self.selected = (self.selected - 1) % len(self.commands)
        if btnp(pyxel.KEY_DOWN):
            self.selected = (self.selected + 1) % len(self.commands)

        if btnp(pyxel.KEY_RETURN) or btnp(pyxel.KEY_Z):
            cmd = self.commands[self.selected]
            key = cmd["key"]

            if key == "done":
                self._return_to_board()
                return

            if key in self.used_commands:
                self.message = "実行済みです！"
                return

            if key == "educate":
                cost = company.employees * 15
                if player.pay(cost):
                    company.educate()
                    self.used_commands.add("educate")
                    self.message = f"教育完了！(-{cost}$)"
                else:
                    self.message = "お金が足りない！"

            elif key == "advertise":
                cost = 200
                if player.pay(cost):
                    company.advertise()
                    self.used_commands.add("advertise")
                    self.message = f"宣伝した！(-{cost}$)"
                else:
                    self.message = "お金が足りない！"

            elif key == "hire":
                self.input_mode = "hire"
                self.hire_count = 10

            elif key == "fire":
                self.input_mode = "fire"
                self.fire_count = min(10, company.employees)

            elif key == "liquidate":
                refund = company.sell_price
                player.add_money(refund)
                self.tile.company = None
                if self.tile.id in player.owned_company_ids:
                    player.owned_company_ids.remove(self.tile.id)
                self.message = f"清算した！+{refund}$"
                self.used_commands.add("liquidate")
                self._return_to_board()

        if btnp(pyxel.KEY_ESCAPE) or btnp(pyxel.KEY_X):
            self._return_to_board()

    def _return_to_board(self):
        self.change_scene("main", game_state=self.game_state,
                          company_types=self.company_types,
                          characters=self.characters)

    def draw(self):
        pyxel.cls(0)
        company = self.tile.company
        player = self.game_state.current_player

        if company is None:
            draw_text(8, 8, "会社は清算されました。", 7)
            return

        # ヘッダー
        draw_text(16, 16, f"経営: {company.name}", 10)
        pyxel.line(16, 28, SCREEN_WIDTH - 16, 28, 7)

        # 会社情報
        y = 48
        info = [
            f"業種:     {company.company_type}",
            f"社員数:   {company.employees}",
            f"実力:     {company.ability}",
            f"知名度:   {company.fame}",
            f"売上:     {company.fixed_revenue}$",
            f"評価額:   {company.evaluation}$",
        ]
        for i, line in enumerate(info):
            draw_text(32, y + i * 16, line, 7)

        # 所持金
        draw_text(32, y + len(info) * 16 + 10, f"所持金: {player.money}$", 11)

        # コマンド
        cmd_y = 220
        pyxel.line(16, cmd_y - 6, SCREEN_WIDTH - 16, cmd_y - 6, 7)

        for i, cmd in enumerate(self.commands):
            cy = cmd_y + i * 18
            is_used = cmd["key"] in self.used_commands
            color = 5 if is_used else (10 if i == self.selected else 7)
            prefix = ">" if i == self.selected else " "
            label = cmd["label"]

            # コスト表示
            cost_str = ""
            if cmd["key"] == "educate":
                cost_str = f" ({company.employees * 15}$)"
            elif cmd["key"] == "advertise":
                cost_str = " (200$)"

            draw_text(32, cy, f"{prefix}{label}{cost_str}", color)

        # 入力モード
        if self.input_mode == "hire":
            pyxel.rect(120, 280, 260, 40, 1)
            pyxel.rectb(120, 280, 260, 40, 7)
            cost = self.hire_count * 15
            draw_text(136, 290, f"雇用: {self.hire_count}人 ({cost}$)", 10)
            draw_text(136, 304, "上下キー, ENTER", 5)

        if self.input_mode == "fire":
            pyxel.rect(120, 280, 260, 40, 1)
            pyxel.rectb(120, 280, 260, 40, 7)
            draw_text(136, 290, f"解雇: {self.fire_count}人", 10)
            draw_text(136, 304, "上下キー, ENTER", 5)

        # メッセージ
        if self.message:
            pyxel.rect(16, SCREEN_HEIGHT - 40, SCREEN_WIDTH - 32, 24, 1)
            pyxel.rectb(16, SCREEN_HEIGHT - 40, SCREEN_WIDTH - 32, 24, 7)
            draw_text(32, SCREEN_HEIGHT - 32, self.message, 10)
