"""アイソメトリックビュー用 2D スプライト描画

全てオフスクリーン画像バンクへ描画する。
呼び出し側が pyxel.blt の scale 倍率で拡大してスクリーンへ転送する前提。

座標系: cx, cy はダイヤモンドタイル上面の中央。
スプライトはこの点を「足元」として上方向に立つ。
"""


def draw_building(img, cx, cy, owner_color):
    """ビルを描く。cx, cy はタイル中心（ダイヤモンド上面の中央）

    サイズ: 20x28（TILE_W=64, TILE_H=32 に収まる）
    """
    BW = 20
    BH = 28
    bx = cx - BW // 2
    by = cy - BH + 4        # 足元をタイル上面に少し食い込ませる
    # 本体
    img.rect(bx, by, BW, BH, 6)
    # 右側面の影
    img.rect(bx + BW - 3, by, 3, BH, 5)
    # 屋根（オーナー色）- 屋根高 4px
    img.rect(bx - 1, by - 3, BW + 2, 3, owner_color)
    img.rect(bx + 1, by - 5, BW - 2, 2, owner_color)
    # 輪郭
    img.rectb(bx, by, BW, BH, 0)
    # 窓（3行 x 2列）
    win_color = 12
    for wy_i in range(4):
        wy = by + 3 + wy_i * 6
        if wy + 3 > by + BH - 4:
            break
        img.rect(bx + 3, wy, 4, 3, win_color)
        img.rect(bx + BW - 7, wy, 4, 3, win_color)
    # ドア
    door_w = 5
    door_h = 6
    dx = cx - door_w // 2
    dy = by + BH - door_h
    img.rect(dx, dy, door_w, door_h, 1)


def draw_player(img, cx, cy, color, player_id):
    """プレイヤーコマを描く。cx, cy は足元（タイル上面）

    サイズ: 約 8x16（頭 + 体）
    """
    # 足元より上方向に立つ
    # 体（長方形 5x7）
    body_w = 5
    body_h = 7
    bx = cx - body_w // 2
    by = cy - body_h
    img.rect(bx, by, body_w, body_h, color)

    # 腕（両脇に2px）
    img.rect(bx - 1, by + 1, 1, body_h - 2, color)
    img.rect(bx + body_w, by + 1, 1, body_h - 2, color)

    # 頭（3x3 白）
    head_r = 2
    hx = cx - head_r
    hy = by - head_r - 1
    img.rect(hx, hy, head_r * 2 + 1, head_r * 2 + 1, 7)
    # 目
    img.pset(cx - 1, hy + 2, 0)
    img.pset(cx + 1, hy + 2, 0)

    # 髪（オーナー色の上部ライン）
    img.line(hx, hy, hx + head_r * 2, hy, color)

    # 番号（体の中央）
    img.text(cx - 1, by + 1, str(player_id), 7)

    # 足元の影（楕円っぽい横線）
    img.line(cx - 3, cy + 1, cx + 3, cy + 1, 0)
