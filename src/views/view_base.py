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
        """ボード＋プレイヤーをイメージバンクに描画（blt 拡大転送用）"""
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
    """ボードビューの切り替えを管理する

    view_type:
      - "isometric": ダイヤモンド投影の擬似 3D 描画（本番用）
      - "topview":   フラットな俯瞰（デバッグ用）
    """

    def __init__(self, board_model):
        from src.views.isometric.board_view import IsometricBoardView
        from src.views.isometric.player_view import IsometricPlayerView
        from src.views.topview.board_view import TopViewBoardView
        from src.views.topview.player_view import TopViewPlayerView

        self.board_model = board_model
        self.view_type = "isometric"

        self._iso_board = IsometricBoardView(board_model)
        self._iso_player = IsometricPlayerView()
        self._top_board = TopViewBoardView(board_model)
        self._top_player = TopViewPlayerView()

    @property
    def board_view(self):
        if self.view_type == "topview":
            return self._top_board
        return self._iso_board

    @property
    def player_view(self):
        if self.view_type == "topview":
            return self._top_player
        return self._iso_player

    def toggle_view(self):
        self.view_type = "topview" if self.view_type == "isometric" else "isometric"
