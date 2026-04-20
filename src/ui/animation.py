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


class TileZoomAnimation(Animation):
    """マスズームアニメーション（pyxel.blt の scale 方式）

    オフスクリーン画像（IMG_W x IMG_H）を scale 倍してスクリーンに転送する。
    常時 scale, offset_x, offset_y を提供する。

    通常時:
      scale = BASE_SCALE, 画像(0,0)が画面(BASE_OFFSET_X, BASE_OFFSET_Y)に来る

    ズーム時:
      scale = ZOOM_SCALE, ターゲットイメージ座標が画面中心(FOCUS_X, FOCUS_Y)に来る
    """

    # 画像バンクサイズとスクリーン上の描画領域
    IMG_W = 256
    IMG_H = 208              # 画像バンク上で実際に使う領域の高さ
    SCREEN_W = 512
    SCREEN_H = 512

    # 通常時（ピクセル等倍 2x）
    BASE_SCALE = 2.0
    BASE_OFFSET_X = 0        # 画像左端→画面左端
    BASE_OFFSET_Y = 16       # HUD の下

    # ズーム時
    ZOOM_SCALE = 4.0
    FOCUS_X = SCREEN_W // 2  # ターゲットを中心に寄せる
    FOCUS_Y = 240            # 画面のボード領域中心に近い位置

    ZOOM_IN_DURATION = 20
    ZOOM_OUT_DURATION = 15
    IMG_CENTER = IMG_W // 2

    # 視線追従（通常時にボードを微妙に平行移動して現プレイヤーを寄せる）
    FOLLOW_SPEED = 0.08
    FOLLOW_FACTOR = 0.25     # 画像座標の中心からのズレに対する移動係数

    def __init__(self):
        super().__init__(duration=self.ZOOM_IN_DURATION)
        self.active = False
        self.zooming_in = False
        self.zooming_out = False
        self.target_x = self.IMG_CENTER
        self.target_y = self.IMG_H // 2
        # 視線追従
        self._follow_x = self.IMG_CENTER
        self._follow_y = self.IMG_H // 2
        self._current_follow_x = float(self.IMG_CENTER)
        self._current_follow_y = float(self.IMG_H // 2)

    # ---- 視線追従 ----------------------------------------------------
    def set_follow_target(self, target_x, target_y):
        self._follow_x = target_x
        self._follow_y = target_y

    def update_follow(self):
        self._current_follow_x += (self._follow_x - self._current_follow_x) * self.FOLLOW_SPEED
        self._current_follow_y += (self._follow_y - self._current_follow_y) * self.FOLLOW_SPEED

    @property
    def _follow_offset(self):
        """通常時にオフスクリーンを平行移動させる画像座標オフセット"""
        dx = (self._current_follow_x - self.IMG_CENTER) * self.FOLLOW_FACTOR
        dy = (self._current_follow_y - self.IMG_H // 2) * self.FOLLOW_FACTOR
        return (dx, dy)

    # ---- ズーム開始/終了 --------------------------------------------
    def start_zoom_in(self, target_x, target_y, on_complete=None):
        self.target_x = target_x
        self.target_y = target_y
        self.active = True
        self.zooming_in = True
        self.zooming_out = False
        self.start(duration=self.ZOOM_IN_DURATION, on_complete=on_complete)

    def start_zoom_out(self, on_complete=None):
        self.zooming_in = False
        self.zooming_out = True
        self.start(duration=self.ZOOM_OUT_DURATION, on_complete=on_complete)

    def finish_zoom(self):
        self.active = False
        self.zooming_in = False
        self.zooming_out = False
        self.playing = False

    def _lerp(self, a, b, t):
        return a + (b - a) * t

    @property
    def _eased_progress(self):
        if not self.active:
            return 0.0
        p = self.progress
        if self.zooming_in:
            return 1 - (1 - p) ** 2  # イーズアウト
        elif self.zooming_out:
            return 1 - p ** 2        # 逆イーズアウト
        return 1.0

    # ---- blt パラメータ ---------------------------------------------
    @property
    def scale(self):
        """現在の blt スケール"""
        if not self.active:
            return self.BASE_SCALE
        return self._lerp(self.BASE_SCALE, self.ZOOM_SCALE, self._eased_progress)

    @property
    def offset(self):
        """pyxel.blt の転送先左上座標 (screen_x, screen_y)

        return 値で pyxel.blt(offset_x, offset_y, img, 0, 0, IMG_W, IMG_H, scale=scale)
        を呼べば OK。
        """
        s = self.scale
        fx, fy = self._follow_offset

        # 通常時の基準位置（視線追従で微平行移動）
        base_x = self.BASE_OFFSET_X - fx * self.BASE_SCALE
        base_y = self.BASE_OFFSET_Y - fy * self.BASE_SCALE

        if not self.active:
            return (base_x, base_y)

        # ズーム時: ターゲット画像座標 (tx, ty) が画面 (FOCUS_X, FOCUS_Y) に来るよう offset を決定
        #   screen = offset + img * s  →  offset = FOCUS - (tx, ty) * s
        zoom_x = self.FOCUS_X - self.target_x * s
        zoom_y = self.FOCUS_Y - self.target_y * s

        t = self._eased_progress
        ox = self._lerp(base_x, zoom_x, t)
        oy = self._lerp(base_y, zoom_y, t)
        return (ox, oy)

    def project_image_to_screen(self, img_x, img_y):
        """オフスクリーン画像座標 → 現在のスクリーン座標"""
        ox, oy = self.offset
        s = self.scale
        return (ox + img_x * s, oy + img_y * s)
