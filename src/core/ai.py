"""CPU AI 意思決定"""
import random
from src.core.card_logic import get_normal_cards, get_battle_cards


class AIPlayer:
    """CPU AIの意思決定を行うクラス"""

    def __init__(self, ai_params: dict):
        self.aggression = ai_params.get("aggression", 50)
        self.investment_tendency = ai_params.get("investment_tendency", 50)
        self.card_usage = ai_params.get("card_usage", 50)
        self.flee_tendency = ai_params.get("flee_tendency", 30)
        self.preferred_cost_min = ai_params.get("preferred_company_cost", {}).get("min", 300)
        self.preferred_cost_max = ai_params.get("preferred_company_cost", {}).get("max", 1500)
        self.education_priority = ai_params.get("education_priority", 50)
        self.advertising_priority = ai_params.get("advertising_priority", 50)

    def choose_command(self, player, game_state) -> str:
        """ターン開始時のコマンド選択: 'dice', 'card'"""
        if player.is_slowed:
            return "dice"
        normal_cards = get_normal_cards(player.cards)
        if normal_cards and random.randint(0, 100) < self.card_usage:
            return "card"
        return "dice"

    def choose_card_to_use(self, player) -> int:
        """使用するカードのインデックスを返す"""
        normal_cards = get_normal_cards(player.cards)
        if normal_cards:
            card = random.choice(normal_cards)
            return player.cards.index(card)
        return -1

    def choose_branch(self, branches: list) -> int:
        """分岐の選択"""
        return random.randint(0, len(branches) - 1)

    def should_buy_land(self, player, tile, game_state) -> bool:
        """土地を購入するか"""
        if player.money < tile.land_price:
            return False
        if random.randint(0, 100) < self.investment_tendency:
            return True
        return player.money > tile.land_price * 3

    def should_build_company(self, player, available_types) -> str:
        """会社を建設するか、建設する場合は種類IDを返す"""
        affordable = [
            ct for ct in available_types
            if ct["construction_cost"] <= player.money
            and self.preferred_cost_min <= ct["construction_cost"] <= self.preferred_cost_max
        ]
        if not affordable:
            affordable = [
                ct for ct in available_types
                if ct["construction_cost"] <= player.money
            ]
        if affordable and random.randint(0, 100) < self.investment_tendency:
            return random.choice(affordable)["type_id"]
        return None

    def choose_management_action(self, player, company) -> str:
        """経営コマンドを選択: 'educate', 'advertise', 'hire', 'none'"""
        actions = []
        edu_cost = company.employees * 15
        if player.money >= edu_cost and random.randint(0, 100) < self.education_priority:
            actions.append("educate")
        if player.money >= 200 and random.randint(0, 100) < self.advertising_priority:
            actions.append("advertise")
        if player.money >= 150 and random.randint(0, 100) < self.investment_tendency // 2:
            actions.append("hire")
        if actions:
            return random.choice(actions)
        return "none"

    def choose_battle_action(self, player, battle_state, is_attacker: bool) -> str:
        """戦闘コマンド: 'attack', 'defend', 'card', 'flee'"""
        stats = battle_state.attacker_stats if is_attacker else battle_state.defender_stats
        other = battle_state.defender_stats if is_attacker else battle_state.attacker_stats

        battle_cards = get_battle_cards(player.cards)
        if battle_cards and random.randint(0, 100) < self.card_usage:
            return "card"

        if random.randint(0, 100) < self.flee_tendency and stats.hp < other.hp:
            return "flee"

        if stats.hp < stats.max_hp // 4:
            return "defend"

        if random.randint(0, 100) < self.aggression:
            return "attack"

        return random.choice(["attack", "defend"])

    def should_buyout_land(self, player, tile) -> bool:
        """土地を買い取るか"""
        cost = tile.land_price * 5
        return player.money >= cost and random.randint(0, 100) < self.investment_tendency // 2

    def should_buyout_company(self, player, company) -> bool:
        """会社を買収するか"""
        cost = company.evaluation * 4
        return player.money >= cost and random.randint(0, 100) < self.aggression // 2
