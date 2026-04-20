"""プレイヤー描画（トップビュー・デバッグ用）

オフスクリーン描画は board_view.draw_board_to_image() で一括処理する。
このクラスは抽象要件を満たすためのプレースホルダ。
"""
from src.views.view_base import PlayerViewBase


class TopViewPlayerView(PlayerViewBase):
    def draw_player(self, player, screen_x: int, screen_y: int, index_on_tile: int = 0):
        pass

    def draw_move_animation(self, player, from_pos, to_pos, progress: float):
        pass
