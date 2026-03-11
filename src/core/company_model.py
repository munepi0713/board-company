"""会社データ・経営ロジック"""
from dataclasses import dataclass
from src.core.rules import (
    EDUCATION_COST_PER_EMPLOYEE, EDUCATION_ABILITY_GAIN,
    ADVERTISING_COST, ADVERTISING_FAME_GAIN,
    HIRE_COST_PER_PERSON, ABILITY_MAX, FAME_MAX,
    ABILITY_MIN, FAME_MIN, ABILITY_DECAY, FAME_DECAY,
    COMPANY_FEE_RATE, SELL_RATE,
)


@dataclass
class CompanyType:
    type_id: str
    name: str
    construction_cost: int
    initial_employees: int
    initial_revenue: int


@dataclass
class Company:
    name: str
    company_type: str
    owner_id: int
    tile_id: int
    employees: int
    ability: int = 50
    fame: int = 50
    construction_cost: int = 0
    base_revenue: int = 0

    @property
    def fixed_revenue(self) -> int:
        return (self.fame + self.ability) // 10 + self.employees // 10

    @property
    def evaluation(self) -> int:
        return self.construction_cost + (self.fixed_revenue * 5)

    @property
    def fee(self) -> int:
        """会社使用料"""
        return int(self.fixed_revenue * COMPANY_FEE_RATE)

    @property
    def sell_price(self) -> int:
        return int(self.evaluation * SELL_RATE)

    def apply_decay(self):
        """偶数ターンの能力・知名度減衰"""
        self.ability = max(ABILITY_MIN, self.ability - ABILITY_DECAY)
        self.fame = max(FAME_MIN, self.fame - FAME_DECAY)

    def educate(self):
        """社員教育。能力を上昇させる"""
        self.ability = min(ABILITY_MAX, self.ability + EDUCATION_ABILITY_GAIN)

    def advertise(self):
        """宣伝。知名度を上昇させる"""
        self.fame = min(FAME_MAX, self.fame + ADVERTISING_FAME_GAIN)

    def hire(self, count: int) -> int:
        """採用。コストを返す"""
        cost = count * HIRE_COST_PER_PERSON
        self.employees += count
        return cost

    def fire(self, count: int):
        """解雇"""
        self.employees = max(0, self.employees - count)

    def merge_with(self, other: "Company"):
        """吸収合併"""
        self.employees += other.employees
        self.base_revenue += other.base_revenue
        self.construction_cost += other.construction_cost // 2
        self.ability = (self.ability + other.ability) // 2
        self.fame = (self.fame + other.fame) // 2
