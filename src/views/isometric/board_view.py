"""ボード描画（アイソメトリックビュー）"""
import pyxel
from src.views.view_base import BoardViewBase
from src.ui.font import draw_text

IMG_SIZE = 256

# アイソメトリックタイルサイズ
ISO_TILE_W = 48  # ひし形の横幅
ISO_TILE_H = 24  # ひし形の高さ（= W/2）
ISO_TILE_DEPTH = 12  # 立体部分の高さ

# マップ原点（画面中央上部から展開）
ORIGIN_X = 256
ORIGIN_Y = 80

# オフスクリーン用の縮小アイソメトリックサイズ
OFF_ISO_W = 30
OFF_ISO_H = 15
OFF_ISO_DEPTH = 8

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

# 同一マス上のプレイヤー表示オフセット（イメージバンク用）
_PLAYER_IMG_OFFSETS = [(-4, -4), (4, -4), (-4, 4), (4, 4)]


class IsometricBoardView(BoardViewBase):
    """アイソメトリックでボードを描画する"""

    def __init__(self, board_model):
        super().__init__(board_model)

        # オフスクリーン描画のオフセット（ボードを256x256の中央に配置）
        if board_model.tiles:
            positions = [self._grid_to_off_iso(t.grid_x, t.grid_y)
                         for t in board_model.tiles]
            min_x = min(p[0] for p in positions)
            max_x = max(p[0] for p in positions) + OFF_ISO_W
            min_y = min(p[1] for p in positions)
            max_y = max(p[1] for p in positions) + OFF_ISO_H + OFF_ISO_DEPTH
            board_w = max_x - min_x
            board_h = max_y - min_y
            self._img_ox = (IMG_SIZE - board_w) // 2 - min_x
            self._img_oy = (IMG_SIZE - board_h) // 2 - min_y
        else:
            self._img_ox = 0
            self._img_oy = 0

    def _grid_to_iso(self, grid_x, grid_y):
        """グリッド座標→アイソメトリックスクリーン座標"""
        sx = ORIGIN_X + (grid_x - grid_y) * (ISO_TILE_W // 2)
        sy = ORIGIN_Y + (grid_x + grid_y) * (ISO_TILE_H // 2)
        return (sx, sy)

    def _grid_to_off_iso(self, grid_x, grid_y):
        """グリッド座標→オフスクリーン用アイソメトリック座標"""
        sx = (grid_x - grid_y) * (OFF_ISO_W // 2)
        sy = (grid_x + grid_y) * (OFF_ISO_H // 2)
        return (sx, sy)

    def tile_screen_pos(self, tile_id: int, camera_x=0, camera_y=0):
        tile = self.board_model.get_tile(tile_id)
        sx, sy = self._grid_to_iso(tile.grid_x, tile.grid_y)
        return (sx - camera_x, sy - camera_y)

    def tile_image_pos(self, tile_id):
        """タイルのイメージバンク上の中心座標を返す"""
        tile = self.board_model.get_tile(tile_id)
        sx, sy = self._grid_to_off_iso(tile.grid_x, tile.grid_y)
        cx = sx + self._img_ox + OFF_ISO_W // 2
        cy = sy + self._img_oy + OFF_ISO_H // 2
        return (cx, cy)

    # ------------------------------------------------------------------
    # 通常スクリーン描画（従来互換）
    # ------------------------------------------------------------------
    def draw_board(self, camera_x=0, camera_y=0):
        for tile in self.board_model.tiles:
            sx, sy = self.tile_screen_pos(tile.id, camera_x, camera_y)
            cx = sx + ISO_TILE_W // 2
            cy = sy + ISO_TILE_H // 2
            for next_id in tile.next_tiles:
                nx, ny = self.tile_screen_pos(next_id, camera_x, camera_y)
                ncx = nx + ISO_TILE_W // 2
                ncy = ny + ISO_TILE_H // 2
                pyxel.line(cx, cy, ncx, ncy, ROAD_COLOR)

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

        hw = ISO_TILE_W // 2
        hh = ISO_TILE_H // 2
        d = ISO_TILE_DEPTH

        cx = sx + hw
        cy = sy + hh

        pyxel.tri(cx - hw, cy, cx, cy + hh, cx, cy + hh + d, side_color)
        pyxel.tri(cx - hw, cy, cx, cy + hh + d, cx - hw, cy + d, side_color)

        darker = 1
        pyxel.tri(cx + hw, cy, cx, cy + hh, cx, cy + hh + d, darker)
        pyxel.tri(cx + hw, cy, cx, cy + hh + d, cx + hw, cy + d, darker)

        pyxel.tri(cx, cy - hh, cx + hw, cy, cx, cy + hh, top_color)
        pyxel.tri(cx, cy - hh, cx, cy + hh, cx - hw, cy, top_color)

        pyxel.line(cx, cy - hh, cx + hw, cy, border)
        pyxel.line(cx + hw, cy, cx, cy + hh, border)
        pyxel.line(cx, cy + hh, cx - hw, cy, border)
        pyxel.line(cx - hw, cy, cx, cy - hh, border)
        pyxel.line(cx - hw, cy, cx - hw, cy + d, border)
        pyxel.line(cx + hw, cy, cx + hw, cy + d, border)
        pyxel.line(cx - hw, cy + d, cx, cy + hh + d, border)
        pyxel.line(cx, cy + hh + d, cx + hw, cy + d, border)

        if tile.has_company:
            self._draw_building(cx, cy, tile)

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
        bw = 10
        bh = 18
        by = cy - bh

        pyxel.rect(cx - bw, by, bw * 2, bh, 7)
        pyxel.tri(cx - bw - 2, by, cx, by - 6, cx + bw + 2, by, 5)
        pyxel.rect(cx - 6, by + 4, 4, 4, 12)
        pyxel.rect(cx + 2, by + 4, 4, 4, 12)
        pyxel.rect(cx - 3, by + 10, 6, 8, 0)

    # ------------------------------------------------------------------
    # オフスクリーン描画 → blt3d 用
    # ------------------------------------------------------------------
    def draw_board_to_image(self, img, players=None, move_info=None):
        """ボード＋プレイヤーをイメージバンクに描画（blt3d転送用）"""
        img.cls(0)
        ox, oy = self._img_ox, self._img_oy

        # 道（接続線）
        for tile in self.board_model.tiles:
            sx, sy = self._grid_to_off_iso(tile.grid_x, tile.grid_y)
            sx += ox
            sy += oy
            cx = sx + OFF_ISO_W // 2
            cy = sy + OFF_ISO_H // 2
            for next_id in tile.next_tiles:
                nt = self.board_model.get_tile(next_id)
                nx, ny = self._grid_to_off_iso(nt.grid_x, nt.grid_y)
                nx += ox
                ny += oy
                ncx = nx + OFF_ISO_W // 2
                ncy = ny + OFF_ISO_H // 2
                img.line(cx, cy, ncx, ncy, ROAD_COLOR)

        # マスを奥から手前に描画
        sorted_tiles = sorted(
            self.board_model.tiles,
            key=lambda t: t.grid_x + t.grid_y
        )
        for tile in sorted_tiles:
            sx, sy = self._grid_to_off_iso(tile.grid_x, tile.grid_y)
            sx += ox
            sy += oy
            top_color, side_color = TILE_COLORS.get(tile.tile_type, (5, 13))
            border = TILE_OWNED_BORDER if tile.is_owned else TILE_BORDER_COLOR
            hw = OFF_ISO_W // 2
            hh = OFF_ISO_H // 2
            d = OFF_ISO_DEPTH
            cx = sx + hw
            cy = sy + hh

            # 側面
            img.tri(cx - hw, cy, cx, cy + hh, cx, cy + hh + d, side_color)
            img.tri(cx - hw, cy, cx, cy + hh + d, cx - hw, cy + d, side_color)
            img.tri(cx + hw, cy, cx, cy + hh, cx, cy + hh + d, 1)
            img.tri(cx + hw, cy, cx, cy + hh + d, cx + hw, cy + d, 1)

            # 上面
            img.tri(cx, cy - hh, cx + hw, cy, cx, cy + hh, top_color)
            img.tri(cx, cy - hh, cx, cy + hh, cx - hw, cy, top_color)

            # 枠線
            img.line(cx, cy - hh, cx + hw, cy, border)
            img.line(cx + hw, cy, cx, cy + hh, border)
            img.line(cx, cy + hh, cx - hw, cy, border)
            img.line(cx - hw, cy, cx, cy - hh, border)
            img.line(cx - hw, cy, cx - hw, cy + d, border)
            img.line(cx + hw, cy, cx + hw, cy + d, border)
            img.line(cx - hw, cy + d, cx, cy + hh + d, border)
            img.line(cx, cy + hh + d, cx + hw, cy + d, border)

            if tile.tile_type == "plus":
                img.text(cx - 2, cy - 3, "+", 7)
            elif tile.tile_type == "minus":
                img.text(cx - 2, cy - 3, "-", 7)
            elif tile.tile_type == "card_shop":
                img.text(cx - 2, cy - 3, "S", 7)
            elif tile.tile_type == "card":
                img.text(cx - 2, cy - 3, "C", 7)

        # プレイヤー
        if players:
            tile_counts = {}
            for p in players:
                if p.is_bankrupt:
                    continue
                if move_info and p.id == move_info["player_id"]:
                    fx, fy = self.tile_image_pos(move_info["from_tile"])
                    tx, ty = self.tile_image_pos(move_info["to_tile"])
                    prog = move_info["progress"]
                    px = int(fx + (tx - fx) * prog)
                    py = int(fy + (ty - fy) * prog)
                    img.circ(px, py, 2, p.color)
                    continue
                tid = p.position
                if tid not in tile_counts:
                    tile_counts[tid] = 0
                idx = tile_counts[tid]
                tile_counts[tid] += 1
                tx, ty = self.tile_image_pos(tid)
                dx, dy = _PLAYER_IMG_OFFSETS[idx % len(_PLAYER_IMG_OFFSETS)]
                img.circ(tx + dx, ty + dy, 2, p.color)

    def draw_tile_info(self, tile, x, y):
        """マス情報のツールチップ描画"""
        pyxel.rect(x, y, 120, 40, 0)
        pyxel.rectb(x, y, 120, 40, 7)
        draw_text(x + 4, y + 4, tile.name, 7)
        if tile.tile_type == "normal":
            draw_text(x + 4, y + 14, f"価格:{tile.land_price}$", 7)
            if tile.has_company:
                draw_text(x + 4, y + 24, tile.company.name[:8], 10)
