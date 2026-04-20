"""タイルズーム機能のユニットテスト＋統合テスト

TileZoomAnimation の scale/offset 補間・状態遷移、
draw_board_to_image / tile_image_pos の座標計算を検証する。

Usage:
    python tests/test_zoom.py
"""

import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src.ui.animation import TileZoomAnimation
from src.core.board_model import Tile, BoardModel


# ---------------------------------------------------------------------------
# ヘルパー
# ---------------------------------------------------------------------------

def _build_board():
    """map_default.json 相当のボードモデルを生成（Pyxel 不要）"""
    from src.utils.data_loader import load_map_data
    board, _goal = load_map_data()
    return board


def _make_small_board():
    tiles = [
        Tile(id=0, tile_type="normal", name="A", grid_x=0, grid_y=0, next_tiles=[1]),
        Tile(id=1, tile_type="plus", name="B", grid_x=1, grid_y=0, next_tiles=[2]),
        Tile(id=2, tile_type="minus", name="C", grid_x=2, grid_y=0, next_tiles=[3]),
        Tile(id=3, tile_type="card", name="D", grid_x=2, grid_y=1, next_tiles=[0]),
    ]
    return BoardModel(tiles)


# ===========================================================================
# 1. TileZoomAnimation ユニットテスト
# ===========================================================================

def test_default_scale_is_base():
    """非アクティブ時は BASE_SCALE を返す"""
    z = TileZoomAnimation()
    assert z.scale == z.BASE_SCALE
    ox, oy = z.offset
    assert abs(ox - z.BASE_OFFSET_X) < 1
    assert abs(oy - z.BASE_OFFSET_Y) < 1


def test_zoom_in_scale_progression():
    """ズームイン: scale は BASE → ZOOM に到達する"""
    z = TileZoomAnimation()
    z.start_zoom_in(100, 80)

    # 開始時（frame=0, progress=0 → eased=0）は BASE
    assert abs(z.scale - z.BASE_SCALE) < 1e-3

    for _ in range(z.ZOOM_IN_DURATION):
        z.update()

    # 完了時は ZOOM
    assert abs(z.scale - z.ZOOM_SCALE) < 1e-3


def test_zoom_out_scale_returns_to_base():
    """ズームアウト: scale が BASE に戻る"""
    z = TileZoomAnimation()
    z.start_zoom_in(100, 80)
    for _ in range(z.ZOOM_IN_DURATION):
        z.update()

    z.start_zoom_out()
    for _ in range(z.ZOOM_OUT_DURATION):
        z.update()

    assert abs(z.scale - z.BASE_SCALE) < 1e-3


def test_zoom_in_scale_monotonically_increases():
    """ズームイン中、scale は単調増加"""
    z = TileZoomAnimation()
    z.start_zoom_in(128, 104)
    prev = z.scale
    for _ in range(z.ZOOM_IN_DURATION):
        z.update()
        cur = z.scale
        assert cur >= prev - 1e-6, f"scale decreased: {prev} -> {cur}"
        prev = cur


def test_zoom_out_scale_monotonically_decreases():
    """ズームアウト中、scale は単調減少"""
    z = TileZoomAnimation()
    z.start_zoom_in(128, 104)
    for _ in range(z.ZOOM_IN_DURATION):
        z.update()

    z.start_zoom_out()
    prev = z.scale
    for _ in range(z.ZOOM_OUT_DURATION):
        z.update()
        cur = z.scale
        assert cur <= prev + 1e-6, f"scale increased: {prev} -> {cur}"
        prev = cur


def test_zoom_target_lands_near_focus_center():
    """ズームイン完了時、ターゲット画像座標は画面の FOCUS 位置近くに来る"""
    z = TileZoomAnimation()
    tx, ty = 50, 40
    z.start_zoom_in(tx, ty)
    for _ in range(z.ZOOM_IN_DURATION):
        z.update()

    sx, sy = z.project_image_to_screen(tx, ty)
    assert abs(sx - z.FOCUS_X) < 2, f"focus x off: {sx} vs {z.FOCUS_X}"
    assert abs(sy - z.FOCUS_Y) < 2, f"focus y off: {sy} vs {z.FOCUS_Y}"


def test_offset_no_nan_or_inf():
    """さまざまなターゲットで NaN/Inf が出ないこと"""
    for tx, ty in [(0, 0), (128, 104), (255, 207), (50, 200), (200, 30)]:
        z = TileZoomAnimation()
        z.start_zoom_in(tx, ty)
        for _ in range(z.ZOOM_IN_DURATION + 5):
            s = z.scale
            ox, oy = z.offset
            for v in (s, ox, oy):
                assert not math.isnan(v) and not math.isinf(v), \
                    f"NaN/Inf at ({tx},{ty}): scale={s}, offset=({ox},{oy})"
            z.update()


def test_finish_zoom_resets_to_base():
    """finish_zoom() 後は BASE 状態に戻る"""
    z = TileZoomAnimation()
    z.start_zoom_in(100, 100)
    for _ in range(10):
        z.update()
    z.finish_zoom()

    assert not z.active
    assert z.scale == z.BASE_SCALE


