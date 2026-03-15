"""blt3d投影のイメージ座標→スクリーン座標変換

キャリブレーションデータによる区分線形補間を使って、
イメージバンク上の座標をスクリーン座標に変換する。
"""


# --- FLAT mode ---
# H-ストライプ: (img_y, screen_y) — project(128, img_y)のY座標
_FLAT_Y_TABLE = [
    (8, 280.3), (25, 288.3), (42, 298.3), (59, 309.8),
    (76, 323.4), (93, 339.9), (96, 351.6), (110, 360.5),
    (160, 412.3),
]

# グリッドデータから計算したXスケール: (img_y, x_scale)
# screen_x = 256 + (img_x - 128) * x_scale
_FLAT_XSCALE_TABLE = [
    (8, 1.10), (42, 1.18), (76, 1.30), (96, 1.47), (160, 1.94),
]

# --- ISO mode ---
# ホモグラフィ行列（4ポイントキャリブレーション）
_H_ISO = (
    (-2.50339106, -7.50857792, 927.18155900),
    (-0.28165276, -6.20906384, 410.00000000),
    (-0.00282242, -0.01300859, 1.00000000),
)


def _lerp_table(table, img_val):
    """テーブルから線形補間する"""
    if img_val <= table[0][0]:
        # 外挿（最初の2点から）
        if len(table) >= 2:
            x0, y0 = table[0]
            x1, y1 = table[1]
            if x1 != x0:
                return y0 + (y1 - y0) * (img_val - x0) / (x1 - x0)
        return table[0][1]
    if img_val >= table[-1][0]:
        # 外挿（最後の2点から）
        if len(table) >= 2:
            x0, y0 = table[-2]
            x1, y1 = table[-1]
            if x1 != x0:
                return y1 + (y1 - y0) * (img_val - x1) / (x1 - x0)
        return table[-1][1]
    # 補間
    for i in range(len(table) - 1):
        x0, y0 = table[i]
        x1, y1 = table[i + 1]
        if x0 <= img_val <= x1:
            t = (img_val - x0) / (x1 - x0) if x1 != x0 else 0
            return y0 + (y1 - y0) * t
    return table[-1][1]


def _project_flat(img_x, img_y):
    """FLAT mode: 区分線形補間による投影"""
    screen_y = _lerp_table(_FLAT_Y_TABLE, img_y)
    x_scale = _lerp_table(_FLAT_XSCALE_TABLE, img_y)
    screen_x = 256 + (img_x - 128) * x_scale

    # スケール: 遠い(小さいimg_y)ほど小さく、近い(大きいimg_y)ほど大きく
    # 基準: img_y=128 でスケール1.0
    ref_scale = _lerp_table(_FLAT_XSCALE_TABLE, 128)
    scale = x_scale / ref_scale

    return (screen_x, screen_y, scale)


def _project_iso(img_x, img_y):
    """ISO mode: ホモグラフィによる投影"""
    H = _H_ISO
    w = H[2][0] * img_x + H[2][1] * img_y + H[2][2]
    if abs(w) < 0.05:
        return None

    sx = (H[0][0] * img_x + H[0][1] * img_y + H[0][2]) / w
    sy = (H[1][0] * img_x + H[1][1] * img_y + H[1][2]) / w

    # スケール: |w|が大きいほど近い（スケール大）
    # 基準深度: ボード中央付近 w ≈ -1.0
    scale = abs(w) / 1.0

    return (sx, sy, scale)


def project_to_screen(img_x, img_y, is_iso):
    """イメージ座標をスクリーン座標に変換する

    Returns:
        (screen_x, screen_y, scale) or None
        scale は参照距離に対する相対スケール（1.0=基準）
    """
    if is_iso:
        return _project_iso(img_x, img_y)
    else:
        return _project_flat(img_x, img_y)
