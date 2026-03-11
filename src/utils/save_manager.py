"""セーブ/ロード管理"""
import json
import os

SAVE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "saves")


def save_game(game_state, filename: str = "autosave.json"):
    """ゲーム状態をセーブ"""
    os.makedirs(SAVE_DIR, exist_ok=True)
    filepath = os.path.join(SAVE_DIR, filename)

    data = {
        "version": "1.0",
        "turn_number": game_state.turn_number,
        "current_player_index": game_state.current_player_index,
        "players": [],
        "board_state": {"tiles": []},
    }

    for p in game_state.players:
        player_data = {
            "id": p.id,
            "name": p.name,
            "character_id": p.character_id,
            "is_human": p.is_human,
            "money": p.money,
            "position": p.position,
            "is_bankrupt": p.is_bankrupt,
            "slow_debuff_turns": p.slow_debuff_turns,
            "cards": [{"id": c.id, "name": c.name} for c in p.cards],
            "color": p.color,
        }
        data["players"].append(player_data)

    for t in game_state.board.tiles:
        tile_data = {
            "id": t.id,
            "land_price": t.land_price,
            "land_owner_id": t.land_owner_id,
        }
        if t.company:
            tile_data["company"] = {
                "name": t.company.name,
                "company_type": t.company.company_type,
                "owner_id": t.company.owner_id,
                "employees": t.company.employees,
                "ability": t.company.ability,
                "fame": t.company.fame,
                "construction_cost": t.company.construction_cost,
                "base_revenue": t.company.base_revenue,
            }
        data["board_state"]["tiles"].append(tile_data)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def has_save(filename: str = "autosave.json") -> bool:
    filepath = os.path.join(SAVE_DIR, filename)
    return os.path.exists(filepath)