def test_on_complete_callback_fires():
    """ズームイン完了時にコールバックが呼ばれる"""
    called = [False]

    def cb():
        called[0] = True

    z = TileZoomAnimation()
    z.start_zoom_in(128, 104, on_complete=cb)
    for _ in range(z.ZOOM_IN_DURATION):
        z.update()
    assert called[0]


def test_double_zoom_in_resets_animation():
    """ズームイン中に再 start しても破綻しない"""
    z = TileZoomAnimation()
    z.start_zoom_in(50, 50)
    for _ in range(5):
        z.update()

    z.start_zoom_in(200, 150)
    assert z.active
    assert z.target_x == 200
    assert z.frame == 0

    for _ in range(z.ZOOM_IN_DURATION):
        z.update()
    sx, sy = z.project_image_to_screen(200, 150)
    assert abs(sx - z.FOCUS_X) < 2


def test_zoom_out_without_zoom_in():
    """zoom_in 無しで zoom_out でもクラッシュしない"""
    z = TileZoomAnimation()
    z.active = True
    z.start_zoom_out()
    for _ in range(z.ZOOM_OUT_DURATION):
        z.update()
    assert abs(z.scale - z.BASE_SCALE) < 1e-3


def test_eased_progress_range():
    """_eased_progress が [0, 1] の範囲内"""
    z = TileZoomAnimation()
    z.start_zoom_in(100, 100)
    for _ in range(z.ZOOM_IN_DURATION + 5):
        ep = z._eased_progress
        assert 0.0 <= ep <= 1.0
        z.update()

    z.start_zoom_out()
    for _ in range(z.ZOOM_OUT_DURATION + 5):
        ep = z._eased_progress
        assert 0.0 <= ep <= 1.0
        z.update()


# ===========================================================================
# 2. tile_image_pos 座標境界テスト（Pyxel必要 — ヘッドレスでスキップ）
# ===========================================================================

def _can_import_pyxel():
    try:
        import pyxel  # noqa: F401
        return True
    except Exception:
        return False


def test_tile_image_pos_bounds_topview():
    """TopView: 全タイル座標が 0〜IMG_W, 0〜IMG_H 内"""
    if not _can_import_pyxel():
        print("  SKIP (pyxel not available)")
        return

    from src.views.topview.board_view import TopViewBoardView, IMG_W, IMG_H
    board = _build_board()
    view = TopViewBoardView(board)

    for tile in board.tiles:
        x, y = view.tile_image_pos(tile.id)
        assert 0 <= x < IMG_W and 0 <= y < IMG_H, \
            f"TopView tile {tile.id} out of bounds: ({x}, {y})"


def test_tile_image_pos_bounds_isometric():
    """Isometric: 全タイル座標が 0〜IMG_W, 0〜IMG_H 内"""
    if not _can_import_pyxel():
        print("  SKIP (pyxel not available)")
        return

    from src.views.isometric.board_view import IsometricBoardView, IMG_W, IMG_H
    board = _build_board()
    view = IsometricBoardView(board)

    for tile in board.tiles:
        x, y = view.tile_image_pos(tile.id)
        assert 0 <= x < IMG_W and 0 <= y < IMG_H, \
            f"Isometric tile {tile.id} out of bounds: ({x}, {y})"


def test_tile_image_pos_distinct_isometric():
    """異なる grid のタイルは異なる画像座標を持つ（Isometric）"""
    if not _can_import_pyxel():
        print("  SKIP (pyxel not available)")
        return

    from src.views.isometric.board_view import IsometricBoardView
    board = _build_board()
    view = IsometricBoardView(board)

    positions = {}
    for tile in board.tiles:
        pos = view.tile_image_pos(tile.id)
        if pos in positions:
            other = positions[pos]
            t_other = board.get_tile(other)
            assert (tile.grid_x == t_other.grid_x and tile.grid_y == t_other.grid_y), \
                f"Tiles {tile.id} and {other} have same image pos {pos} but different grids"
        positions[pos] = tile.id


# ===========================================================================
# メイン
# ===========================================================================

def main():
    print("=" * 50)
    print("BOARD COMPANY - Zoom Unit Tests")
    print("=" * 50)

    tests = [
        test_default_scale_is_base,
        test_zoom_in_scale_progression,
        test_zoom_out_scale_returns_to_base,
        test_zoom_in_scale_monotonically_increases,
        test_zoom_out_scale_monotonically_decreases,
        test_zoom_target_lands_near_focus_center,
        test_offset_no_nan_or_inf,
        test_finish_zoom_resets_to_base,
        test_on_complete_callback_fires,
        test_double_zoom_in_resets_animation,
        test_zoom_out_without_zoom_in,
        test_eased_progress_range,
        test_tile_image_pos_bounds_topview,
        test_tile_image_pos_bounds_isometric,
        test_tile_image_pos_distinct_isometric,
    ]

    passed = 0
    failed = 0
    for test in tests:
        name = test.__name__
        try:
            print(f"[TEST] {name}")
            test()
            passed += 1
            print("  PASS")
        except Exception as e:
            print(f"  FAIL: {e}")
            failed += 1

    print("=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 50)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
