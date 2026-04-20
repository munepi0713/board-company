"""プレイヤー描画（アイソメトリック）

オフスクリーン描画はすべて board_view.draw_board_to_image() で一括処理している。
このクラスは PlayerViewBase の抽象要件を満たすためのプレースホルダ。
"""
from src.views.view_base import PlayerViewBase


class IsometricPlayerView(PlayerViewBase):
    def draw_player(self, player, screen_x: int, screen_y: int, index_on_tile: int = 0):
        """未使用（board_view 内で一括描画）"""
        pass

    def draw_move_animation(self, player, from_pos, to_pos, progress: float):
        """未使用（board_view 内で一括描画）"""
        pass
