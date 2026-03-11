"""戦闘ルール・ダメージ計算"""
import random
from dataclasses import dataclass, field
from src.core.rules import (
    DAMAGE_RANDOM_RANGE, DEFENSE_MULTIPLIER, MIN_DAMAGE,
    FLEE_DIVISOR, FLEE_PENALTY_RATE,
)


@dataclass
class BattleStats:
    hp: int = 0
    max_hp: int = 0
    attack: int = 0
    defense: int = 0
    speed: int = 0
    # バフ・デバフ
    attack_multiplier: float = 1.0
    defense_multiplier: float = 1.0
    speed_multiplier: float = 1.0
    is_defending: bool = False
    # カードバフ残りターン
    buffs: list = field(default_factory=list)


@dataclass
class BattleBuff:
    name: str
    stat: str  # attack, defense, speed
    multiplier: float
    remaining_turns: int
    target_self: bool = True


class BattleState:
    def __init__(self, attacker_player, defender_player, board):
        self.attacker = attacker_player
        self.defender = defender_player
        self.board = board
        self.attacker_stats = self._calc_battle_stats(attacker_player)
        self.defender_stats = self._calc_battle_stats(defender_player)
        self.turn = 0
        self.is_attacker_turn = True
        self.finished = False
        self.winner = None
        self.loser = None
        self.fled = False
        self.messages = []

    def _calc_battle_stats(self, player) -> BattleStats:
        total_employees = 0
        total_eval = 0
        abilities = []
        fames = []
        for tile in self.board.tiles:
            if tile.company and tile.company.owner_id == player.id:
                total_employees += tile.company.employees
                total_eval += tile.company.evaluation
                abilities.append(tile.company.ability)
                fames.append(tile.company.fame)
        avg_ability = sum(abilities) // len(abilities) if abilities else 50
        avg_fame = sum(fames) // len(fames) if fames else 50
        hp = max(total_employees, 1)
        attack = total_employees + total_eval // 10
        return BattleStats(
            hp=hp, max_hp=hp,
            attack=max(attack, 1),
            defense=avg_ability,
            speed=avg_fame,
        )

    def determine_turn_order(self):
        """行動順を決定"""
        atk_roll = random.randint(0, 100)
        def_roll = random.randint(0, 100)
        atk_speed = int(self.attacker_stats.speed * self.attacker_stats.speed_multiplier)
        def_speed = int(self.defender_stats.speed * self.defender_stats.speed_multiplier)
        self.is_attacker_turn = (atk_roll < atk_speed) or (atk_roll >= def_roll)

    def execute_attack(self, actor_stats: BattleStats, target_stats: BattleStats) -> int:
        """攻撃を実行しダメージを返す"""
        atk = actor_stats.attack * actor_stats.attack_multiplier
        spd = actor_stats.speed * actor_stats.speed_multiplier
        t_def = target_stats.defense * target_stats.defense_multiplier
        if target_stats.is_defending:
            t_def *= DEFENSE_MULTIPLIER
        t_spd = target_stats.speed * target_stats.speed_multiplier

        damage = (atk * spd / 100) - (t_def * t_spd / 100)
        # ランダム補正
        variance = 1.0 + random.uniform(-DAMAGE_RANDOM_RANGE, DAMAGE_RANDOM_RANGE)
        damage = int(damage * variance)
        damage = max(MIN_DAMAGE, damage)

        target_stats.hp -= damage
        target_stats.is_defending = False
        return damage

    def execute_defend(self, actor_stats: BattleStats):
        """防御"""
        actor_stats.is_defending = True

    def try_flee(self, actor_stats: BattleStats) -> bool:
        """逃走を試みる"""
        rate = (actor_stats.defense + actor_stats.speed * actor_stats.speed_multiplier) / FLEE_DIVISOR
        return random.random() < rate

    def apply_card_buff(self, buff: BattleBuff, target_stats: BattleStats):
        """カードバフを適用"""
        target_stats.buffs.append(buff)

    def tick_buffs(self, stats: BattleStats):
        """バフターン管理"""
        stats.attack_multiplier = 1.0
        stats.defense_multiplier = 1.0
        stats.speed_multiplier = 1.0
        remaining = []
        for buff in stats.buffs:
            if buff.remaining_turns > 0:
                if buff.stat == "attack":
                    stats.attack_multiplier *= buff.multiplier
                elif buff.stat == "defense":
                    stats.defense_multiplier *= buff.multiplier
                elif buff.stat == "speed":
                    stats.speed_multiplier *= buff.multiplier
                buff.remaining_turns -= 1
                if buff.remaining_turns > 0:
                    remaining.append(buff)
            else:
                remaining.append(buff)
        stats.buffs = remaining

    def check_battle_end(self) -> bool:
        """戦闘終了判定"""
        if self.attacker_stats.hp <= 0:
            self.finished = True
            self.winner = self.defender
            self.loser = self.attacker
            return True
        if self.defender_stats.hp <= 0:
            self.finished = True
            self.winner = self.attacker
            self.loser = self.defender
            return True
        return False

    def next_battle_turn(self):
        self.turn += 1
        self.is_attacker_turn = not self.is_attacker_turn
        self.determine_turn_order()
