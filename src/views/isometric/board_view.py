"""ボード描画（アイソメトリックビュー）"""
import pyxel
from src.views.view_base import BoardViewBase
from src.ui.font import draw_text

# アイソメトリックタイルサイズ
ISO_TILE_W = 48  # ひし形の横幅
ISO_TILE_H = 24  # ひし形の高さ（= W/2）
ISO_TILE_DEPTH = 12  # 立体部分の高さ

# マップ原点（画面中央上部から展開）
ORIGIN_X = 256
ORIGIN_Y = 80

# マスタイプごとの色（上面 / 側面）
TILE_COLORS = {
    "normal":    (3, 13),   # 緑 / 暗い緑
    "card_shop": (9, 4),    # オレンジ / 暗いオレンジ
    "plus":      (11, 3),   # 黄緑 / 緑
    "minus":     (2, 1),    # 紫 / 暗い紫
    "card":      (10, 9),   # 黄色 / オレンジ
}

TILE_BORDER_COLOR = 1
TILE_OWNED_BORDER = 8
ROAD_COLOR = 13


class IsometricBoardView(BoardViewBase):
    """アイソメトリックでボードを描画する"""

    def __init__(self, board_model):
        super().__init__(board_model)

    def _grid_to_iso(self, grid_x, grid_y):
        """グリッド座標→アイソメトリックスクリーン座標"""
        sx = ORIGIN_X + (grid_x - grid_y) * (ISO_TILE_W // 2)
        sy = ORIGIN_Y + (grid_x + grid_y) * (ISO_TILE_H // 2)
        return (sx, sy)

    def tile_screen_pos(self, tile_id: int, camera_x=0, camera_y=0):
        tile = self.board_model.get_tile(tile_id)
        sx, sy = self._grid_to_iso(tile.grid_x, tile.grid_y)
        return (sx - camera_x, sy - camera_y)

    def draw_board(self, camera_x=0, camera_y=0):
        # 道（接続線）を先に描画
        for tile in self.board_model.tiles:
            sx, sy = self.tile_screen_pos(tile.id, camera_x, camera_y)
            cx = sx + ISO_TILE_W // 2
            cy = sy + ISO_TILE_H // 2
            for next_id in tile.next_tiles:
                nx, ny = self.tile_screen_pos(next_id, camera_x, camera_y)
                ncx = nx + ISO_TILE_W // 2
                ncy = ny + ISO_TILE_H // 2
                pyxel.line(cx, cy, ncx, ncy, ROAD_COLOR)

        # タイルを奥から手前に描画（Painter's Algorithm）
        sorted_tiles = sorted(
            self.board_model.tiles,
            key=lambda t: t.grid_x + t.grid_y
        )
        for tile in sorted_tiles:
            self.draw_tile(tile, camera_x, camera_y)

    def draw_tile(self, tile, camera_x=0, camera_y=0):
        sx, sy = self.tile_screen_pos(tile.id, camera_x, camera_y)
        top_color, side_color = TILE_COLORS.get(tile.tile_type, (5, 13))
        border = TILE_OWNED_BORDER if tile.is_owned else TILE_BORDER_COLOR

        hw = ISO_TILE_W // 2  # 24
        hh = ISO_TILE_H // 2  # 12
        d = ISO_TILE_DEPTH

        # タイル中心
        cx = sx + hw
        cy = sy + hh

        # 左側面（平行四辺形）
        # 頂点: 左(cx-hw, cy) → 下(cx, cy+hh) → 下+d(cx, cy+hh+d) → 左+d(cx-hw, cy+d)
        pyxel.tri(cx - hw, cy, cx, cy + hh, cx, cy + hh + d, side_color)
        pyxel.tri(cx - hw, cy, cx, cy + hh + d, cx - hw, cy + d, side_color)

        # 右側面（平行四辺形）
        # 頂点: 右(cx+hw, cy) → 下(cx, cy+hh) → 下+d(cx, cy+hh+d) → 右+d(cx+hw, cy+d)
        darker = 1  # より暗い色
        pyxel.tri(cx + hw, cy, cx, cy + hh, cx, cy + hh + d, darker)
        pyxel.tri(cx + hw, cy, cx, cy + hh + d, cx + hw, cy + d, darker)

        # 上面（ひし形）
        # 頂点: 上(cx, cy-hh) → 右(cx+hw, cy) → 下(cx, cy+hh) → 左(cx-hw, cy)
        pyxel.tri(cx, cy - hh, cx + hw, cy, cx, cy + hh, top_color)
        pyxel.tri(cx, cy - hh, cx, cy + hh, cx - hw, cy, top_color)

        # 枠線
        # 上面の輪郭
        pyxel.line(cx, cy - hh, cx + hw, cy, border)
        pyxel.line(cx + hw, cy, cx, cy + hh, border)
        pyxel.line(cx, cy + hh, cx - hw, cy, border)
        pyxel.line(cx - hw, cy, cx, cy - hh, border)
        # 側面の輪郭
        pyxel.line(cx - hw, cy, cx - hw, cy + d, border)
        pyxel.line(cx + hw, cy, cx + hw, cy + d, border)
        pyxel.line(cx - hw, cy + d, cx, cy + hh + d, border)
        pyxel.line(cx, cy + hh + d, cx + hw, cy + d, border)

        # 会社がある場合、立体的な建物
        if tile.has_company:
            self._draw_building(cx, cy, tile)

        # マスタイプ表示（上面中央）
        if tile.tile_type == "plus":
            pyxel.text(cx - 2, cy - 3, "+", 7)
        elif tile.tile_type == "minus":
            pyxel.text(cx - 2, cy - 3, "-", 7)
        elif tile.tile_type == "card_shop":
            pyxel.text(cx - 2, cy - 3, "S", 7)
        elif tile.tile_type == "card":
            pyxel.text(cx - 2, cy - 3, "C", 7)

    def _draw_building(self, cx, cy, tile):
        """タイル上に立体的な建物を描画"""
        bw = 10  # 建物の幅（半分）
        bh = 18  # 建物の高さ

        # 建物のベース（タイル上面の少し上）
        by = cy - bh

        # 正面
        pyxel.rect(cx - bw, by, bw * 2, bh, 7)
        # 屋根
        pyxel.tri(cx - bw - 2, by, cx, by - 6, cx + bw + 2, by, 5)
        # 窓
        pyxel.rect(cx - 6, by + 4, 4, 4, 12)
        pyxel.rect(cx + 2, by + 4, 4, 4, 12)
        # ドア
        pyxel.rect(cx - 3, by + 10, 6, 8, 0)

    def draw_tile_info(self, tile, x, y):
        """マス情報のツールチップ描画"""
        pyxel.rect(x, y, 120, 40, 0)
        pyxel.rectb(x, y, 120, 40, 7)
        draw_text(x + 4, y + 4, tile.name, 7)
        if tile.tile_type == "normal":
            draw_text(x + 4, y + 14, f"価格:{tile.land_price}$", 7)
            if tile.has_company:
                draw_text(x + 4, y + 24, tile.company.name[:8], 10)
