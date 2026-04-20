"""ボード描画（アイソメトリック）- ダイヤモンド投影 2D 描画

擬似 3D アイソメトリックビューを 2D 描画（ダイヤモンド型タイル）で実現する。
描画は常にイメージバンクへ行い、呼び出し側が pyxel.blt の scale でスクリーンに転送する。

座標変換:
    grid (gx, gy) → image (cx + (gx - gy) * TILE_W/2, cy + (gx + gy) * TILE_H/2)
"""
import pyxel
from src.views.view_base import BoardViewBase
from src.views.isometric.sprites import draw_building, draw_player
from src.core.rules import TILE_SIZE

# オフスクリーン画像サイズ（IMG_H は実コンテンツ領域）
IMG_W = 512
IMG_H = 416

# ダイヤモンドタイルサイズ（2:1 比）
TILE_W = 64
TILE_H = 32

# ボード中心（オフスクリーン上）— 8x8 グリッドが収まるよう調整
BOARD_CX = IMG_W // 2        # 256
BOARD_CY = 96                # 上部に建物の高さぶん余白を確保

# マスタイプごとの色（上面）
TILE_COLORS = {
    "normal": 3,       # 緑
    "card_shop": 9,    # オレンジ
    "plus": 11,        # 黄緑
    "minus": 2,        # 紫
    "card": 10,        # 黄色
}
# 側面の暗い色（南面）
TILE_SIDE_COLOR = 1     # 濃い青
# 側面の少し明るい色（東面）
TILE_SIDE_COLOR_E = 5   # 暗めグレー
# 枠線色
TILE_BORDER_COLOR = 0
TILE_OWNED_BORDER = 8   # 赤

TILE_DEPTH = 6           # ダイヤモンドの「高さ」（厚み）px

# 道（接続線）の色
ROAD_COLOR = 13

# 同一マス上の複数プレイヤーのオフセット（画像座標）
_PLAYER_OFFSETS = [(-10, -4), (10, -4), (-10, 8), (10, 8)]


def _draw_diamond_filled(img, cx, cy, w, h, color):
    """塗り潰しダイヤモンドを描画（スキャンライン）"""
    hh = h // 2
    hw = w // 2
    if hh <= 0 or hw <= 0:
        img.pset(cx, cy, color)
        return
    for dy in range(-hh, hh + 1):
        t = 1.0 - abs(dy) / hh
        half_w = int(hw * t)
        img.line(cx - half_w, cy + dy, cx + half_w, cy + dy, color)


def _draw_diamond_outline(img, cx, cy, w, h, color):
    """ダイヤモンドの枠線のみ描画"""
    hh = h // 2
    hw = w // 2
    img.line(cx, cy - hh, cx + hw, cy, color)
    img.line(cx + hw, cy, cx, cy + hh, color)
    img.line(cx, cy + hh, cx - hw, cy, color)
    img.line(cx - hw, cy, cx, cy - hh, color)


def _draw_tile_block(img, cx, cy, top_color, border_color):
    """マス1つ: 上面ダイヤモンド + 南/東の側面 で立体的に見せる"""
    hw = TILE_W // 2
    hh = TILE_H // 2

    # --- 側面（南西・南東） ---
    # 下側の4点: (cx-hw, cy), (cx, cy+hh), (cx+hw, cy), そこから TILE_DEPTH 下
    d = TILE_DEPTH
    # 南西面（左下）— 暗い
    for i in range(d):
        img.line(cx - hw, cy + i, cx, cy + hh + i, TILE_SIDE_COLOR)
    # 南東面（右下）— やや明るい
    for i in range(d):
        img.line(cx, cy + hh + i, cx + hw, cy + i, TILE_SIDE_COLOR_E)
    # 底辺ライン
    img.line(cx - hw, cy + d, cx, cy + hh + d, border_color)
    img.line(cx, cy + hh + d, cx + hw, cy + d, border_color)

    # --- 上面 ---
    _draw_diamond_filled(img, cx, cy, TILE_W, TILE_H, top_color)
    _draw_diamond_outline(img, cx, cy, TILE_W, TILE_H, border_color)


