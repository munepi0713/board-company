"""ゲーム全体の状態管理"""
import random
from enum import Enum
from src.core.rules import (
    GOAL_ASSETS, LAND_FEE_RATE, COMPANY_FEE_RATE,
    LAND_BUYOUT_MULTIPLIER, COMPANY_BUYOUT_MULTIPLIER,
    SELL_RATE, NEWS_INTERVAL,
)
from src.core.player_model import Player
from src.core.board_model import BoardModel, Tile
from src.core.company_model import Company


class GamePhase(Enum):
    TURN_START = "turn_start"
    EVENT_CHECK = "event_check"
    NEWS = "news"
    REVENUE = "revenue"
    PLAYER_COMMAND = "player_command"
    DICE_ROLL = "dice_roll"
    DICE_RESULT = "dice_result"
    MOVING = "moving"
    BRANCH_SELECT = "branch_select"
    TILE_ACTION = "tile_action"
    PURCHASE_LAND = "purchase_land"
    BUILD_COMPANY = "build_company"
    PAY_FEE = "pay_fee"
    BATTLE_START = "battle_start"
    MANAGEMENT = "management"
    BATTLE = "battle"
    CARD_SHOP = "card_shop"
    TURN_END = "turn_end"
    GAME_OVER = "game_over"


class GameState:
    def __init__(self):
        self.turn_number: int = 1
        self.current_player_index: int = 0
        self.players: list = []
        self.board: BoardModel = None
        self.phase: GamePhase = GamePhase.TURN_START
        self.goal_assets: int = GOAL_ASSETS
        self.dice_value: int = 0
        self.winner = None
        self.messages: list = []
        self.event_results: list = []
        self.news_content: str = ""
        self.sponsor_names: list = []
        self.all_player_done: bool = False
        self.news_done: bool = False  # ニュース済みフラグ（同一ターン再表示防止）
        self.news_snapshot: dict = {}  # 前回ニュース時のスナップショット

    @property
    def current_player(self) -> Player:
        return self.players[self.current_player_index]

    @property
    def active_players(self) -> list:
        return [p for p in self.players if not p.is_bankrupt]

    def get_player_total_assets(self, player: Player) -> int:
        """プレイヤーの総資産を計算"""
        land_value = 0
        company_value = 0
        for tile in self.board.tiles:
            if tile.land_owner_id == player.id:
                land_value += tile.land_price
            if tile.company and tile.company.owner_id == player.id:
                company_value += tile.company.evaluation
        return player.money + land_value + company_value

    def roll_dice(self) -> int:
        """サイコロを振り、結果を返す"""
        self.dice_value = random.randint(1, 6)
        player = self.current_player
        if player.is_slowed:
            self.dice_value = 1
        player.remaining_moves = self.dice_value
        return self.dice_value

    def advance_movement(self) -> bool:
        """1マス進める。移動完了ならTrueを返す"""
        player = self.current_player
        if player.remaining_moves <= 0:
            return True

        tile = self.board.get_tile(player.position)
        next_tiles = tile.next_tiles

        if len(next_tiles) == 0:
            return True

        if len(next_tiles) > 1 and player.remaining_moves > 0:
            self.phase = GamePhase.BRANCH_SELECT
            return False

        player.position = next_tiles[0]
        player.remaining_moves -= 1
        player.stats.tiles_moved += 1

        if player.remaining_moves <= 0:
            return True
        return False

    def choose_branch(self, branch_index: int):
        """分岐を選択"""
        player = self.current_player
        tile = self.board.get_tile(player.position)
        if 0 <= branch_index < len(tile.next_tiles):
            player.position = tile.next_tiles[branch_index]
            player.remaining_moves -= 1
            player.stats.tiles_moved += 1

    def check_victory(self):
        """勝利条件を判定"""
        for player in self.active_players:
            if self.get_player_total_assets(player) >= self.goal_assets:
                self.winner = player
                return player
        if len(self.active_players) <= 1 and len(self.players) > 1:
            self.winner = self.active_players[0] if self.active_players else None
            return self.winner
        return None

    def process_even_turn_revenue(self):
        """偶数ターンの損益計上"""
        results = []
        for player in self.active_players:
            total_revenue = 0
            total_land_fee = 0
            for tile in self.board.tiles:
                if tile.company and tile.company.owner_id == player.id:
                    revenue = tile.company.fixed_revenue
                    player.add_money(revenue)
                    total_revenue += revenue
                    player.stats.total_revenue += revenue
                    tile.company.apply_decay()
                    # 土地使用料の支払い
                    if tile.land_owner_id is not None and tile.land_owner_id != player.id:
                        land_fee = int(tile.land_price * LAND_FEE_RATE)
                        player.pay(land_fee)
                        owner = self._get_player_by_id(tile.land_owner_id)
                        if owner:
                            owner.add_money(land_fee)
                            owner.stats.total_land_income += land_fee
                        total_land_fee += land_fee
            if total_revenue > 0 or total_land_fee > 0:
                results.append(
                    f"{player.name}: +{total_revenue}$ (売上), -{total_land_fee}$ (土地使用料)"
                )
        return results

    def next_player(self):
        """次のプレイヤーに移行"""
        start_index = self.current_player_index
        while True:
            self.current_player_index = (self.current_player_index + 1) % len(self.players)
            if self.current_player_index == 0:
                self.all_player_done = True
            if not self.current_player.is_bankrupt:
                break
            if self.current_player_index == start_index:
                break

    def next_turn(self):
        """次のターンに進む"""
        self.turn_number += 1
        self.current_player_index = 0
        self.all_player_done = False
        self.news_done = False
        while self.current_player.is_bankrupt and self.current_player_index < len(self.players) - 1:
            self.current_player_index += 1

    def is_news_turn(self) -> bool:
        return self.turn_number % NEWS_INTERVAL == 0

    def is_even_turn(self) -> bool:
        return self.turn_number % 2 == 0

    def take_news_snapshot(self):
        """現在のゲーム状態をスナップショットとして保存"""
        snapshot = {
            "turn": self.turn_number,
            "players": {},
            "land_prices": {},
            "companies": {},
        }
        for p in self.players:
            snapshot["players"][p.id] = {
                "money": p.money,
                "assets": self.get_player_total_assets(p),
                "land_count": len(p.owned_land_ids),
                "company_count": len(p.owned_company_ids),
            }
        for tile in self.board.tiles:
            if tile.tile_type == "normal":
                snapshot["land_prices"][tile.id] = tile.land_price
            if tile.company:
                snapshot["companies"][tile.id] = {
                    "name": tile.company.name,
                    "owner_id": tile.company.owner_id,
                    "employees": tile.company.employees,
                }
        self.news_snapshot = snapshot

    def _get_player_by_id(self, player_id: int):
        for p in self.players:
            if p.id == player_id:
                return p
        return None

    def get_tile_action_type(self, tile: Tile, player: Player) -> str:
        """マス到着時のアクション種類を判定"""
        if tile.tile_type == "card_shop":
            return "card_shop"
        elif tile.tile_type == "plus":
            return "plus"
        elif tile.tile_type == "minus":
            return "minus"
        elif tile.tile_type == "card":
            return "card_get"
        elif tile.tile_type == "normal":
            if not tile.is_owned and not tile.has_company:
                return "empty_land"
            elif tile.land_owner_id == player.id:
                if tile.has_company and tile.company.owner_id == player.id:
                    return "own_land_own_company"
                elif tile.has_company:
                    return "own_land_other_company"
                else:
                    return "own_land_no_company"
            else:
                if tile.has_company and tile.company.owner_id != player.id:
                    return "other_land_other_company"
                elif tile.has_company and tile.company.owner_id == player.id:
                    return "other_land_own_company"
                else:
                    return "other_land_no_company"
        return "none"
