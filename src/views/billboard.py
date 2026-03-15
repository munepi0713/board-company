"""ビルボード描画 — スクリーン上に垂直に立つスプライトを描画する

blt3dで投影されたボード上に、パースなしで垂直に立つ
ビルボードスプライトを描画する。
"""

import pyxel


def draw_building_on_screen(cx, cy, scale, owner_color):
    """建物ビルボードをスクリーンに描画する

    cx, cy: 建物の足元スクリーン座標
    scale: 距離に応じたスケール (1.0=基準サイズ)
    owner_color: オーナーのカラーインデックス
    """
    s = max(0.3, min(scale, 8.0))
    w = int(16 * s)
    h = int(48 * s)
    if w < 4 or h < 6:
        return

    bx = cx - w // 2
    by = int(cy - h)

    # 建物本体
    pyxel.rect(bx, by, w, h, 6)
    # 側面の影
    shadow_w = max(int(3 * s), 1)
    pyxel.rect(bx + w - shadow_w, by, shadow_w, h, 5)

    # 屋根（三角形）
    roof_h = max(int(6 * s), 2)
    for row in range(roof_h):
        rx0 = bx + (row * w) // (roof_h * 2)
        rx1 = bx + w - 1 - (row * w) // (roof_h * 2)
        if rx0 <= rx1:
            pyxel.line(rx0, by - roof_h + row, rx1, by - roof_h + row, owner_color)

    # 窓
    win_w = max(int(3 * s), 2)
    win_h = max(int(3 * s), 2)
    win_gap = max(int(7 * s), 4)
    margin_x = max(int(2 * s), 1)
    for row in range(6):
        wy = by + max(int(4 * s), 2) + row * win_gap
        if wy + win_h >= int(cy) - max(int(4 * s), 2):
            break
        pyxel.rect(bx + margin_x, wy, win_w, win_h, 12)
        rx = bx + w - margin_x - win_w
        if rx > bx + margin_x + win_w:
            pyxel.rect(rx, wy, win_w, win_h, 12)

    # ドア
    door_w = max(int(5 * s), 2)
    door_h = max(int(6 * s), 3)
    door_y = int(cy) - door_h
    if door_y > by + int(8 * s):
        dx = cx - door_w // 2
        pyxel.rect(dx, door_y, door_w, door_h, 1)

    # 輪郭
    pyxel.rectb(bx, by, w, h, 0)
    # オーナー色ライン
    pyxel.line(bx, by, bx + w - 1, by, owner_color)


def draw_player_on_screen(cx, cy, scale, color, player_id):
    """プレイヤービルボードをスクリーンに描画する

    cx, cy: プレイヤーの足元スクリーン座標
    scale: 距離に応じたスケール
    color: プレイヤーカラー
    player_id: プレイヤー番号
    """
    s = max(0.3, min(scale, 8.0))
    h = int(36 * s)
    head_r = max(int(5 * s), 2)
    body_w = max(int(10 * s), 4)
    body_h = h - head_r * 2 - max(int(2 * s), 1)
    if body_h < 4:
        return

    cx = int(cx)
    cy = int(cy)

    # 足元から上方向
    body_top = cy - body_h
    head_cy = body_top - head_r - 1

    # 足
    leg_h = max(body_h // 3, 2)
    leg_w = max(int(3 * s), 1)
    pyxel.rect(cx - leg_w - 1, cy - leg_h, leg_w, leg_h, color)
    pyxel.rect(cx + 1, cy - leg_h, leg_w, leg_h, color)

    # 体
    shirt_top = cy - leg_h - (body_h - leg_h)
    shirt_h = body_h - leg_h
    pyxel.rect(cx - body_w // 2, shirt_top, body_w, shirt_h, color)

    # 腕
    arm_w = max(int(3 * s), 1)
    arm_h = max(shirt_h - 2, 2)
    pyxel.rect(cx - body_w // 2 - arm_w, shirt_top + 1, arm_w, arm_h, color)
    pyxel.rect(cx + body_w // 2, shirt_top + 1, arm_w, arm_h, color)

    # 頭
    pyxel.circ(cx, head_cy, head_r, 7)
    pyxel.circb(cx, head_cy, head_r, 0)

    # 髪（頭の上半分）
    import math
    for dy in range(-head_r, -1):
        hw = head_r * head_r - dy * dy
        if hw > 0:
            half_w = int(math.sqrt(hw))
            pyxel.line(cx - half_w, head_cy + dy, cx + half_w, head_cy + dy, color)

    # プレイヤー番号
    pyxel.text(cx - 2, shirt_top + max(int(2 * s), 1), str(player_id), 7)

    # 体の輪郭
    pyxel.rectb(cx - body_w // 2, shirt_top, body_w, body_h, 0)
