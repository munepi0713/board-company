"""アニメーション管理"""
import math


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
    """マスズームアニメーション（blt3d使用）

    常にカメラパラメータを提供する。
    非ズーム時はデフォルトの俯瞰位置、ズーム時はマスに接近する。
    flat_mode=Trueの場合、パースをつけずに真上からのカメラで
    ズームのみ行う（アイソメトリック描画との二重パース防止）。
    """

    ZOOM_IN_DURATION = 20
    ZOOM_OUT_DURATION = 15
    IMG_CENTER = 128  # イメージバンク中心

    # 通常時カメラ（俯瞰・パースあり、rot_y=45でダイヤモンド表示）
    NORMAL_X = 57
    NORMAL_Y = 199
    NORMAL_Z = 150
    NORMAL_RX = 62
    NORMAL_RY = 45
    NORMAL_FOV = 40

    # ズーム時カメラ（接近・パースあり）
    ZOOM_Z = 25
    ZOOM_Y_OFFSET = 20  # マス位置からのYオフセット
    ZOOM_RX = 55

    # フラットモード: ほぼ真上からのカメラ（パース最小）
    # 公式サンプル参照: rot_x最大100=真下、Z小さめ、FOV狭め
    FLAT_NORMAL_X = 128
    FLAT_NORMAL_Y = 220
    FLAT_NORMAL_Z = 120
    FLAT_NORMAL_RX = 75
    FLAT_FOV = 90

    FLAT_ZOOM_Z = 20
    FLAT_ZOOM_Y_OFFSET = 10
    FLAT_ZOOM_RX = 70

    # 視線追従パラメータ
    FOLLOW_SPEED = 0.08  # 追従の補間速度（0〜1、大きいほど速い）
    FOLLOW_FACTOR_PERSPECTIVE = 0.3  # パースモードでの追従係数
    FOLLOW_FACTOR_FLAT = 0.5  # フラットモードでの追従係数

    def __init__(self):
        super().__init__(duration=20)
        self.active = False
        self.zooming_in = False
        self.zooming_out = False
        self.target_x = self.IMG_CENTER
        self.target_y = self.IMG_CENTER
        self.flat_mode = False
        # 視線追従用
        self._follow_x = self.IMG_CENTER
        self._follow_y = self.IMG_CENTER
        self._current_follow_x = float(self.IMG_CENTER)
        self._current_follow_y = float(self.IMG_CENTER)

    def set_follow_target(self, target_x, target_y):
        """視線追従のターゲット位置を設定する（イメージ座標）"""
        self._follow_x = target_x
        self._follow_y = target_y

    def update_follow(self):
        """視線追従の補間を更新する（毎フレーム呼ぶ）"""
        self._current_follow_x += (self._follow_x - self._current_follow_x) * self.FOLLOW_SPEED
        self._current_follow_y += (self._follow_y - self._current_follow_y) * self.FOLLOW_SPEED

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
            return 1 - p ** 2  # イーズアウト（逆方向）
        return 1.0

    @property
    def camera_pos(self):
        """常にカメラ位置を返す（非ズーム時はデフォルト俯瞰）"""
        if self.flat_mode:
            return self._camera_pos_flat
        return self._camera_pos_perspective

    def _screen_parallel_offset(self, dx_img, dy_img):
        """イメージ空間のオフセットをスクリーン平行面でのカメラ移動量に変換する。

        カメラの回転角から right / up ベクトルを求め、イメージ平面上の
        オフセットをスクリーン座標へ射影→カメラ移動量（x,y,z）へ逆変換する。
        これによりカメラはスクリーンと平行な面上を移動し、姿勢は変化しない。
        """
        if self.flat_mode:
            rx_rad = math.radians(self.FLAT_NORMAL_RX)
            ry_rad = 0.0
        else:
            rx_rad = math.radians(self.NORMAL_RX)
            ry_rad = math.radians(self.NORMAL_RY)

        cos_ry = math.cos(ry_rad)
        sin_ry = math.sin(ry_rad)
        sin_rx = math.sin(rx_rad)
        cos_rx = math.cos(rx_rad)

        # スクリーン水平/垂直成分への射影
        screen_h = dx_img * cos_ry - dy_img * sin_ry
        screen_v = (dx_img * sin_ry + dy_img * cos_ry) * sin_rx

        # カメラ移動量（イメージ空間 x, y, z）へ逆変換
        cam_dx = screen_h * cos_ry + screen_v * sin_ry * sin_rx
        cam_dy = -screen_h * sin_ry + screen_v * cos_ry * sin_rx
        cam_dz = screen_v * cos_rx

        return (cam_dx, cam_dy, cam_dz)

    @property
    def _follow_offset_3d(self):
        """スクリーン平行面での追従オフセット (dx, dy, dz)"""
        dx_img = self._current_follow_x - self.IMG_CENTER
        dy_img = self._current_follow_y - self.IMG_CENTER
        f = self.FOLLOW_FACTOR_FLAT if self.flat_mode else self.FOLLOW_FACTOR_PERSPECTIVE
        ox, oy, oz = self._screen_parallel_offset(dx_img, dy_img)
        return (ox * f, oy * f, oz * f)

    @property
    def _camera_pos_perspective(self):
        ox, oy, oz = self._follow_offset_3d
        base_x = self.NORMAL_X + ox
        base_y = self.NORMAL_Y + oy
        base_z = self.NORMAL_Z + oz
        if not self.active:
            return (base_x, base_y, base_z)
        t = self._eased_progress
        zoom_y = self.target_y + self.ZOOM_Y_OFFSET
        cx = self._lerp(base_x, self.target_x, t)
        cy = self._lerp(base_y, zoom_y, t)
        cz = self._lerp(base_z, self.ZOOM_Z, t)
        return (cx, cy, cz)

    @property
    def _camera_pos_flat(self):
        ox, oy, oz = self._follow_offset_3d
        base_x = self.FLAT_NORMAL_X + ox
        base_y = self.FLAT_NORMAL_Y + oy
        base_z = self.FLAT_NORMAL_Z + oz
        if not self.active:
            return (base_x, base_y, base_z)
        t = self._eased_progress
        zoom_y = self.target_y + self.FLAT_ZOOM_Y_OFFSET
        cx = self._lerp(base_x, self.target_x, t)
        cy = self._lerp(base_y, zoom_y, t)
        cz = self._lerp(base_z, self.FLAT_ZOOM_Z, t)
        return (cx, cy, cz)

    @property
    def camera_rot(self):
        if self.flat_mode:
            return (self.FLAT_NORMAL_RX, 0, 0)
        if not self.active:
            return (self.NORMAL_RX, self.NORMAL_RY, 0)
        t = self._eased_progress
        rx = self._lerp(self.NORMAL_RX, self.ZOOM_RX, t)
        ry = self._lerp(self.NORMAL_RY, 0, t)  # ズーム時はrot_y=0に戻す
        return (rx, ry, 0)

    @property
    def fov(self):
        return self.FLAT_FOV if self.flat_mode else self.NORMAL_FOV
