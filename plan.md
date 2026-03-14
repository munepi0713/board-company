# アイソメトリックビュー追加 — 実装計画

## 要件の整理

### やること
1. **解像度を 512x512 に変更** — 全画面・UIをスケール対応
2. **アイソメトリックビューの新規実装** — `src/views/isometric/` 配下
3. **ビュー切り替え機能** — ゲーム中にトップビュー⇔アイソメトリックを切り替え可能に
4. **既存トップビューの維持** — 現在の `topview/` は変更最小限

### やらないこと
- ゲームロジック（`core/`）の変更
- JSONデータの変更
- 新しい外部アセットの導入（引き続きプロシージャル描画）

---

## 影響分析

### 解像度変更 (256→512) の影響範囲
- `src/core/rules.py` — `SCREEN_WIDTH`, `SCREEN_HEIGHT` の値変更
- `main.py` — `pyxel.init()` に渡す値（rules.py 経由なので自動追従）
- `src/ui/hud.py` — `SCREEN_WIDTH` 使用（自動追従）
- `src/ui/dialog.py` — `SCREEN_WIDTH`, `SCREEN_HEIGHT` 使用（自動追従）
- `src/scenes/title.py` — センタリング計算に `SCREEN_WIDTH` 使用（自動追従だが座標調整要）
- `src/scenes/setup.py` — 同上
- `src/scenes/battle_scene.py` — 同上
- `src/scenes/ending.py` — 同上
- `src/scenes/news.py` — 同上
- `src/scenes/management.py` — 同上
- `src/scenes/main_board.py` — ボード描画座標、HUD位置（要調整）

**注意:** 大半のUIは `SCREEN_WIDTH/SCREEN_HEIGHT` を参照しているため定数変更で追従するが、ハードコードされた座標（y=196, y=244 等）は512に合わせて調整が必要。

---

## 実装ステップ

### Step 1: 解像度定数の変更と UI 座標調整
**対象ファイル:**
- `src/core/rules.py` — `SCREEN_WIDTH=512`, `SCREEN_HEIGHT=512`, `TILE_SIZE=32`（2倍）
- `src/scenes/main_board.py` — HUD表示座標の調整（y=196→y=440, y=244→y=496 等）
- `src/scenes/title.py` — メニュー位置、装飾位置の調整
- `src/scenes/setup.py` — レイアウト調整
- `src/scenes/battle_scene.py` — レイアウト調整
- `src/scenes/ending.py` — レイアウト調整
- `src/scenes/news.py` — レイアウト調整
- `src/scenes/management.py` — レイアウト調整
- `src/views/topview/board_view.py` — offset, spacing を512px用に調整
- `src/views/topview/player_view.py` — プレイヤースプライトサイズ調整

### Step 2: ビュー切り替え基盤の構築
**対象ファイル:**
- `src/views/view_base.py` — `ViewManager` クラスの追加（ビュー切り替えを管理）
- `src/views/__init__.py` — ファクトリ関数 `create_views(view_type, board_model)` の追加

**ViewManager の設計:**
```python
class ViewManager:
    """ビューの切り替えを管理"""
    def __init__(self, board_model):
        self.board_model = board_model
        self.view_type = "topview"  # "topview" | "isometric"
        self._board_views = {
            "topview": TopViewBoardView(board_model),
            "isometric": IsometricBoardView(board_model),
        }
        self._player_views = {
            "topview": TopViewPlayerView(),
            "isometric": IsometricPlayerView(),
        }

    @property
    def board_view(self): return self._board_views[self.view_type]

    @property
    def player_view(self): return self._player_views[self.view_type]

    def toggle_view(self):
        self.view_type = "isometric" if self.view_type == "topview" else "topview"
```

### Step 3: アイソメトリックビューの実装
**新規ファイル:**
- `src/views/isometric/board_view.py` — `IsometricBoardView(BoardViewBase)`
- `src/views/isometric/player_view.py` — `IsometricPlayerView(PlayerViewBase)`
- `src/views/isometric/__init__.py` — エクスポート

**アイソメトリック座標変換:**
```
screen_x = origin_x + (grid_x - grid_y) * tile_width_half
screen_y = origin_y + (grid_x + grid_y) * tile_height_half
```

**描画内容:**
- **タイル:** ひし形（ダイヤモンド型）のタイル。タイプごとに色分け（既存の色スキーム踏襲）
- **道路:** タイル中心間をアイソメトリック座標で接続線描画
- **建物:** タイル上に立体的な建物アイコン（直方体をプロシージャル描画）
- **プレイヤー:** アイソメトリック座標上にキャラクター描画。奥行き順（Y座標ソート）で描画

**タイルサイズ（アイソメトリック）:**
- `ISO_TILE_W = 48` （横幅）
- `ISO_TILE_H = 24` （高さ = 横幅の半分）
- マップ原点: `(256, 80)` — 画面上部中央から展開

### Step 4: MainBoardScene へのビュー切り替え統合
**対象ファイル:**
- `src/scenes/main_board.py`:
  - `board_view` / `player_view` を `ViewManager` に置き換え
  - Vキーでビュー切り替え（`view_manager.toggle_view()`）
  - カメラ位置をビューごとに管理

### Step 5: テスト・ビルド
- `python tests/test_screens.py` でスクリーンショットテスト
- `pyxel package . main.py` で `.pyxapp` 再ビルド
- `pyxel app2html board-company.pyxapp` で HTML 更新

---

## 技術的な考慮事項

### アイソメトリック描画の描画順序
- アイソメトリックでは **奥から手前の順** に描画が必要（Painter's Algorithm）
- `grid_x + grid_y` の値が小さいタイルを先に描画
- プレイヤーも同様のソート

### カメラ制御
- 512x512 画面に対してアイソメトリックマップは横に広がるため、カメラのパン機能が必要になる場合がある
- マップの grid 範囲は x:0-7, y:0-7 なので、`ISO_TILE_W=48` の場合の全体幅は約 `(7+7)*24 + 48 = 384px` — 512px に収まるため当初はカメラ固定で可

### Pyxel の制約
- Pyxel 2.x は 16 色パレット固定 — 影やハイライトは既存パレットの暗い/明るい色で対応
- `pyxel.tri()` でひし形タイルの上面を描画
- `pyxel.line()` / `pyxel.rect()` で立体部分を描画

---

## ファイル変更一覧

| ファイル | 変更内容 |
|---|---|
| `src/core/rules.py` | SCREEN_WIDTH=512, SCREEN_HEIGHT=512, TILE_SIZE 調整 |
| `src/views/view_base.py` | ViewManager クラス追加 |
| `src/views/__init__.py` | ファクトリ関数追加 |
| `src/views/topview/board_view.py` | offset/spacing 調整 |
| `src/views/topview/player_view.py` | スプライトサイズ調整 |
| `src/views/isometric/__init__.py` | エクスポート |
| `src/views/isometric/board_view.py` | **新規** アイソメトリックボード描画 |
| `src/views/isometric/player_view.py` | **新規** アイソメトリックプレイヤー描画 |
| `src/scenes/main_board.py` | ViewManager統合、Vキー切り替え、座標調整 |
| `src/scenes/title.py` | レイアウト座標調整 |
| `src/scenes/setup.py` | レイアウト座標調整 |
| `src/scenes/battle_scene.py` | レイアウト座標調整 |
| `src/scenes/ending.py` | レイアウト座標調整 |
| `src/scenes/news.py` | レイアウト座標調整 |
| `src/scenes/management.py` | レイアウト座標調整 |
