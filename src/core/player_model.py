"""プレイヤーデータ・操作ロジック"""
from dataclasses import dataclass, field
from typing import Optional
from src.core.rules import INITIAL_MONEY, MAX_CARDS


@dataclass
class PlayerStats:
    total_revenue: int = 0
    total_land_income: int = 0
    total_company_income: int = 0
    battles_won: int = 0
    battles_lost: int = 0
    tiles_moved: int = 0


@dataclass
class Player:
    id: int
    name: str
    character_id: int
    is_human: bool
    money: int = INITIAL_MONEY
    position: int = 0
    cards: list = field(default_factory=list)
    owned_land_ids: list = field(default_factory=list)
    owned_company_ids: list = field(default_factory=list)
    is_bankrupt: bool = False
    slow_debuff_turns: int = 0
    remaining_moves: int = 0
    stats: PlayerStats = field(default_factory=PlayerStats)
    color: int = 8  # Pyxel color index for this player

    @property
    def total_assets(self) -> int:
        """総資産（会社・土地の評価額は外部から計算する必要あり）"""
        return self.money

    @property
    def card_count(self) -> int:
        return len(self.cards)

    @property
    def can_hold_card(self) -> bool:
        return self.card_count < MAX_CARDS

    @property
    def is_slowed(self) -> bool:
        return self.slow_debuff_turns > 0

    def add_money(self, amount: int):
        self.money += amount

    def pay(self, amount: int) -> bool:
        """支払い。成功したらTrue"""
        if self.money >= amount:
            self.money -= amount
            return True
        return False

    def add_card(self, card) -> bool:
        if self.can_hold_card:
            self.cards.append(card)
            return True
        return False

    def remove_card(self, card_index: int):
        if 0 <= card_index < len(self.cards):
            return self.cards.pop(card_index)
        return None

    def tick_slow_debuff(self):
        if self.slow_debuff_turns > 0:
            self.slow_debuff_turns -= 1
