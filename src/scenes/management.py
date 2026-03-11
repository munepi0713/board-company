"""経営画面"""
import pyxel
from src.scenes.scene_base import Scene
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
            {"label": "Training", "key": "educate"},
            {"label": "Advertise", "key": "advertise"},
            {"label": "Hire", "key": "hire"},
            {"label": "Fire", "key": "fire"},
            {"label": "Liquidate", "key": "liquidate"},
            {"label": "Done", "key": "done"},
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
            if pyxel.btnp(pyxel.KEY_UP):
                self.hire_count = min(self.hire_count + 10, 100)
            if pyxel.btnp(pyxel.KEY_DOWN):
                self.hire_count = max(self.hire_count - 10, 1)
            if pyxel.btnp(pyxel.KEY_RETURN) or pyxel.btnp(pyxel.KEY_Z):
                cost = company.hire(self.hire_count)
                player.pay(cost)
                self.used_commands.add("hire")
                self.message = f"Hired {self.hire_count} (+{cost}$)"
                self.input_mode = None
            if pyxel.btnp(pyxel.KEY_ESCAPE) or pyxel.btnp(pyxel.KEY_X):
                self.input_mode = None
            return

        if self.input_mode == "fire":
            if pyxel.btnp(pyxel.KEY_UP):
                self.fire_count = min(self.fire_count + 10, company.employees)
            if pyxel.btnp(pyxel.KEY_DOWN):
                self.fire_count = max(self.fire_count - 10, 1)
            if pyxel.btnp(pyxel.KEY_RETURN) or pyxel.btnp(pyxel.KEY_Z):
                company.fire(self.fire_count)
                self.used_commands.add("fire")
                self.message = f"Fired {self.fire_count}"
                self.input_mode = None
            if pyxel.btnp(pyxel.KEY_ESCAPE) or pyxel.btnp(pyxel.KEY_X):
                self.input_mode = None
            return

        if pyxel.btnp(pyxel.KEY_UP):
            self.selected = (self.selected - 1) % len(self.commands)
        if pyxel.btnp(pyxel.KEY_DOWN):
            self.selected = (self.selected + 1) % len(self.commands)

        if pyxel.btnp(pyxel.KEY_RETURN) or pyxel.btnp(pyxel.KEY_Z):
            cmd = self.commands[self.selected]
            key = cmd["key"]

            if key == "done":
                self._return_to_board()
                return

            if key in self.used_commands:
                self.message = "Already done!"
                return

            if key == "educate":
                cost = company.employees * 15
                if player.pay(cost):
                    company.educate()
                    self.used_commands.add("educate")
                    self.message = f"Training done! (-{cost}$)"
                else:
                    self.message = "Not enough money!"

            elif key == "advertise":
                cost = 200
                if player.pay(cost):
                    company.advertise()
                    self.used_commands.add("advertise")
                    self.message = f"Advertised! (-{cost}$)"
                else:
                    self.message = "Not enough money!"

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
                self.message = f"Liquidated! +{refund}$"
                self.used_commands.add("liquidate")
                self._return_to_board()

        if pyxel.btnp(pyxel.KEY_ESCAPE) or pyxel.btnp(pyxel.KEY_X):
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
            pyxel.text(8, 8, "Company liquidated.", 7)
            return

        # ヘッダー
        pyxel.text(8, 8, f"Management: {company.name}", 10)
        pyxel.line(8, 18, SCREEN_WIDTH - 8, 18, 7)

        # 会社情報
        y = 28
        info = [
            f"Type:     {company.company_type}",
            f"Staff:    {company.employees}",
            f"Ability:  {company.ability}",
            f"Fame:     {company.fame}",
            f"Revenue:  {company.fixed_revenue}$",
            f"Value:    {company.evaluation}$",
        ]
        for i, line in enumerate(info):
            pyxel.text(16, y + i * 10, line, 7)

        # 所持金
        pyxel.text(16, y + len(info) * 10 + 5, f"Your Money: {player.money}$", 11)

        # コマンド
        cmd_y = 120
        pyxel.line(8, cmd_y - 4, SCREEN_WIDTH - 8, cmd_y - 4, 7)

        for i, cmd in enumerate(self.commands):
            cy = cmd_y + i * 12
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

            pyxel.text(16, cy, f"{prefix}{label}{cost_str}", color)

        # 入力モード
        if self.input_mode == "hire":
            pyxel.rect(60, 140, 140, 30, 1)
            pyxel.rectb(60, 140, 140, 30, 7)
            cost = self.hire_count * 15
            pyxel.text(68, 146, f"Hire: {self.hire_count} ({cost}$)", 10)
            pyxel.text(68, 156, "UP/DOWN, ENTER", 5)

        if self.input_mode == "fire":
            pyxel.rect(60, 140, 140, 30, 1)
            pyxel.rectb(60, 140, 140, 30, 7)
            pyxel.text(68, 146, f"Fire: {self.fire_count}", 10)
            pyxel.text(68, 156, "UP/DOWN, ENTER", 5)

        # メッセージ
        if self.message:
            pyxel.rect(8, SCREEN_HEIGHT - 30, SCREEN_WIDTH - 16, 20, 1)
            pyxel.rectb(8, SCREEN_HEIGHT - 30, SCREEN_WIDTH - 16, 20, 7)
            pyxel.text(16, SCREEN_HEIGHT - 24, self.message, 10)
