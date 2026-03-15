"""ビルボード描画 — オフスクリーンイメージ上に立体的なスプライトを描画する

blt3dの透視投影により、イメージ上で-Y方向に伸びるスプライトは
カメラから見て「立ち上がって」見える。
"""


def draw_building_billboard(img, cx, cy, owner_color, height=36):
    """建物ビルボードをイメージバンクに描画する

    img: Pyxelイメージバンク
    cx, cy: タイル中心のイメージ座標
    owner_color: オーナーのカラーインデックス
    height: 建物の高さ (ピクセル)
    """
    w = 14
    h = height

    # 建物は上方向 (-Y) に伸びる
    bx = cx - w // 2
    by = cy - h

    # 建物本体
    img.rect(bx, by, w, h, 6)  # 薄灰色
    # 側面の影 (右端1列を暗くする)
    img.rect(bx + w - 2, by, 2, h, 5)

    # 屋根 (三角形)
    roof_h = 5
    for row in range(roof_h):
        x0 = bx + row
        x1 = bx + w - 1 - row
        if x0 <= x1:
            img.line(x0, by - roof_h + row, x1, by - roof_h + row, owner_color)

    # 窓 (3行2列)
    win_w = 3
    win_h = 3
    win_gap_y = 6
    win_margin_x = 2
    for row in range(4):
        wy = by + 4 + row * win_gap_y
        if wy + win_h >= cy - 4:
            break
        # 左窓
        img.rect(bx + win_margin_x, wy, win_w, win_h, 12)  # 水色
        # 右窓
        img.rect(bx + w - win_margin_x - win_w, wy, win_w, win_h, 12)

    # ドア
    door_w = 4
    door_h = 5
    door_y = cy - door_h
    if door_y > by + 8:
        dx = cx - door_w // 2
        img.rect(dx, door_y, door_w, door_h, 1)  # 濃い青
        # ドアノブ
        img.pset(dx + door_w - 1, door_y + door_h // 2, 10)

    # 輪郭
    img.rectb(bx, by, w, h, 5)


def draw_player_billboard(img, cx, cy, color, player_id, height=22):
    """プレイヤービルボードをイメージバンクに描画する

    img: Pyxelイメージバンク
    cx, cy: プレイヤーの足元イメージ座標
    color: プレイヤーカラー
    player_id: プレイヤー番号
    height: キャラクターの高さ (ピクセル)
    """
    h = height
    head_r = 4
    body_w = 8
    body_h = h - head_r * 2 - 2

    # 足元から上方向 (-Y) に配置
    body_top = cy - body_h
    head_cy = body_top - head_r - 1

    # 足 (2本)
    leg_h = max(body_h // 3, 2)
    leg_w = 2
    img.rect(cx - 3, cy - leg_h, leg_w, leg_h, color)
    img.rect(cx + 1, cy - leg_h, leg_w, leg_h, color)

    # 体
    shirt_top = cy - leg_h - (body_h - leg_h)
    shirt_h = body_h - leg_h
    img.rect(cx - body_w // 2, shirt_top, body_w, shirt_h, color)

    # 腕 (両サイド)
    arm_h = max(shirt_h - 2, 2)
    img.rect(cx - body_w // 2 - 2, shirt_top + 1, 2, arm_h, color)
    img.rect(cx + body_w // 2, shirt_top + 1, 2, arm_h, color)

    # 頭
    img.circ(cx, head_cy, head_r, 7)  # 肌色代わりに白
    img.circb(cx, head_cy, head_r, 0)

    # 髪 (頭の上半分)
    for dy in range(-head_r, -1):
        hw = head_r * head_r - dy * dy
        if hw > 0:
            import math
            half_w = int(math.sqrt(hw))
            img.line(cx - half_w, head_cy + dy, cx + half_w, head_cy + dy, color)

    # プレイヤー番号 (体の中央)
    img.text(cx - 1, shirt_top + 2, str(player_id), 7)
