"""プレイヤー描画（トップビュー）- ダミーグラフィックス"""
import pyxel
from src.views.view_base import PlayerViewBase
from src.core.rules import PLAYER_SPRITE_W, PLAYER_SPRITE_H

# プレイヤーの位置オフセット（同マスに複数いる場合）
PLAYER_OFFSETS = [
    (4, 4),
    (18, 4),
    (4, 18),
    (18, 18),
]


class TopViewPlayerView(PlayerViewBase):
    """トップビューでプレイヤーを描画する（ダミーグラフィックス）"""

    def draw_player(self, player, screen_x: int, screen_y: int, index_on_tile: int = 0):
        """プレイヤーをダミーのキャラクターとして描画"""
        ox, oy = PLAYER_OFFSETS[index_on_tile % len(PLAYER_OFFSETS)]
        px = screen_x + ox
        py = screen_y + oy

        color = player.color

        # 頭（丸）
        pyxel.circ(px + 5, py + 3, 3, color)
        # 体（四角）
        pyxel.rect(px + 2, py + 6, 7, 6, color)
        # プレイヤー番号
        pyxel.text(px + 4, py + 7, str(player.id), 7)

    def draw_move_animation(self, player, from_pos, to_pos, progress: float):
        """移動アニメーション"""
        fx, fy = from_pos
        tx, ty = to_pos
        cx = int(fx + (tx - fx) * progress)
        cy = int(fy + (ty - fy) * progress)
        self.draw_player(player, cx, cy)
