"""blt3d投影キャリブレーション - ストライプパターン

水平ストライプと垂直ストライプで投影座標を密に計測する。
4フレーム分のパターンを順次描画する:
  frame 0-4: 水平ストライプ（ISO）
  frame 5-9: 垂直ストライプ（ISO）
  frame 10-14: 水平ストライプ（FLAT）
  frame 15-19: 垂直ストライプ（FLAT）
"""
import pyxel

IMG_BANK = 2
SCREEN_W = 512
SCREEN_H = 512

# 使用する色（黒0以外の15色）
COLORS = list(range(1, 16))  # 1-15
STRIPE_H = 17  # 256 / 15 ≈ 17
STRIPE_W = 17


class App:
    def __init__(self):
        pyxel.init(SCREEN_W, SCREEN_H, title="calibrate_stripes", fps=30)
        self.frame = 0
        pyxel.run(self.update, self.draw)

    def update(self):
        self.frame += 1

    def draw(self):
        pyxel.cls(0)
        img = pyxel.images[IMG_BANK]
        img.cls(0)

        mode = self.frame // 5  # 0=h_iso, 1=v_iso, 2=h_flat, 3=v_flat
        is_horizontal = mode % 2 == 0
        is_iso = mode < 2

        if is_horizontal:
            # 水平ストライプ: 15本、各17px幅
            for i, col in enumerate(COLORS):
                y0 = i * STRIPE_H
                img.rect(0, y0, 256, STRIPE_H, col)
        else:
            # 垂直ストライプ: 15本、各17px幅
            for i, col in enumerate(COLORS):
                x0 = i * STRIPE_W
                img.rect(x0, 0, STRIPE_W, 256, col)

        if is_iso:
            pyxel.blt3d(0, -160, 512, 580, IMG_BANK,
                        (57, 199, 150), (62, 45, 0), fov=40)
        else:
            pyxel.blt3d(0, 16, 512, 420, IMG_BANK,
                        (128, 220, 120), (75, 0, 0), fov=90)


App()
