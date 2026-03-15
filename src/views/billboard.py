"""ビルボード描画 — オフスクリーンイメージ上に立体的なスプライトを描画する

blt3dの透視投影により、イメージ上で-Y方向に伸びるスプライトは
カメラから見て「立ち上がって」見える。
"""


def draw_building_billboard(img, cx, cy, owner_color, height=14):
    """建物ビルボードをイメージバンクに描画する

    img: Pyxelイメージバンク
    cx, cy: タイル中心のイメージ座標
    owner_color: オーナーのカラーインデックス
    height: 建物の高さ (ピクセル)
    """
    w = 8
    h = height

    # 建物は上方向 (-Y) に伸びる
    bx = cx - w // 2
    by = cy - h

    # 建物本体
    img.rect(bx, by, w, h, 6)  # 薄灰色

    # 屋根 (三角形)
    roof_h = 3
    # 三角屋根: 中央が頂点
    for row in range(roof_h):
        x0 = bx + row
        x1 = bx + w - 1 - row
        if x0 <= x1:
            img.line(x0, by - roof_h + row, x1, by - roof_h + row, owner_color)

    # 窓 (水色ドット)
    for row in range(2):
        wy = by + 2 + row * 4
        if wy + 1 >= cy:
            break
        img.rect(bx + 1, wy, 2, 2, 12)  # 左窓
        img.rect(bx + w - 3, wy, 2, 2, 12)  # 右窓

    # ドア
    door_y = cy - 3
    if door_y > by + 4:
        img.rect(cx - 1, door_y, 2, 3, 1)  # 濃い青


def draw_player_billboard(img, cx, cy, color, player_id, height=10):
    """プレイヤービルボードをイメージバンクに描画する

    img: Pyxelイメージバンク
    cx, cy: プレイヤーの足元イメージ座標
    color: プレイヤーカラー
    player_id: プレイヤー番号
    height: キャラクターの高さ (ピクセル)
    """
    h = height
    head_r = 2
    body_w = 4
    body_h = h - head_r * 2 - 1

    # 足元から上方向 (-Y) に配置
    body_top = cy - body_h
    head_cy = body_top - head_r

    # 体
    img.rect(cx - body_w // 2, body_top, body_w, body_h, color)

    # 頭
    img.circ(cx, head_cy, head_r, color)

    # 輪郭
    img.circb(cx, head_cy, head_r, 0)

    # プレイヤー番号
    img.text(cx - 1, body_top + 1, str(player_id), 7)
