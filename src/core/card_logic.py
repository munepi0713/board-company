"""カード効果・使用条件判定"""
import random
from dataclasses import dataclass


@dataclass
class Card:
    id: str
    name: str
    price: int
    card_type: str  # "normal" or "battle"
    description: str

    @property
    def sell_price(self) -> int:
        return self.price // 5


# カード定義
CARD_DEFINITIONS = {
    "double_dice": Card("double_dice", "x2の目カード", 150, "normal",
                        "出た目の2倍の数を進む"),
    "teleport": Card("teleport", "ぶっとびカード", 300, "normal",
                      "ランダムなマスにジャンプ"),
    "slow": Card("slow", "のんびりカード", 100, "normal",
                  "相手を5ターン1歩に制限"),
    "tax_audit": Card("tax_audit", "マルサの女カード", 800, "normal",
                       "ランダムな1人の財産1/3没収"),
    "jcbb": Card("jcbb", "JCBBカード", 100, "normal",
                  "空き地を1/5価格で購入可能"),
    "takeover": Card("takeover", "乗っ取りカード", 200, "normal",
                      "他人の会社を評価額x2で購入(1/3失敗)"),
    "temp_worker": Card("temp_worker", "契約社員カード", 100, "battle",
                         "攻撃力1.5倍(1ターン)"),
    "training": Card("training", "社員教育カード", 100, "battle",
                      "防御力2倍(2ターン)"),
    "tv_cm": Card("tv_cm", "TV CMカード", 100, "battle",
                   "すばやさ2倍(2ターン)"),
    "repair": Card("repair", "ビル補修カード", 300, "battle",
                    "HP 1/3回復"),
    "headhunt": Card("headhunt", "社員引き抜きカード", 200, "battle",
                      "相手の攻撃力0.7倍(戦闘終了まで)"),
    "compare_cm": Card("compare_cm", "比較CMカード", 200, "battle",
                        "相手のすばやさ0.7倍(戦闘終了まで)"),
}


def get_random_card() -> Card:
    """ランダムなカードを1枚返す"""
    return random.choice(list(CARD_DEFINITIONS.values()))


def get_shop_cards(count: int = 4) -> list:
    """カード売り場の品揃えを返す"""
    all_cards = list(CARD_DEFINITIONS.values())
    return random.sample(all_cards, min(count, len(all_cards)))


def get_normal_cards(cards: list) -> list:
    """通常使用可能カードをフィルタ"""
    return [c for c in cards if c.card_type == "normal"]


def get_battle_cards(cards: list) -> list:
    """戦闘使用可能カードをフィルタ"""
    return [c for c in cards if c.card_type == "battle"]
