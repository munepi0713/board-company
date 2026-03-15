"""ビルボード描画 — オフスクリーンイメージ上に立体的なスプライトを描画する

blt3dの透視投影により、イメージ上で-Y方向に伸びるスプライトは
カメラから見て「立ち上がって」見える。
"""

import math


def draw_building_billboard(img, cx, cy, owner_color, height=55):
    """建物ビルボードをイメージバンクに描画する

    img: Pyxelイメージバンク
    cx, cy: タイル中心のイメージ座標
    owner_color: オーナーのカラーインデックス
    height: 建物の高さ (ピクセル)
    """
    w = 18
    h = height

    # 建物は上方向 (-Y) に伸びる
    bx = cx - w // 2
    by = cy - h

    # 建物本体（明るい灰色）
    img.rect(bx, by, w, h, 6)
    # 側面の影 (右端3列を暗くする)
    img.rect(bx + w - 3, by, 3, h, 5)

    # 屋根 (三角形、大きめ)
    roof_h = 7
    for row in range(roof_h):
        x0 = bx + row
        x1 = bx + w - 1 - row
        if x0 <= x1:
            img.line(x0, by - roof_h + row, x1, by - roof_h + row, owner_color)

    # 窓 (複数行、2列)
    win_w = 4
    win_h = 4
    win_gap_y = 7
    win_margin_x = 2
    for row in range(6):
        wy = by + 5 + row * win_gap_y
        if wy + win_h >= cy - 5:
            break
        # 左窓
        img.rect(bx + win_margin_x, wy, win_w, win_h, 12)
        # 右窓
        img.rect(bx + w - win_margin_x - win_w, wy, win_w, win_h, 12)

    # ドア
    door_w = 6
    door_h = 7
    door_y = cy - door_h
    if door_y > by + 10:
        dx = cx - door_w // 2
        img.rect(dx, door_y, door_w, door_h, 1)
        # ドアノブ
        img.pset(dx + door_w - 1, door_y + door_h // 2, 10)

    # 輪郭（太め）
    img.rectb(bx, by, w, h, 0)
    # オーナー色のライン（建物上部）
    img.line(bx, by, bx + w - 1, by, owner_color)


def draw_player_billboard(img, cx, cy, color, player_id, height=32):
    """プレイヤービルボードをイメージバンクに描画する

    img: Pyxelイメージバンク
    cx, cy: プレイヤーの足元イメージ座標
    color: プレイヤーカラー
    player_id: プレイヤー番号
    height: キャラクターの高さ (ピクセル)
    """
    h = height
    head_r = 5
    body_w = 10
    body_h = h - head_r * 2 - 3

    # 足元から上方向 (-Y) に配置
    body_top = cy - body_h
    head_cy = body_top - head_r - 1

    # 足 (2本、太め)
    leg_h = max(body_h // 3, 3)
    leg_w = 3
    img.rect(cx - 4, cy - leg_h, leg_w, leg_h, color)
    img.rect(cx + 1, cy - leg_h, leg_w, leg_h, color)

    # 体（太め）
    shirt_top = cy - leg_h - (body_h - leg_h)
    shirt_h = body_h - leg_h
    img.rect(cx - body_w // 2, shirt_top, body_w, shirt_h, color)

    # 腕 (両サイド、太め)
    arm_h = max(shirt_h - 2, 3)
    img.rect(cx - body_w // 2 - 3, shirt_top + 1, 3, arm_h, color)
    img.rect(cx + body_w // 2, shirt_top + 1, 3, arm_h, color)

    # 頭（大きめ）
    img.circ(cx, head_cy, head_r, 7)
    img.circb(cx, head_cy, head_r, 0)

    # 髪 (頭の上半分)
    for dy in range(-head_r, -1):
        hw = head_r * head_r - dy * dy
        if hw > 0:
            half_w = int(math.sqrt(hw))
            img.line(cx - half_w, head_cy + dy, cx + half_w, head_cy + dy, color)

    # プレイヤー番号 (体の中央、大きめ)
    img.text(cx - 2, shirt_top + 2, str(player_id), 7)

    # 輪郭（体全体）
    img.rectb(cx - body_w // 2, shirt_top, body_w, body_h, 0)
