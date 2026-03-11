"""ボードマップデータ・経路探索"""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Tile:
    id: int
    tile_type: str  # normal, card_shop, plus, minus, card
    name: str
    next_tiles: list = field(default_factory=list)
    grid_x: int = 0
    grid_y: int = 0
    land_price: int = 0
    land_owner_id: Optional[int] = None
    company: Optional[object] = None  # Company instance
    plus_minus_amount: int = 0

    @property
    def is_owned(self) -> bool:
        return self.land_owner_id is not None

    @property
    def has_company(self) -> bool:
        return self.company is not None


class BoardModel:
    """ボードの論理構造を管理する。描画には関与しない。"""

    def __init__(self, tiles: list):
        self.tiles = tiles
        self._tile_map = {t.id: t for t in tiles}

    def get_tile(self, tile_id: int) -> Tile:
        return self._tile_map[tile_id]

    def get_next_tiles(self, tile_id: int) -> list:
        """指定マスから進める次のマスIDリストを返す"""
        return self.get_tile(tile_id).next_tiles

    def has_branch(self, tile_id: int) -> bool:
        """分岐があるか判定"""
        return len(self.get_next_tiles(tile_id)) > 1

    def get_all_normal_tiles(self) -> list:
        """全ての通常マスを返す"""
        return [t for t in self.tiles if t.tile_type == "normal"]

    def get_random_tile_id(self) -> int:
        """ランダムなマスIDを返す"""
        import random
        return random.choice(self.tiles).id
