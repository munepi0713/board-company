"""ボード描画（トップビュー）- ダミーグラフィックス"""
import pyxel
from src.views.view_base import BoardViewBase
from src.core.rules import TILE_SIZE

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


class TopViewBoardView(BoardViewBase):
    """トップビューでボードを描画する（ダミーグラフィックス）"""

    def __init__(self, board_model):
        super().__init__(board_model)
        self.offset_x = 64
        self.offset_y = 48

    def tile_screen_pos(self, tile_id: int, camera_x=0, camera_y=0):
        tile = self.board_model.get_tile(tile_id)
        sx = tile.grid_x * (TILE_SIZE + 4) + self.offset_x - camera_x
        sy = tile.grid_y * (TILE_SIZE + 4) + self.offset_y - camera_y
        return (sx, sy)

    def draw_board(self, camera_x=0, camera_y=0):
        # まず道（接続線）を描画
        for tile in self.board_model.tiles:
            sx, sy = self.tile_screen_pos(tile.id, camera_x, camera_y)
            cx = sx + TILE_SIZE // 2
            cy = sy + TILE_SIZE // 2
            for next_id in tile.next_tiles:
                nx, ny = self.tile_screen_pos(next_id, camera_x, camera_y)
                ncx = nx + TILE_SIZE // 2
                ncy = ny + TILE_SIZE // 2
                pyxel.line(cx, cy, ncx, ncy, ROAD_COLOR)

        # マスを描画
        for tile in self.board_model.tiles:
            self.draw_tile(tile, camera_x, camera_y)

    def draw_tile(self, tile, camera_x=0, camera_y=0):
        sx, sy = self.tile_screen_pos(tile.id, camera_x, camera_y)
        color = TILE_COLORS.get(tile.tile_type, 5)

        # マスの背景
        pyxel.rect(sx, sy, TILE_SIZE, TILE_SIZE, color)

        # 枠
        border = TILE_OWNED_BORDER if tile.is_owned else TILE_BORDER_COLOR
        pyxel.rectb(sx, sy, TILE_SIZE, TILE_SIZE, border)

        # 会社がある場合、小さな建物アイコン
        if tile.has_company:
            bx = sx + 4
            by = sy + 4
            pyxel.rect(bx, by, 10, 12, 7)  # 建物（白い四角）
            pyxel.rect(bx + 2, by + 6, 6, 6, 0)  # ドア
            pyxel.pset(bx + 4, by + 2, 8)  # 窓
            pyxel.pset(bx + 4, by + 4, 8)  # 窓

        # マスタイプ表示
        if tile.tile_type == "plus":
            pyxel.text(sx + 12, sy + 12, "+", 7)
        elif tile.tile_type == "minus":
            pyxel.text(sx + 12, sy + 12, "-", 7)
        elif tile.tile_type == "card_shop":
            pyxel.text(sx + 10, sy + 12, "S", 7)
        elif tile.tile_type == "card":
            pyxel.text(sx + 10, sy + 12, "C", 7)

    def draw_tile_info(self, tile, x, y):
        """マス情報のツールチップ描画"""
        pyxel.rect(x, y, 120, 40, 0)
        pyxel.rectb(x, y, 120, 40, 7)
        pyxel.text(x + 4, y + 4, tile.name, 7)
        if tile.tile_type == "normal":
            pyxel.text(x + 4, y + 14, f"Price:{tile.land_price}$", 7)
            if tile.has_company:
                pyxel.text(x + 4, y + 24, tile.company.name[:8], 10)
