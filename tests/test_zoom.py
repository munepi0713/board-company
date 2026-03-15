"""タイルズーム機能のユニットテスト＋統合テスト

TileZoomAnimation のカメラ補間・状態遷移、
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
    """最小限のボード（テスト用）"""
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

def test_default_camera_returns_normal_position():
    """非アクティブ時はデフォルト俯瞰位置を返す"""
    z = TileZoomAnimation()
    pos = z.camera_pos
    rot = z.camera_rot
    assert pos == (z.NORMAL_X, z.NORMAL_Y, z.NORMAL_Z), f"got {pos}"
    assert rot == (z.NORMAL_RX, z.NORMAL_RY, 0), f"got {rot}"
    assert z.fov == 90


def test_zoom_in_start_and_end_positions():
    """ズームイン: 開始は通常位置、終了はターゲット位置"""
    z = TileZoomAnimation()
    z.start_zoom_in(100, 80)

    # frame=0 → progress=0 → eased=0 → 通常位置
    pos0 = z.camera_pos
    assert abs(pos0[0] - z.NORMAL_X) < 1, f"start X: {pos0[0]}"
    assert abs(pos0[2] - z.NORMAL_Z) < 1, f"start Z: {pos0[2]}"

    # 全フレーム進める
    for _ in range(z.ZOOM_IN_DURATION):
        z.update()

    # 完了後 → ターゲット位置
    pos_end = z.camera_pos
    assert abs(pos_end[0] - 100) < 1, f"end X: {pos_end[0]}"
    assert abs(pos_end[2] - z.ZOOM_Z) < 1, f"end Z: {pos_end[2]}"


def test_zoom_out_start_and_end_positions():
    """ズームアウト: ターゲットから通常位置へ戻る"""
    z = TileZoomAnimation()
    z.start_zoom_in(100, 80)
    for _ in range(z.ZOOM_IN_DURATION):
        z.update()

    z.start_zoom_out()
    # frame=0 → progress=0 → eased=1.0 (1 - 0² = 1) → まだターゲット位置
    pos0 = z.camera_pos
    assert abs(pos0[0] - 100) < 1, f"out start X: {pos0[0]}"

    for _ in range(z.ZOOM_OUT_DURATION):
        z.update()

    # 完了後 → 通常位置に戻る
    pos_end = z.camera_pos
    assert abs(pos_end[0] - z.NORMAL_X) < 1, f"out end X: {pos_end[0]}"
    assert abs(pos_end[2] - z.NORMAL_Z) < 1, f"out end Z: {pos_end[2]}"


def test_zoom_in_z_monotonically_decreases():
    """ズームイン中、Zは単調減少する（カメラが接近）"""
    z = TileZoomAnimation()
    z.start_zoom_in(128, 128)
    prev_z = z.camera_pos[2]
    for _ in range(z.ZOOM_IN_DURATION):
        z.update()
        cur_z = z.camera_pos[2]
        assert cur_z <= prev_z, f"Z increased: {prev_z} -> {cur_z}"
        prev_z = cur_z


def test_zoom_out_z_monotonically_increases():
    """ズームアウト中、Zは単調増加する（カメラが離れる）"""
    z = TileZoomAnimation()
    z.start_zoom_in(128, 128)
    for _ in range(z.ZOOM_IN_DURATION):
        z.update()

    z.start_zoom_out()
    prev_z = z.camera_pos[2]
    for _ in range(z.ZOOM_OUT_DURATION):
        z.update()
        cur_z = z.camera_pos[2]
        assert cur_z >= prev_z, f"Z decreased: {prev_z} -> {cur_z}"
        prev_z = cur_z


def test_rotation_only_changes_x():
    """カメラ回転はX/Y軸が変化し、Zは常に0（rot_y=45→0に補間）"""
    z = TileZoomAnimation()
    z.start_zoom_in(50, 50)
    for _ in range(z.ZOOM_IN_DURATION + 5):
        rx, ry, rz = z.camera_rot
        assert rz == 0, f"Z rotation changed: rz={rz}"
        assert 0 <= ry <= z.NORMAL_RY, f"ry out of range: {ry}"
        assert z.ZOOM_RX <= rx <= z.NORMAL_RX, f"rx out of range: {rx}"
        z.update()


def test_camera_pos_no_nan_or_inf():
    """さまざまなターゲット座標でNaN/Infが出ないことを確認"""
    for tx, ty in [(0, 0), (128, 128), (255, 255), (50, 200), (200, 30)]:
        z = TileZoomAnimation()
        z.start_zoom_in(tx, ty)
        for _ in range(z.ZOOM_IN_DURATION + 5):
            pos = z.camera_pos
            rot = z.camera_rot
            for v in pos + rot:
                assert not math.isnan(v) and not math.isinf(v), \
                    f"NaN/Inf at target ({tx},{ty}): pos={pos}, rot={rot}"
            z.update()


def test_finish_zoom_resets_to_normal():
    """finish_zoom()後はデフォルト俯瞰に戻る"""
    z = TileZoomAnimation()
    z.start_zoom_in(100, 100)
    for _ in range(10):
        z.update()
    z.finish_zoom()

    assert not z.active
    assert z.camera_pos == (z.NORMAL_X, z.NORMAL_Y, z.NORMAL_Z)
    assert z.camera_rot == (z.NORMAL_RX, z.NORMAL_RY, 0)


def test_on_complete_callback_fires():
    """ズームイン完了時にコールバックが呼ばれる"""
    called = [False]

    def cb():
        called[0] = True

    z = TileZoomAnimation()
    z.start_zoom_in(128, 128, on_complete=cb)
    for _ in range(z.ZOOM_IN_DURATION):
        z.update()
    assert called[0], "on_complete not called"


def test_double_zoom_in_resets_animation():
    """ズームイン中に再度start_zoom_inを呼んでもクラッシュしない"""
    z = TileZoomAnimation()
    z.start_zoom_in(50, 50)
    for _ in range(5):
        z.update()

    # 途中で別のターゲットにズーム開始
    z.start_zoom_in(200, 200)
    assert z.active
    assert z.target_x == 200
    assert z.frame == 0  # リセットされている

    for _ in range(z.ZOOM_IN_DURATION):
        z.update()
    pos = z.camera_pos
    assert abs(pos[0] - 200) < 1


def test_zoom_out_without_zoom_in():
    """zoom_in無しでzoom_outを呼んでもクラッシュしない"""
    z = TileZoomAnimation()
    z.active = True  # 手動でアクティブに
    z.start_zoom_out()
    for _ in range(z.ZOOM_OUT_DURATION):
        z.update()
    # クラッシュしなければOK
    pos = z.camera_pos
    assert abs(pos[2] - z.NORMAL_Z) < 1


def test_eased_progress_range():
    """_eased_progressの値が[0, 1]の範囲内であること"""
    z = TileZoomAnimation()

    # ズームイン
    z.start_zoom_in(100, 100)
    for _ in range(z.ZOOM_IN_DURATION + 5):
        ep = z._eased_progress
        assert 0.0 <= ep <= 1.0, f"zoom_in eased_progress out of range: {ep}"
        z.update()

    # ズームアウト
    z.start_zoom_out()
    for _ in range(z.ZOOM_OUT_DURATION + 5):
        ep = z._eased_progress
        assert 0.0 <= ep <= 1.0, f"zoom_out eased_progress out of range: {ep}"
        z.update()


# ===========================================================================
# 2. tile_image_pos 座標境界テスト（Pyxel必要 — ヘッドレスでスキップ）
# ===========================================================================

def _can_import_pyxel():
    """Pyxel がインポートできるか（ヘッドレス環境では失敗する）"""
    try:
        import pyxel
        return True
    except Exception:
        return False


def test_tile_image_pos_bounds_topview():
    """TopView: 全タイルの座標が 0-255 の範囲内"""
    if not _can_import_pyxel():
        print("  SKIP (pyxel not available)")
        return

    from src.views.topview.board_view import TopViewBoardView
    board = _build_board()
    view = TopViewBoardView(board)

    for tile in board.tiles:
        x, y = view.tile_image_pos(tile.id)
        assert 0 <= x < 256 and 0 <= y < 256, \
            f"TopView tile {tile.id} out of bounds: ({x}, {y})"


def test_tile_image_pos_bounds_isometric():
    """Isometric: 全タイルの座標が 0-255 の範囲内"""
    if not _can_import_pyxel():
        print("  SKIP (pyxel not available)")
        return

    from src.views.isometric.board_view import IsometricBoardView
    board = _build_board()
    view = IsometricBoardView(board)

    for tile in board.tiles:
        x, y = view.tile_image_pos(tile.id)
        assert 0 <= x < 256 and 0 <= y < 256, \
            f"Isometric tile {tile.id} out of bounds: ({x}, {y})"


def test_tile_image_pos_distinct():
    """異なるタイルは（隣接タイルを除き）異なる座標を持つ"""
    if not _can_import_pyxel():
        print("  SKIP (pyxel not available)")
        return

    from src.views.topview.board_view import TopViewBoardView
    board = _build_board()
    view = TopViewBoardView(board)

    positions = {}
    for tile in board.tiles:
        pos = view.tile_image_pos(tile.id)
        # 同じグリッド座標のタイルは存在しないはず
        if pos in positions:
            other = positions[pos]
            t_other = board.get_tile(other)
            # grid座標が同じなら同じ位置は正しい
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
        test_default_camera_returns_normal_position,
        test_zoom_in_start_and_end_positions,
        test_zoom_out_start_and_end_positions,
        test_zoom_in_z_monotonically_decreases,
        test_zoom_out_z_monotonically_increases,
        test_rotation_only_changes_x,
        test_camera_pos_no_nan_or_inf,
        test_finish_zoom_resets_to_normal,
        test_on_complete_callback_fires,
        test_double_zoom_in_resets_animation,
        test_zoom_out_without_zoom_in,
        test_eased_progress_range,
        test_tile_image_pos_bounds_topview,
        test_tile_image_pos_bounds_isometric,
        test_tile_image_pos_distinct,
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
