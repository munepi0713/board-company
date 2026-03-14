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

    def tile_image_pos(self, tile_id):
        """タイルのイメージバンク上の中心座標を返す"""
        return (128, 128)

    def draw_board_to_image(self, img, players=None, move_info=None):
        """ボード＋プレイヤーをイメージバンクに描画（blt3d用）"""
        pass


class PlayerViewBase(ABC):
    """プレイヤー描画の基底クラス"""

    @abstractmethod
    def draw_player(self, player, screen_x: int, screen_y: int):
        pass

    @abstractmethod
    def draw_move_animation(self, player, from_pos, to_pos, progress: float):
        pass


class ViewManager:
    """ビューの切り替えを管理（ボード層＋プレイヤー層のみ）"""

    def __init__(self, board_model):
        from src.views.topview.board_view import TopViewBoardView
        from src.views.topview.player_view import TopViewPlayerView
        from src.views.isometric.board_view import IsometricBoardView
        from src.views.isometric.player_view import IsometricPlayerView

        self.board_model = board_model
        self.view_type = "topview"
        self._board_views = {
            "topview": TopViewBoardView(board_model),
            "isometric": IsometricBoardView(board_model),
        }
        self._player_views = {
            "topview": TopViewPlayerView(),
            "isometric": IsometricPlayerView(),
        }

    @property
    def board_view(self):
        return self._board_views[self.view_type]

    @property
    def player_view(self):
        return self._player_views[self.view_type]

    def toggle_view(self):
        """トップビュー⇔アイソメトリックを切り替え"""
        self.view_type = "isometric" if self.view_type == "topview" else "topview"
