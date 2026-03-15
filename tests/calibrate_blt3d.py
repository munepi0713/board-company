"""blt3dの投影座標を実測するキャリブレーション - グリッドベース"""
import pyxel

IMG_BANK = 2
SCREEN_W = 512
SCREEN_H = 512

# 画像を4x4グリッド(各64x64)に分割、各セルに異なる色を塗る
# 色は各グリッドの中心点を特定するために使う
GRID_SIZE = 4
CELL_SIZE = 256 // GRID_SIZE  # 64px

# 16色のうち0(黒)以外を使う
GRID_COLORS = [
    [8, 9, 10, 11],
    [14, 15, 12, 3],
    [4, 2, 6, 7],
    [1, 5, 13, 8],  # 8を再利用(最後のセルは同定不要)
]


class App:
    def __init__(self):
        pyxel.init(SCREEN_W, SCREEN_H, title="calibrate", fps=30)
        self.mode = 0
        self.frame = 0
        pyxel.run(self.update, self.draw)

    def update(self):
        self.frame += 1
        if self.frame == 5:
            self.mode = 1

    def draw(self):
        pyxel.cls(0)
        img = pyxel.images[IMG_BANK]
        img.cls(0)

        # グリッドを描画（各セルの中心に十字マーカー付き）
        for gy in range(GRID_SIZE):
            for gx in range(GRID_SIZE):
                x0 = gx * CELL_SIZE
                y0 = gy * CELL_SIZE
                col = GRID_COLORS[gy][gx]
                # セル全体を塗る
                img.rect(x0, y0, CELL_SIZE, CELL_SIZE, col)
                # 黒い格子線で区切る
                img.rectb(x0, y0, CELL_SIZE, CELL_SIZE, 0)

        if self.mode == 0:
            pyxel.blt3d(0, -160, 512, 580, IMG_BANK,
                        (57, 199, 150), (62, 45, 0), fov=40)
        else:
            pyxel.blt3d(0, 16, 512, 420, IMG_BANK,
                        (128, 220, 120), (75, 0, 0), fov=90)


App()
