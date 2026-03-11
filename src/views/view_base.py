"""ビュー基底クラス・インターフェース"""
from abc import ABC, abstractmethod


class BoardViewBase(ABC):
    """ボード描画の基底クラス"""

    def __init__(self, board_model):
        self.board_model = board_model

    @abstractmethod
    def draw_board(self, camera_x=0, camera_y=0):
        pass

    @abstractmethod
    def draw_tile(self, tile, camera_x=0, camera_y=0):
        pass

    @abstractmethod
    def tile_screen_pos(self, tile_id: int, camera_x=0, camera_y=0):
        pass


class PlayerViewBase(ABC):
    """プレイヤー描画の基底クラス"""

    @abstractmethod
    def draw_player(self, player, screen_x: int, screen_y: int):
        pass

    @abstractmethod
    def draw_move_animation(self, player, from_pos, to_pos, progress: float):
        pass
