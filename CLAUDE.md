# CLAUDE.md — AI アシスタント向けプロジェクトガイド

## 最初に読むドキュメント

このプロジェクトに取りかかる前に、以下のドキュメントを順に読んでください。

1. **[docs/11_プロジェクト構成.md](docs/11_プロジェクト構成.md)** — ディレクトリ構造、ファイル一覧、アーキテクチャ図、依存関係ルール
2. **[docs/10_技術設計.md](docs/10_技術設計.md)** — 疎結合設計の方針、core/ と views/ の分離原則
3. **[docs/01_ゲーム概要.md](docs/01_ゲーム概要.md)** — ゲームルール・勝利条件・基本仕様

変更対象の機能に応じて、関連する仕様書（docs/02〜09）も参照してください。

## プロジェクト概要

Pyxel 2.x で動作するレトロスタイルのボードゲーム（会社経営シミュレーション）。
Python 3.9+、256x256px / 16色 / 30FPS。外部アセット（.pyxres）は使わず全てプロシージャル描画。

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
```

## MCP サーバー

`.mcp.json` に pyxel-mcp の設定がある。pyxel-mcp を使うと:

- ヘッドレスでゲームを実行しスクリーンショットを撮影できる
- キー入力をシミュレートしてゲーム進行を自動テストできる
- スプライト、タイルマップ、画面レイアウトを検査できる

動作確認時は `python tests/test_screens.py` を実行して全テスト通過を確認すること。

## コード変更時の注意

- ソースを変更したら `pyxel package . main.py` で `.pyxapp` を再ビルドする
- ブラウザ実行は `.pyxapp` 経由（`?play=` コマンド）。`?run=` ではマルチファイル import が動かない
- `tests/test_screens.py` を実行してスクリーンショットが正常に生成されることを確認する
- スクリーンショットが更新された場合は `screenshots/` もコミットに含める
