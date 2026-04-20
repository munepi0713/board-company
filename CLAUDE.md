# CLAUDE.md — AI アシスタント向けプロジェクトガイド

## 最初に読むドキュメント

このプロジェクトに取りかかる前に、以下のドキュメントを順に読んでください。

1. **[docs/11_プロジェクト構成.md](docs/11_プロジェクト構成.md)** — ディレクトリ構造、ファイル一覧、アーキテクチャ図、依存関係ルール
2. **[docs/10_技術設計.md](docs/10_技術設計.md)** — 疎結合設計の方針、core/ と views/ の分離原則
3. **[docs/01_ゲーム概要.md](docs/01_ゲーム概要.md)** — ゲームルール・勝利条件・基本仕様

変更対象の機能に応じて、関連する仕様書（docs/02〜09）も参照してください。

## プロジェクト概要

Pyxel 2.x で動作するレトロスタイルのボードゲーム（会社経営シミュレーション）。
Python 3.9+、256x256px / 16色 / 30FPS。`.pyxres`（スプライト・タイルマップ等のリソースファイル）は必要に応じて使用する。

## アーキテクチャ上の重要ルール

- **`src/core/` は Pyxel に依存しない。** `import pyxel` を core/ 配下に追加しないこと。
- **`src/views/` は差し替え可能。** BoardViewBase / PlayerViewBase の抽象クラスを実装する形で描画を行う。
- **データは JSON 駆動。** ゲームバランスの変更は `data/*.json` で行い、コードに直書きしない。
- **定数は `src/core/rules.py` に集約。** マジックナンバーを散在させない。

## 開発コマンド

```bash
# 依存インストール
pip install -r requirements.txt

# ゲーム起動（ローカル）
python main.py

# 自動テスト（pyxel-mcp が必要）
pip install pyxel-mcp
python tests/test_screens.py

# .pyxapp ビルド（ソース変更後は必ず再ビルド）
pyxel package . main.py

# Web 版 HTML の更新（.pyxapp 再ビルド後に実行）
pyxel app2html board-company.pyxapp
```

## MCP サーバー

`.mcp.json` に pyxel-mcp の設定がある。pyxel-mcp を使うと:

- ヘッドレスでゲームを実行しスクリーンショットを撮影できる
- キー入力をシミュレートしてゲーム進行を自動テストできる
- スプライト、タイルマップ、画面レイアウトを検査できる

動作確認時は `python tests/test_screens.py` を実行して全テスト通過を確認すること。

## テスト

```bash
# 画面遷移テスト（pyxel-mcp 必要、スクリーンショット自動生成）
python tests/test_screens.py

# ズーム機能ユニットテスト（Pyxel不要、ヘッドレス実行可）
python tests/test_zoom.py
```

- `test_screens.py` — pyxel-mcp を使った7つの画面遷移・描画テスト
- `test_zoom.py` — TileZoomAnimation の15項目のユニットテスト（scale/offset 補間、イージング、状態遷移、tile_image_pos 座標境界）

## 描画パイプライン（オフスクリーン → scale 付き blt）

メインボードの描画は **オフスクリーン描画 → `pyxel.blt` scale 拡大転送** の統一パイプライン。ビュー種別（isometric / topview）とズーム有無を問わず同一コードパスで描画する。

### パイプライン概要

```
BoardView.draw_board_to_image(img)   ← 256x208 領域に描画（img bank 2）
         ↓
TileZoomAnimation.scale / offset     ← 常時提供（通常時=BASE_SCALE, ズーム時=ZOOM_SCALE へ補間）
         ↓
pyxel.blt(offset_x, offset_y, 2, 0, 0, IMG_W, IMG_H, scale=scale)
```

### TileZoomAnimation の定数

| パラメータ | 値 | 説明 |
|---|---|---|
| `BASE_SCALE` | 2.0 | 通常時のピクセル等倍拡大（256→512） |
| `ZOOM_SCALE` | 4.0 | ズーム時の拡大倍率 |
| `BASE_OFFSET_X, BASE_OFFSET_Y` | 0, 16 | 通常時の描画左上（HUD の下） |
| `FOCUS_X, FOCUS_Y` | 256, 240 | ズーム時のターゲット画像座標をここへ寄せる |
| `ZOOM_IN_DURATION / ZOOM_OUT_DURATION` | 20 / 15 | フレーム数 |
| `FOLLOW_FACTOR` | 0.25 | 視線追従による平行移動係数 |

### ビュー別のタイルサイズ

| ビュー | タイル | 備考 |
|---|---|---|
| Isometric | `TILE_W=32, TILE_H=16, TILE_DEPTH=3` | ダイヤモンド 2:1、上面 + 南/東側面で立体感 |
| TopView | `CELL_W=22, CELL_H=22, GAP=2` | デバッグ用のフラット表示 |

### イメージバンク使用状況

| バンク | 用途 |
|---|---|
| 0 | フォント（BDFフォント描画用） |
| 1 | （予備） |
| 2 | **ボードオフスクリーン描画** ← `pyxel.blt` 転送元（使用領域 256x208） |

### 関連ファイル

| ファイル | 役割 |
|---|---|
| `src/ui/animation.py` → `TileZoomAnimation` | scale/offset の補間、視線追従 |
| `src/views/view_base.py` → `ViewManager` | Isometric / TopView の切り替え |
| `src/views/isometric/board_view.py` | ダイヤモンド投影でのオフスクリーン描画 |
| `src/views/isometric/sprites.py` | 建物・プレイヤーの 2D スプライト関数 |
| `src/views/topview/board_view.py` | フラット俯瞰（デバッグ用） |
| `src/scenes/main_board.py` | 統一描画パイプライン、ズーム状態遷移 |

### ダイヤモンド投影（Isometric）

```
grid (gx, gy) → image (BOARD_CX + (gx - gy) * TILE_W/2,
                        BOARD_CY + (gx + gy) * TILE_H/2)
```

描画は奥（`gx+gy` 小）→手前（大）の順。同一タイル内は タイル→建物→プレイヤー の順。

### main_board.py のズーム状態遷移

```
移動完了 → TILE_ZOOM_IN（20F）→ マスアクション実行 → TILE_ZOOM_OUT（15F）→ 次のプレイヤーへ
```

SubPhase: `TILE_ZOOM_IN`, `TILE_ZOOM_OUT` が追加されている。

## 入力操作ルール

- **キーボード入力は必ず `src/ui/input_helper.py` の `btnp()` / `btn()` を使う。** `pyxel.btnp()` や `pyxel.btn()` を直接呼ばないこと。
- `input_helper` はキーボードとゲームパッド（GAMEPAD1）の入力を統合している。スマホブラウザでは Pyxel の仮想ゲームパッドが表示されるため、この統合レイヤーを使うことでタッチ操作にも対応できる。
- 新しいキー → ゲームパッドのマッピングが必要な場合は `_KEY_TO_GAMEPAD` に追加する。

## コード変更時の注意

- ソースを変更したら `pyxel package . main.py` で `.pyxapp` を再ビルドする
- `.pyxapp` 再ビルド後は `pyxel app2html board-company.pyxapp` で Web 版 HTML も更新する
- ブラウザ実行は GitHub Pages 経由で `board-company.html` を配信（`pyxel app2html` で生成した自己完結型 HTML）
- `tests/test_screens.py` を実行してスクリーンショットが正常に生成されることを確認する
- スクリーンショットが更新された場合は `screenshots/` もコミットに含める
