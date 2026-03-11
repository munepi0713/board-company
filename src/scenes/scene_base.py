"""シーン基底クラス・シーンマネージャー"""


class Scene:
    def __init__(self):
        self.scene_manager = None

    def enter(self, **kwargs):
        """シーンに入る時の初期化"""
        pass

    def update(self):
        """毎フレームの更新処理"""
        pass

    def draw(self):
        """毎フレームの描画処理"""
        pass

    def change_scene(self, scene_name, **kwargs):
        if self.scene_manager:
            self.scene_manager.change_scene(scene_name, **kwargs)


class SceneManager:
    def __init__(self):
        self.current_scene = None
        self.scenes = {}

    def register(self, name, scene):
        self.scenes[name] = scene
        scene.scene_manager = self

    def change_scene(self, scene_name, **kwargs):
        if scene_name in self.scenes:
            self.current_scene = self.scenes[scene_name]
            self.current_scene.enter(**kwargs)

    def update(self):
        if self.current_scene:
            self.current_scene.update()

    def draw(self):
        if self.current_scene:
            self.current_scene.draw()
