"""BOARD COMPANY - エントリーポイント（Pyxel Web / ローカル共用）"""
import pyxel
from src.scenes.scene_base import SceneManager
from src.scenes.title import TitleScene
from src.scenes.setup import SetupScene
from src.scenes.main_board import MainBoardScene
from src.scenes.management import ManagementScene
from src.scenes.battle_scene import BattleScene
from src.scenes.news import NewsScene
from src.scenes.ending import EndingScene
from src.core.rules import SCREEN_WIDTH, SCREEN_HEIGHT, FPS


class App:
    def __init__(self):
        pyxel.init(SCREEN_WIDTH, SCREEN_HEIGHT, title="BOARD COMPANY", fps=FPS,
                   quit_key=pyxel.KEY_NONE)

        # シーン管理
        self.scene_manager = SceneManager()
        self.scene_manager.register("title", TitleScene())
        self.scene_manager.register("setup", SetupScene())
        self.scene_manager.register("main", MainBoardScene())
        self.scene_manager.register("management", ManagementScene())
        self.scene_manager.register("battle", BattleScene())
        self.scene_manager.register("news", NewsScene())
        self.scene_manager.register("ending", EndingScene())

        self.scene_manager.change_scene("title")
        pyxel.run(self.update, self.draw)

    def update(self):
        # Qキーで終了
        if pyxel.btn(pyxel.KEY_Q) and pyxel.btn(pyxel.KEY_CTRL):
            pyxel.quit()
        self.scene_manager.update()

    def draw(self):
        self.scene_manager.draw()


App()
