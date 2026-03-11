"""BOARD COMPANY - エントリーポイント（python -m src.main 用）"""
import os
import sys

# プロジェクトルートをパスに追加（python -m src.main でも動くように）
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

# ルートの main.py に委譲
exec(open(os.path.join(_project_root, "main.py")).read())
