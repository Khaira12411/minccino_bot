from config.held_items import HELD_ITEMS_DICT
from group_func.toggle.held_item.held_items_db_func import fetch_all_user_item_pings
from utils.loggers.pretty_logs import pretty_log

# 🟣────────────────────────────────────────────
#       🐭 Held Item Cache Loader 🐭
# ─────────────────────────────────────────────

held_item_cache: dict[int, dict] = {}
# Structure:
# user_id -> {
#   "user_name": str,
#   "subscribed_items": set[str],
#   "all_held_items": bool
# }


# 🟣────────────────────────────────────────────
#       🐭 Held Item Cache Loader 🐭
# ─────────────────────────────────────────────

import json

from group_func.toggle.held_item.held_items_db_func import fetch_all_user_item_pings
from utils.loggers.pretty_logs import pretty_log

held_item_cache: dict[int, dict] = {}
# Structure:
# user_id -> {
#   "user_name": str,
#   "subscribed_items": set[str],
#   "all_held_items": bool
# }


async def load_held_item_cache(bot):
    """
    Load all user held item subscriptions into memory cache.
    Uses the fetch_all_user_item_pings DB function.
    """
    held_item_cache.clear()

    rows = await fetch_all_user_item_pings(bot)
    for row in rows:
        held_item_pings = row.get("held_item_pings") or {}

        # If it's a string from DB, parse JSON
        if isinstance(held_item_pings, str):
            held_item_pings = json.loads(held_item_pings)

        # Extract "all_held_items" separately from JSON or DB column
        all_flag = (
            held_item_pings.get("all_held_items", False)
            if isinstance(held_item_pings, dict)
            else bool(row.get("all_held_items", False))
        )

        # Build a set of subscribed items, excluding the all_held_items key
        subscribed_items = {
            item
            for item, sub in held_item_pings.items()
            if sub and item != "all_held_items"
        }

        held_item_cache[row["user_id"]] = {
            "user_name": row.get("user_name"),
            "subscribed_items": subscribed_items,
            "all_held_items": all_flag,
        }

    pretty_log(
        message=f"Loaded {len(held_item_cache)} users' held item subscriptions into cache",
        label="🍄 HELD ITEM CACHE",
        bot=bot,
    )

    # DEBUG: print full cache
    """pretty_log(
        message=f"Full held_item_cache: {held_item_cache}",
        label="🐭 HELD ITEM CACHE",
        bot=bot,
    )"""

    return held_item_cache


# ────────────────────────────────────────────
#       🐭 Helper: Users to Ping from Cache 🐭
# ────────────────────────────────────────────
def get_users_to_ping_from_cache(pokemon_name: str, held_item_name: str) -> list[dict]:
    """
    Returns a list of users from the cache who should be pinged
    for a given Pokemon + held item.
    """
    users = []
    for user_id, data in held_item_cache.items():
        subscribed_items = data.get("subscribed_items", set())
        all_held_items = data.get("all_held_items", False)

        # Check if this user is subscribed to the held item
        if held_item_name in subscribed_items or all_held_items:
            # Check if the Pokemon can carry this item
            item_meta = HELD_ITEMS_DICT.get(held_item_name)
            if item_meta and pokemon_name.lower() in item_meta["pokemon"]:
                users.append({"user_id": user_id, "user_name": data.get("user_name")})

    return users


# ────────────────────────────────────────────
#       🐭 Ping Users for Pokemon (Cache) 🐭
# ────────────────────────────────────────────
async def ping_users_for_mon(bot, channel, pokemon_name: str, held_item_name: str):
    """
    Ping all users who are subscribed to a specific held item
    AND the Pokemon can carry that item.
    Uses the in-memory held_item_cache for speed.
    """
    users = get_users_to_ping_from_cache(pokemon_name, held_item_name)
    if not users:
        return

    emoji = HELD_ITEMS_DICT.get(held_item_name, {}).get("emoji", "🐭")
    mentions = " ".join(f"<@{u['user_id']}>" for u in users)

    try:
        await channel.send(
            f"{emoji} {mentions} {pokemon_name.title()} may have a {held_item_name.replace('_',' ').title()}!"
        )
        pretty_log(
            "info",
            f"Pinged {len(users)} users for {pokemon_name} with {held_item_name}",
            label="🐭 HELD ITEM PING",
            bot=bot,
        )
    except Exception as e:
        pretty_log(
            "error",
            f"Failed to send held item ping for {pokemon_name}/{held_item_name}: {e}",
            label="🐭 HELD ITEM PING",
            bot=bot,
        )
