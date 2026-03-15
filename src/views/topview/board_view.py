"""ボード描画（トップビュー）- ダミーグラフィックス"""
import pyxel
from src.views.view_base import BoardViewBase
from src.ui.font import draw_text
from src.core.rules import TILE_SIZE

# イメージバンクサイズ
IMG_SIZE = 256

# オフスクリーン描画用の縮小サイズ
OFF_TILE = 20   # マス1つの大きさ
OFF_GAP = 2     # マス間の隙間
OFF_STEP = OFF_TILE + OFF_GAP  # 22px / マス

# マスタイプごとの色
TILE_COLORS = {
    "normal": 3,      # 緑（暗め）
    "card_shop": 9,   # オレンジ
    "plus": 11,       # 黄緑
    "minus": 2,       # 紫
    "card": 10,       # 黄色
}

# マスの枠色
TILE_BORDER_COLOR = 1  # 濃い青
TILE_OWNED_BORDER = 8  # 赤
ROAD_COLOR = 13        # 灰色

# 同一マス上のプレイヤー表示オフセット（イメージバンク用）
_PLAYER_IMG_OFFSETS = [(-6, -2), (6, -2), (-6, 6), (6, 6)]


class TopViewBoardView(BoardViewBase):
    """トップビューでボードを描画する（ダミーグラフィックス）"""

    def __init__(self, board_model):
        super().__init__(board_model)
        self.offset_x = 64
        self.offset_y = 48

        # オフスクリーン描画のオフセット（ボードを256x256の中央に配置）
        max_gx = max(t.grid_x for t in board_model.tiles) if board_model.tiles else 0
        max_gy = max(t.grid_y for t in board_model.tiles) if board_model.tiles else 0
        board_w = (max_gx + 1) * OFF_STEP
        board_h = (max_gy + 1) * OFF_STEP
        self._img_ox = (IMG_SIZE - board_w) // 2
        self._img_oy = (IMG_SIZE - board_h) // 2

    def tile_screen_pos(self, tile_id: int, camera_x=0, camera_y=0):
        tile = self.board_model.get_tile(tile_id)
        sx = tile.grid_x * (TILE_SIZE + 4) + self.offset_x - camera_x
        sy = tile.grid_y * (TILE_SIZE + 4) + self.offset_y - camera_y
        return (sx, sy)

    def tile_image_pos(self, tile_id):
        """タイルのイメージバンク上の中心座標を返す"""
        tile = self.board_model.get_tile(tile_id)
        x = tile.grid_x * OFF_STEP + self._img_ox + OFF_TILE // 2
        y = tile.grid_y * OFF_STEP + self._img_oy + OFF_TILE // 2
        return (x, y)

    # ------------------------------------------------------------------
    # 通常スクリーン描画（従来互換、blt3d不使用時用）
    # ------------------------------------------------------------------
    def draw_board(self, camera_x=0, camera_y=0):
        for tile in self.board_model.tiles:
            sx, sy = self.tile_screen_pos(tile.id, camera_x, camera_y)
            cx = sx + TILE_SIZE // 2
            cy = sy + TILE_SIZE // 2
            for next_id in tile.next_tiles:
                nx, ny = self.tile_screen_pos(next_id, camera_x, camera_y)
                ncx = nx + TILE_SIZE // 2
                ncy = ny + TILE_SIZE // 2
                pyxel.line(cx, cy, ncx, ncy, ROAD_COLOR)

        for tile in self.board_model.tiles:
            self.draw_tile(tile, camera_x, camera_y)

    def draw_tile(self, tile, camera_x=0, camera_y=0):
        sx, sy = self.tile_screen_pos(tile.id, camera_x, camera_y)
        color = TILE_COLORS.get(tile.tile_type, 5)

        pyxel.rect(sx, sy, TILE_SIZE, TILE_SIZE, color)

        border = TILE_OWNED_BORDER if tile.is_owned else TILE_BORDER_COLOR
        pyxel.rectb(sx, sy, TILE_SIZE, TILE_SIZE, border)

        if tile.has_company:
            bx = sx + 4
            by = sy + 4
            pyxel.rect(bx, by, 10, 12, 7)
            pyxel.rect(bx + 2, by + 6, 6, 6, 0)
            pyxel.pset(bx + 4, by + 2, 8)
            pyxel.pset(bx + 4, by + 4, 8)

        if tile.tile_type == "plus":
            pyxel.text(sx + 12, sy + 12, "+", 7)
        elif tile.tile_type == "minus":
            pyxel.text(sx + 12, sy + 12, "-", 7)
        elif tile.tile_type == "card_shop":
            pyxel.text(sx + 10, sy + 12, "S", 7)
        elif tile.tile_type == "card":
            pyxel.text(sx + 10, sy + 12, "C", 7)

    # ------------------------------------------------------------------
    # オフスクリーン描画 → blt3d 用
    # ------------------------------------------------------------------
    def draw_board_to_image(self, img, players=None, move_info=None):
        """ボード＋プレイヤーをイメージバンクに描画（blt3d転送用）"""
        img.cls(0)
        ox, oy = self._img_ox, self._img_oy

        # 道（接続線）
        for tile in self.board_model.tiles:
            sx = tile.grid_x * OFF_STEP + ox
            sy = tile.grid_y * OFF_STEP + oy
            cx = sx + OFF_TILE // 2
            cy = sy + OFF_TILE // 2
            for next_id in tile.next_tiles:
                nt = self.board_model.get_tile(next_id)
                nx = nt.grid_x * OFF_STEP + ox
                ny = nt.grid_y * OFF_STEP + oy
                ncx = nx + OFF_TILE // 2
                ncy = ny + OFF_TILE // 2
                img.line(cx, cy, ncx, ncy, ROAD_COLOR)

        # マス
        for tile in self.board_model.tiles:
            sx = tile.grid_x * OFF_STEP + ox
            sy = tile.grid_y * OFF_STEP + oy
            color = TILE_COLORS.get(tile.tile_type, 5)
            img.rect(sx, sy, OFF_TILE, OFF_TILE, color)
            border = TILE_OWNED_BORDER if tile.is_owned else TILE_BORDER_COLOR
            img.rectb(sx, sy, OFF_TILE, OFF_TILE, border)

            # 建物マーカー（小さいドットのみ、ビルボードはスクリーン上に描画）
            if tile.has_company:
                img.pset(sx + OFF_TILE // 2, sy + OFF_TILE // 2, 7)

            tcx = sx + OFF_TILE // 2 - 2
            tcy = sy + OFF_TILE // 2 - 2
            if tile.tile_type == "plus":
                img.text(tcx, tcy, "+", 7)
            elif tile.tile_type == "minus":
                img.text(tcx, tcy, "-", 7)
            elif tile.tile_type == "card_shop":
                img.text(tcx, tcy, "S", 7)
            elif tile.tile_type == "card":
                img.text(tcx, tcy, "C", 7)

        # プレイヤーマーカー（小さいドットのみ、ビルボードはスクリーン上に描画）
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
                    img.pset(px, py, p.color)
                    continue
                tid = p.position
                if tid not in tile_counts:
                    tile_counts[tid] = 0
                idx = tile_counts[tid]
                tile_counts[tid] += 1
                tx, ty = self.tile_image_pos(tid)
                dx, dy = _PLAYER_IMG_OFFSETS[idx % len(_PLAYER_IMG_OFFSETS)]
                img.pset(tx + dx, ty + dy, p.color)

    def draw_tile_info(self, tile, x, y):
        """マス情報のツールチップ描画"""
        pyxel.rect(x, y, 120, 40, 0)
        pyxel.rectb(x, y, 120, 40, 7)
        draw_text(x + 4, y + 4, tile.name, 7)
        if tile.tile_type == "normal":
            draw_text(x + 4, y + 14, f"価格:{tile.land_price}$", 7)
            if tile.has_company:
                draw_text(x + 4, y + 24, tile.company.name[:8], 10)
