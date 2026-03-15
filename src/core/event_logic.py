"""イベント発生・効果適用"""
import random


EVENT_DEFINITIONS = [
    {
        "id": "land_price_up",
        "name": "地価上昇",
        "probability": {"numerator": 1, "denominator": 30},
        "message": "{tile_name}地区の地価が上昇しました！",
    },
    {
        "id": "land_price_down",
        "name": "地価下落",
        "probability": {"numerator": 1, "denominator": 50},
        "message": "{tile_name}地区の地価が下落しました...",
    },
    {
        "id": "recession",
        "name": "不景気",
        "probability": {"numerator": 1, "denominator": 50},
        "message": "不景気の影響で{company_name}社の社員が退職しました",
    },
    {
        "id": "boom",
        "name": "好景気",
        "probability": {"numerator": 1, "denominator": 50},
        "message": "好景気の影響で各社の売上が伸びています！",
    },
    {
        "id": "typhoon",
        "name": "台風",
        "probability": {"numerator": 1, "denominator": 40},
        "message": "台風の影響で各社の事業に大きな影響が出ています！",
    },
]

NEWS_TEMPLATES = [
    "今日も平和な一日でした。",
    "経済は堅調に推移しています。",
    "新しいビジネスチャンスが生まれています。",
    "市場は安定しています。",
    "投資家の注目が集まっています。",
]


def check_events(turn_number: int) -> list:
    """ターン開始時のイベント判定"""
    triggered = []
    for event in EVENT_DEFINITIONS:
        prob = event["probability"]
        if random.randint(1, prob["denominator"]) <= prob["numerator"]:
            triggered.append(event)
    return triggered


def apply_event(event: dict, game_state) -> str:
    """イベント効果を適用し、メッセージを返す"""
    board = game_state.board

    if event["id"] == "land_price_up":
        normal_tiles = board.get_all_normal_tiles()
        if normal_tiles:
            tile = random.choice(normal_tiles)
            tile.land_price = int(tile.land_price * 1.3)
            return event["message"].format(tile_name=tile.name)

    elif event["id"] == "land_price_down":
        normal_tiles = board.get_all_normal_tiles()
        if normal_tiles:
            tile = random.choice(normal_tiles)
            tile.land_price = int(tile.land_price * 0.8)
            return event["message"].format(tile_name=tile.name)

    elif event["id"] == "recession":
        companies = [t for t in board.tiles if t.company]
        if companies:
            tile = random.choice(companies)
            loss = random.randint(0, 3)
            tile.company.employees = max(0, tile.company.employees - loss)
            return event["message"].format(company_name=tile.company.name)

    elif event["id"] == "boom":
        for tile in board.tiles:
            if tile.company:
                gain = random.randint(0, 3)
                tile.company.base_revenue += gain
        return event["message"]

    elif event["id"] == "typhoon":
        active = game_state.active_players
        positions = [p.position for p in active]
        random.shuffle(positions)
        for i, player in enumerate(active):
            player.position = positions[i]
        return event["message"]

    return event.get("name", "イベント発生")


def get_news_content(events: list) -> str:
    """ニュース内容を生成"""
    if events:
        return "、".join(e["name"] for e in events) + "が発生しました。"
    return random.choice(NEWS_TEMPLATES)


def generate_cumulative_news(game_state) -> str:
    """前回ニュースからの総合的な変化を報道するニュース文を生成"""
    snapshot = game_state.news_snapshot
    if not snapshot:
        return random.choice(NEWS_TEMPLATES)

    lines = []

    # プレイヤー資産変化
    asset_changes = []
    for p in game_state.players:
        if p.is_bankrupt:
            continue
        prev = snapshot.get("players", {}).get(p.id)
        if not prev:
            continue
        current_assets = game_state.get_player_total_assets(p)
        prev_assets = prev["assets"]
        diff = current_assets - prev_assets
        if diff > 0:
            asset_changes.append(f"{p.name}+{diff}$")
        elif diff < 0:
            asset_changes.append(f"{p.name}{diff}$")

    if asset_changes:
        lines.append("資産変動: " + "、".join(asset_changes) + "。")

    # 地価変動まとめ
    up_count = 0
    down_count = 0
    prev_prices = snapshot.get("land_prices", {})
    for tile in game_state.board.tiles:
        if tile.tile_type != "normal":
            continue
        prev_price = prev_prices.get(tile.id)
        if prev_price is not None:
            if tile.land_price > prev_price:
                up_count += 1
            elif tile.land_price < prev_price:
                down_count += 1
    if up_count > 0 or down_count > 0:
        parts = []
        if up_count > 0:
            parts.append(f"{up_count}地区で上昇")
        if down_count > 0:
            parts.append(f"{down_count}地区で下落")
        lines.append("地価が" + "、".join(parts) + "。")

    # 新規会社
    prev_companies = snapshot.get("companies", {})
    new_companies = []
    for tile in game_state.board.tiles:
        if tile.company and tile.id not in prev_companies:
            new_companies.append(tile.company.name)
    if new_companies:
        lines.append("新会社: " + "、".join(new_companies[:3]) + "設立。")

    # ランキング
    ranked = sorted(
        [p for p in game_state.players if not p.is_bankrupt],
        key=lambda p: game_state.get_player_total_assets(p),
        reverse=True,
    )
    if ranked:
        leader = ranked[0]
        assets = game_state.get_player_total_assets(leader)
        lines.append(f"首位は{leader.name}({assets}$)。")

    if not lines:
        return random.choice(NEWS_TEMPLATES)
    return " ".join(lines)


def get_sponsors(game_state, count: int = 2) -> list:
    """スポンサーを選択"""
    companies = []
    for tile in game_state.board.tiles:
        if tile.company:
            companies.append(tile.company.name)
    if len(companies) >= count:
        return random.sample(companies, count)
    elif companies:
        result = companies[:]
        while len(result) < count:
            result.append("EXGRACE SOFT")
        return result
    return ["EXGRACE SOFT"] * count
