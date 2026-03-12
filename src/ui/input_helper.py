"""ゲームパッド対応の入力ヘルパー

キーボードとゲームパッド（GAMEPAD1）の入力を統合する。
スマホブラウザでは Pyxel の仮想ゲームパッドが表示されるため、
ゲームパッドボタンに対応することでタッチ操作が可能になる。
"""
import pyxel

# キーボード → ゲームパッドのマッピング
_KEY_TO_GAMEPAD = {
    pyxel.KEY_UP: pyxel.GAMEPAD1_BUTTON_DPAD_UP,
    pyxel.KEY_DOWN: pyxel.GAMEPAD1_BUTTON_DPAD_DOWN,
    pyxel.KEY_LEFT: pyxel.GAMEPAD1_BUTTON_DPAD_LEFT,
    pyxel.KEY_RIGHT: pyxel.GAMEPAD1_BUTTON_DPAD_RIGHT,
    pyxel.KEY_RETURN: pyxel.GAMEPAD1_BUTTON_A,
    pyxel.KEY_Z: pyxel.GAMEPAD1_BUTTON_A,
    pyxel.KEY_SPACE: pyxel.GAMEPAD1_BUTTON_A,
    pyxel.KEY_X: pyxel.GAMEPAD1_BUTTON_B,
    pyxel.KEY_ESCAPE: pyxel.GAMEPAD1_BUTTON_B,
    pyxel.KEY_TAB: pyxel.GAMEPAD1_BUTTON_Y,
}


def btnp(key):
    """キーボードまたはゲームパッドのボタンが押された瞬間を検出"""
    if pyxel.btnp(key):
        return True
    gp = _KEY_TO_GAMEPAD.get(key)
    if gp is not None:
        return pyxel.btnp(gp)
    return False


def btn(key):
    """キーボードまたはゲームパッドのボタンが押されているかを検出"""
    if pyxel.btn(key):
        return True
    gp = _KEY_TO_GAMEPAD.get(key)
    if gp is not None:
        return pyxel.btn(gp)
    return False
