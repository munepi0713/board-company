"""JSONデータ読み込み"""
import json
import os

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")


def load_json(filename: str) -> dict:
    filepath = os.path.join(DATA_DIR, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def load_map_data(filename: str = "map_default.json"):
    """マップデータを読み込む"""
    from src.core.board_model import Tile, BoardModel

    data = load_json(filename)
    tiles = []
    for t in data["tiles"]:
        tile = Tile(
            id=t["id"],
            tile_type=t["type"],
            name=t["name"],
            next_tiles=t["next"],
            grid_x=t["position"]["x"],
            grid_y=t["position"]["y"],
            land_price=t.get("land_price", 0),
            plus_minus_amount=t.get("plus_minus_amount", 0),
        )
        tiles.append(tile)
    board = BoardModel(tiles)
    goal = data.get("goal_assets", 10000)
    return board, goal


def load_company_types():
    """会社種類データを読み込む"""
    return load_json("companies.json")


def load_characters():
    """キャラクターデータを読み込む"""
    return load_json("characters.json")
