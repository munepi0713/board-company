"""pyxel-mcp を使った画面遷移の自動テスト

各シーンのスクリーンショットを撮影し、正常に描画されることを検証する。
screenshots/ ディレクトリに代表画像を保存する。

Usage:
    python tests/test_screens.py
"""

import json
import os
import subprocess
import sys
import tempfile

# プロジェクトルート
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAIN_PY = os.path.join(ROOT, "main.py")
SCREENSHOTS_DIR = os.path.join(ROOT, "screenshots")
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)


def run_harness(frames, scale=2):
    """pyxel-mcp harness で指定フレームのスクリーンショットを撮る。"""
    out = os.path.join(SCREENSHOTS_DIR, "capture.png")
    cmd = [
        sys.executable, "-m", "pyxel_mcp.harness",
        MAIN_PY, out, str(frames), str(scale),
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=30, cwd=ROOT)
    if result.returncode != 0:
        stderr = result.stderr.decode(errors="replace")
        raise RuntimeError(f"harness failed (frame={frames}): {stderr}")
    if not os.path.exists(out):
        raise FileNotFoundError(f"Screenshot not created: {out}")
    return out


def run_input_harness(input_schedule, capture_frames, scale=2):
    """pyxel-mcp input_harness で入力をシミュレートしつつ複数フレームを撮影する。"""
    outdir = tempfile.mkdtemp(prefix="pyxel_test_")
    input_file = os.path.join(outdir, "input.json")
    with open(input_file, "w") as f:
        json.dump(input_schedule, f)

    capture_csv = ",".join(str(fr) for fr in capture_frames)
    cmd = [
        sys.executable, "-m", "pyxel_mcp.input_harness",
        MAIN_PY, outdir, capture_csv, str(scale), input_file,
    ]
    result = subprocess.run(cmd, capture_output=True, timeout=60, cwd=ROOT)
    if result.returncode != 0:
        stderr = result.stderr.decode(errors="replace")
        raise RuntimeError(f"input_harness failed: {stderr}")
    return outdir


def copy_screenshot(src, name):
    """スクリーンショットを screenshots/ に保存する。"""
    import shutil
    dst = os.path.join(SCREENSHOTS_DIR, name)
    shutil.copy2(src, dst)
    print(f"  Saved: {dst}")
    return dst


# ---------------------------------------------------------------------------
# テストケース
# ---------------------------------------------------------------------------

def test_title_screen():
    """タイトル画面の表示テスト。"""
    print("[TEST] Title Screen")
    out = run_harness(frames=1, scale=2)
    copy_screenshot(out, "01_title.png")
    assert os.path.getsize(os.path.join(SCREENSHOTS_DIR, "01_title.png")) > 1000
    print("  PASS")


def test_setup_screen():
    """セットアップ画面への遷移テスト。"""
    print("[TEST] Setup Screen")
    schedule = [
        {"frame": 3, "keys": ["KEY_RETURN"]},
        {"frame": 4, "keys": []},
    ]
    outdir = run_input_harness(schedule, capture_frames=[8])
    src = os.path.join(outdir, "frame_0008.png")
    assert os.path.exists(src), "Setup screen not captured"
    copy_screenshot(src, "02_setup.png")
    print("  PASS")


def test_main_board_screen():
    """メインボード画面への遷移テスト。"""
    print("[TEST] Main Board Screen")
    schedule = [
        {"frame": 3, "keys": ["KEY_RETURN"]},   # タイトル → セットアップ
        {"frame": 4, "keys": []},
        {"frame": 8, "keys": ["KEY_DOWN"]},      # カーソルを下へ
        {"frame": 9, "keys": []},
        {"frame": 12, "keys": ["KEY_DOWN"]},
        {"frame": 13, "keys": []},
        {"frame": 16, "keys": ["KEY_DOWN"]},      # OKボタンへ
        {"frame": 17, "keys": []},
        {"frame": 20, "keys": ["KEY_RETURN"]},    # ゲーム開始
        {"frame": 21, "keys": []},
    ]
    outdir = run_input_harness(schedule, capture_frames=[30])
    src = os.path.join(outdir, "frame_0030.png")
    assert os.path.exists(src), "Main board not captured"
    copy_screenshot(src, "03_main_board.png")
    print("  PASS")


def test_dice_animation():
    """サイコロ演出のテスト。"""
    print("[TEST] Dice Animation")
    schedule = [
        {"frame": 3, "keys": ["KEY_RETURN"]},
        {"frame": 4, "keys": []},
        {"frame": 8, "keys": ["KEY_DOWN"]},
        {"frame": 9, "keys": []},
        {"frame": 12, "keys": ["KEY_DOWN"]},
        {"frame": 13, "keys": []},
        {"frame": 16, "keys": ["KEY_DOWN"]},
        {"frame": 17, "keys": []},
        {"frame": 20, "keys": ["KEY_RETURN"]},    # ゲーム開始
        {"frame": 21, "keys": []},
        {"frame": 30, "keys": ["KEY_RETURN"]},    # サイコロを振る
        {"frame": 31, "keys": []},
    ]
    outdir = run_input_harness(schedule, capture_frames=[38])
    src = os.path.join(outdir, "frame_0038.png")
    assert os.path.exists(src), "Dice animation not captured"
    copy_screenshot(src, "04_dice.png")
    print("  PASS")


def test_gameplay_progression():
    """ゲーム進行（数ターン）のテスト。"""
    print("[TEST] Gameplay Progression")
    schedule = [
        {"frame": 3, "keys": ["KEY_RETURN"]},
        {"frame": 4, "keys": []},
        {"frame": 8, "keys": ["KEY_DOWN"]},
        {"frame": 9, "keys": []},
        {"frame": 12, "keys": ["KEY_DOWN"]},
        {"frame": 13, "keys": []},
        {"frame": 16, "keys": ["KEY_DOWN"]},
        {"frame": 17, "keys": []},
        {"frame": 20, "keys": ["KEY_RETURN"]},
        {"frame": 21, "keys": []},
    ]
    # ENTERを繰り返して進行
    frame = 30
    for _ in range(20):
        schedule.append({"frame": frame, "keys": ["KEY_RETURN"]})
        schedule.append({"frame": frame + 1, "keys": []})
        frame += 10

    outdir = run_input_harness(schedule, capture_frames=[100, 180])
    # 少なくとも1枚はキャプチャされていること
    files = [f for f in os.listdir(outdir) if f.endswith(".png")]
    assert len(files) > 0, "No gameplay frames captured"
    # 最初のキャプチャを保存
    files.sort()
    copy_screenshot(os.path.join(outdir, files[0]), "05_gameplay.png")
    print(f"  PASS ({len(files)} frames captured)")


# ---------------------------------------------------------------------------
# メイン
# ---------------------------------------------------------------------------

def main():
    print("=" * 50)
    print("BOARD COMPANY - Screen Tests (pyxel-mcp)")
    print("=" * 50)

    tests = [
        test_title_screen,
        test_setup_screen,
        test_main_board_screen,
        test_dice_animation,
        test_gameplay_progression,
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  FAIL: {e}")
            failed += 1

    print("=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    print(f"Screenshots saved to: {SCREENSHOTS_DIR}/")
    print("=" * 50)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
