"""アイソメトリックビュー用 2D スプライト描画

全てオフスクリーン画像バンクへ描画する。
呼び出し側が pyxel.blt の scale 倍率で拡大してスクリーンへ転送する前提。
"""


# 建物（タイル中心 cx, cy に建つ）
def draw_building(img, cx, cy, owner_color):
    """小さなビルを描く。cx, cy はタイル中心（ダイヤモンドの中央）"""
    # 本体: 高さ BH、幅 BW の長方形
    BW = 10
    BH = 14
    bx = cx - BW // 2
    by = cy - BH + 2       # 上面に少し食い込ませる
    # 側面
    img.rect(bx, by, BW, BH, 6)        # 薄グレー
    img.rect(bx + BW - 2, by, 2, BH, 5)  # 右側の影
    # 屋根（オーナー色）
    img.rect(bx - 1, by - 2, BW + 2, 2, owner_color)
    # 輪郭
    img.rectb(bx, by, BW, BH, 0)
    # 窓
    for wy in (by + 2, by + 6, by + 10):
        img.pset(bx + 2, wy, 12)
        img.pset(bx + 4, wy, 12)
        img.pset(bx + 7, wy, 12)


# プレイヤー（タイル中心から少しずれた位置に立つ）
def draw_player(img, cx, cy, color, player_id):
    """小さなコマを描く。cx, cy は足元より少し上のタイル上面位置"""
    # 体
    img.rect(cx - 1, cy - 3, 3, 4, color)
    # 頭（白）
    img.pset(cx, cy - 4, 7)
    img.pset(cx - 1, cy - 5, 7)
    img.pset(cx, cy - 5, 7)
    img.pset(cx + 1, cy - 5, 7)
    # プレイヤー番号（色付き点で識別）
    # 体に小さくドット（番号は拡大時にも潰れないように省略）
    # 代わりに足元に player_id 色の下線
    img.pset(cx - 1, cy + 1, color)
    img.pset(cx + 1, cy + 1, color)