class IsometricBoardView(BoardViewBase):
    """アイソメトリックでボードを描画する"""

    def __init__(self, board_model):
        super().__init__(board_model)
        self.offset_x = 64   # draw_board（スクリーン直描き）用
        self.offset_y = 48

    # ------------------------------------------------------------------
    # 座標計算
    # ------------------------------------------------------------------
    def _grid_to_image(self, gx, gy):
        ix = BOARD_CX + (gx - gy) * (TILE_W // 2)
        iy = BOARD_CY + (gx + gy) * (TILE_H // 2)
        return (ix, iy)

    def tile_image_pos(self, tile_id: int):
        tile = self.board_model.get_tile(tile_id)
        return self._grid_to_image(tile.grid_x, tile.grid_y)

    def tile_screen_pos(self, tile_id: int, camera_x=0, camera_y=0):
        """スクリーン直描き用（分岐メニューやログに使う便宜的な座標）"""
        tile = self.board_model.get_tile(tile_id)
        sx = tile.grid_x * (TILE_SIZE + 4) + self.offset_x - camera_x
        sy = tile.grid_y * (TILE_SIZE + 4) + self.offset_y - camera_y
        return (sx, sy)

    # ------------------------------------------------------------------
    # 直描き（scale 付き blt を通さない互換パス、通常は未使用）
    # ------------------------------------------------------------------
    def draw_board(self, camera_x=0, camera_y=0):
        pass

    def draw_tile(self, tile, camera_x=0, camera_y=0):
        pass

    # ------------------------------------------------------------------
    # オフスクリーン描画（blt で拡大転送する前提）
    # ------------------------------------------------------------------
    def draw_board_to_image(self, img, players=None, move_info=None):
        img.cls(0)

        # 接続道（タイル上面に薄く線を引く）
        for tile in self.board_model.tiles:
            cx, cy = self._grid_to_image(tile.grid_x, tile.grid_y)
            for next_id in tile.next_tiles:
                nt = self.board_model.get_tile(next_id)
                ncx, ncy = self._grid_to_image(nt.grid_x, nt.grid_y)
                img.line(cx, cy, ncx, ncy, ROAD_COLOR)

        # マスを奥(gx+gy 小)→手前(大) の順に描く
        sorted_tiles = sorted(
            self.board_model.tiles,
            key=lambda t: (t.grid_x + t.grid_y, t.grid_y),
        )

        # マス配置を辞書化（プレイヤー/建物の配置に使う）
        tile_pos = {}
        for tile in sorted_tiles:
            cx, cy = self._grid_to_image(tile.grid_x, tile.grid_y)
            tile_pos[tile.id] = (cx, cy)
            color = TILE_COLORS.get(tile.tile_type, 5)
            border = TILE_OWNED_BORDER if tile.is_owned else TILE_BORDER_COLOR
            _draw_tile_block(img, cx, cy, color, border)

            # マスラベル（大きめに）
            label = None
            if tile.tile_type == "plus":
                label = "+"
            elif tile.tile_type == "minus":
                label = "-"
            elif tile.tile_type == "card_shop":
                label = "S"
            elif tile.tile_type == "card":
                label = "C"
            if label:
                img.text(cx - 2, cy - 3, label, 7)

        # 建物とプレイヤーを奥→手前で描画（タイル順と同じ順）
        # 同一タイル内では: 建物 → プレイヤー（プレイヤーを手前に）
        owner_color_map = {}
        if players:
            for p in players:
                owner_color_map[p.id] = p.color

        tile_player_idx = {}  # tile_id → 次に配置するプレイヤーのインデックス
        moving_player = None
        if move_info:
            moving_player = move_info["player_id"]

        for tile in sorted_tiles:
            cx, cy = tile_pos[tile.id]

            # 建物
            if tile.has_company:
                oc = owner_color_map.get(tile.company.owner_id, 7)
                draw_building(img, cx, cy, oc)

            # そのマス上のプレイヤー
            if players:
                for p in players:
                    if p.is_bankrupt:
                        continue
                    if moving_player is not None and p.id == moving_player:
                        continue
                    if p.position != tile.id:
                        continue
                    idx = tile_player_idx.get(tile.id, 0)
                    tile_player_idx[tile.id] = idx + 1
                    ox, oy = _PLAYER_OFFSETS[idx % len(_PLAYER_OFFSETS)]
                    draw_player(img, cx + ox, cy + oy, p.color, p.id)

        # 移動中プレイヤー: from→to 間を補間して単独描画（最後に描いて最前面へ）
        if move_info and players:
            mp = next((p for p in players if p.id == move_info["player_id"]), None)
            if mp is not None and not mp.is_bankrupt:
                fx, fy = tile_pos.get(move_info["from_tile"], (BOARD_CX, BOARD_CY))
                tx, ty = tile_pos.get(move_info["to_tile"], (BOARD_CX, BOARD_CY))
                prog = move_info["progress"]
                # アーチ軌道（少しジャンプさせる）
                bounce = -8 * prog * (1 - prog)
                px = fx + (tx - fx) * prog
                py = fy + (ty - fy) * prog + bounce
                draw_player(img, int(px), int(py), mp.color, mp.id)

    def draw_tile_info(self, tile, x, y):
        """マス情報のツールチップ描画（スクリーン直描き）"""
        from src.ui.font import draw_text
        pyxel.rect(x, y, 120, 40, 0)
        pyxel.rectb(x, y, 120, 40, 7)
        draw_text(x + 4, y + 4, tile.name, 7)
        if tile.tile_type == "normal":
            draw_text(x + 4, y + 14, f"価格:{tile.land_price}$", 7)
            if tile.has_company:
                draw_text(x + 4, y + 24, tile.company.name[:8], 10)
