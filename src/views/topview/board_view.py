"""ボード描画（トップビュー）- デバッグ用途のシンプル表示

マスを平坦な正方形として描画する。主にデバッグ・動作確認用。
Isometric と同じ blt 拡大パイプラインに乗せるため、オフスクリーン描画のみ実装する。
"""
import pyxel
from src.views.view_base import BoardViewBase
from src.ui.font import draw_text

# オフスクリーン画像サイズ（Isometric と揃える）
IMG_W = 256
IMG_H = 208

# タイル1個あたりのサイズ
CELL_W = 22
CELL_H = 22
GAP = 2

# マスタイプごとの色
TILE_COLORS = {
    "normal": 3,
    "card_shop": 9,
    "plus": 11,
    "minus": 2,
    "card": 10,
}
TILE_BORDER_COLOR = 1
TILE_OWNED_BORDER = 8
ROAD_COLOR = 13

_PLAYER_OFFSETS = [(-5, -3), (5, -3), (-5, 5), (5, 5)]


class TopViewBoardView(BoardViewBase):
    """マスをフラットな正方形で描画（デバッグ用）"""

    def __init__(self, board_model):
        super().__init__(board_model)
        max_gx = max(t.grid_x for t in board_model.tiles) if board_model.tiles else 0
        max_gy = max(t.grid_y for t in board_model.tiles) if board_model.tiles else 0
        board_w = (max_gx + 1) * CELL_W + max_gx * GAP
        board_h = (max_gy + 1) * CELL_H + max_gy * GAP
        self._img_ox = (IMG_W - board_w) // 2
        self._img_oy = (IMG_H - board_h) // 2

        # スクリーン直描き用（未使用だが互換）
        self.offset_x = 64
        self.offset_y = 48

    # ------------------------------------------------------------------
    # 座標
    # ------------------------------------------------------------------
    def _grid_to_image_topleft(self, gx, gy):
        x = self._img_ox + gx * (CELL_W + GAP)
        y = self._img_oy + gy * (CELL_H + GAP)
        return (x, y)

    def tile_image_pos(self, tile_id: int):
        tile = self.board_model.get_tile(tile_id)
        x, y = self._grid_to_image_topleft(tile.grid_x, tile.grid_y)
        return (x + CELL_W // 2, y + CELL_H // 2)

    def tile_screen_pos(self, tile_id: int, camera_x=0, camera_y=0):
        tile = self.board_model.get_tile(tile_id)
        sx = tile.grid_x * 36 + self.offset_x - camera_x
        sy = tile.grid_y * 36 + self.offset_y - camera_y
        return (sx, sy)

    def draw_board(self, camera_x=0, camera_y=0):
        pass

    def draw_tile(self, tile, camera_x=0, camera_y=0):
        pass

    # ------------------------------------------------------------------
    # オフスクリーン描画
    # ------------------------------------------------------------------
    def draw_board_to_image(self, img, players=None, move_info=None):
        img.cls(0)

        # 道
        for tile in self.board_model.tiles:
            cx, cy = self.tile_image_pos(tile.id)
            for next_id in tile.next_tiles:
                nt = self.board_model.get_tile(next_id)
                ncx, ncy = self.tile_image_pos(nt.id)
                img.line(cx, cy, ncx, ncy, ROAD_COLOR)

        # マス
        for tile in self.board_model.tiles:
            x, y = self._grid_to_image_topleft(tile.grid_x, tile.grid_y)
            color = TILE_COLORS.get(tile.tile_type, 5)
            img.rect(x, y, CELL_W, CELL_H, color)
            border = TILE_OWNED_BORDER if tile.is_owned else TILE_BORDER_COLOR
            img.rectb(x, y, CELL_W, CELL_H, border)

            # ラベル
            tcx = x + CELL_W // 2 - 2
            tcy = y + CELL_H // 2 - 2
            label = {
                "plus": "+", "minus": "-",
                "card_shop": "S", "card": "C",
            }.get(tile.tile_type)
            if label:
                img.text(tcx, tcy, label, 7)

            # 建物マーカー
            if tile.has_company:
                img.rect(x + 3, y + 3, 4, 6, 7)

        # プレイヤー
        moving_player = move_info["player_id"] if move_info else None
        tile_idx = {}
        if players:
            for p in players:
                if p.is_bankrupt:
                    continue
                if moving_player is not None and p.id == moving_player:
                    continue
                tid = p.position
                idx = tile_idx.get(tid, 0)
                tile_idx[tid] = idx + 1
                tcx, tcy = self.tile_image_pos(tid)
                ox, oy = _PLAYER_OFFSETS[idx % len(_PLAYER_OFFSETS)]
                px = tcx + ox
                py = tcy + oy
                img.rect(px - 1, py - 1, 3, 3, p.color)
                img.pset(px, py - 2, 7)

        # 移動中プレイヤー
        if move_info and players:
            mp = next((p for p in players if p.id == move_info["player_id"]), None)
            if mp is not None and not mp.is_bankrupt:
                fx, fy = self.tile_image_pos(move_info["from_tile"])
                tx, ty = self.tile_image_pos(move_info["to_tile"])
                prog = move_info["progress"]
                px = int(fx + (tx - fx) * prog)
                py = int(fy + (ty - fy) * prog)
                img.rect(px - 1, py - 1, 3, 3, mp.color)
                img.pset(px, py - 2, 7)

    def draw_tile_info(self, tile, x, y):
        pyxel.rect(x, y, 120, 40, 0)
        pyxel.rectb(x, y, 120, 40, 7)
        draw_text(x + 4, y + 4, tile.name, 7)
        if tile.tile_type == "normal":
            draw_text(x + 4, y + 14, f"価格:{tile.land_price}$", 7)
            if tile.has_company:
                draw_text(x + 4, y + 24, tile.company.name[:8], 10)
