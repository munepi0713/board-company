"""アニメーション管理"""


class Animation:
    """汎用アニメーション"""

    def __init__(self, duration: int = 30):
        self.duration = duration
        self.frame = 0
        self.playing = False
        self.on_complete = None

    def start(self, duration: int = None, on_complete=None):
        self.frame = 0
        self.duration = duration or self.duration
        self.playing = True
        self.on_complete = on_complete

    def update(self):
        if not self.playing:
            return
        self.frame += 1
        if self.frame >= self.duration:
            self.playing = False
            if self.on_complete:
                self.on_complete()

    @property
    def progress(self) -> float:
        if self.duration == 0:
            return 1.0
        return min(1.0, self.frame / self.duration)

    @property
    def is_done(self) -> bool:
        return not self.playing


class DiceAnimation(Animation):
    """サイコロアニメーション"""

    def __init__(self):
        super().__init__(duration=30)
        self.display_value = 1
        self.final_value = 1

    def start_roll(self, final_value: int, on_complete=None):
        self.final_value = final_value
        self.start(duration=30, on_complete=on_complete)

    def update(self):
        if not self.playing:
            return
        self.frame += 1
        if self.frame < self.duration - 5:
            import random
            self.display_value = random.randint(1, 6)
        else:
            self.display_value = self.final_value
        if self.frame >= self.duration:
            self.playing = False
            self.display_value = self.final_value
            if self.on_complete:
                self.on_complete()


class MoveAnimation(Animation):
    """移動アニメーション"""

    def __init__(self):
        super().__init__(duration=8)
        self.from_pos = (0, 0)
        self.to_pos = (0, 0)

    def start_move(self, from_pos, to_pos, on_complete=None):
        self.from_pos = from_pos
        self.to_pos = to_pos
        self.start(duration=8, on_complete=on_complete)

    @property
    def current_pos(self):
        p = self.progress
        fx, fy = self.from_pos
        tx, ty = self.to_pos
        return (int(fx + (tx - fx) * p), int(fy + (ty - fy) * p))
