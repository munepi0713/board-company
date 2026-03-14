"""プレイヤー描画（アイソメトリックビュー）"""
import pyxel
from src.views.view_base import PlayerViewBase
from src.views.isometric.board_view import ISO_TILE_W, ISO_TILE_H

# プレイヤーの位置オフセット（同マスに複数いる場合、ひし形上面内に配置）
PLAYER_OFFSETS = [
    (ISO_TILE_W // 2 - 6, -4),
    (ISO_TILE_W // 2 + 6, -4),
    (ISO_TILE_W // 2 - 6, 6),
    (ISO_TILE_W // 2 + 6, 6),
]


class IsometricPlayerView(PlayerViewBase):
    """アイソメトリックでプレイヤーを描画する"""

    def draw_player(self, player, screen_x: int, screen_y: int, index_on_tile: int = 0):
        """プレイヤーをアイソメトリック座標上に描画"""
        ox, oy = PLAYER_OFFSETS[index_on_tile % len(PLAYER_OFFSETS)]
        px = screen_x + ox
        py = screen_y + oy

        color = player.color

        # 影（楕円）
        pyxel.elli(px - 5, py + 8, 10, 5, 1)

        # 体（台形風）
        pyxel.rect(px - 4, py, 8, 8, color)
        # 頭（丸）
        pyxel.circ(px, py - 3, 4, color)
        # プレイヤー番号
        pyxel.text(px - 1, py + 1, str(player.id), 7)

    def draw_move_animation(self, player, from_pos, to_pos, progress: float):
        """移動アニメーション"""
        fx, fy = from_pos
        tx, ty = to_pos
        cx = int(fx + (tx - fx) * progress)
        cy = int(fy + (ty - fy) * progress)
        self.draw_player(player, cx, cy)
