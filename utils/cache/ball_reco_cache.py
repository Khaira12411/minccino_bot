# Ball Recommendation Cache
# user_id -> {
#   "user_name": str,
#   "is_patreon": bool,
#   "catch_rate_bonus": float,
#   "held_items": dict,
#   "pokemon": dict,
#   "fishing": dict
# }

from utils.loggers.pretty_logs import pretty_log
from group_func.toggle.ball_recon.ball_recon_db_func import *
import json

ball_reco_cache: dict[int, dict] = {}


async def load_ball_reco_cache(bot):
    """
    Load all user ball recommendation preferences into memory cache.
    Uses the fetch_all_user_recs DB function.
    """
    ball_reco_cache.clear()

    rows = await fetch_all_user_recs(bot)
    for row in rows:
        # Parse JSON columns if they are strings
        held_items = row.get("held_items") or {}
        if isinstance(held_items, str):
            held_items = json.loads(held_items)

        pokemon = row.get("pokemon") or {}
        if isinstance(pokemon, str):
            pokemon = json.loads(pokemon)

        fishing = row.get("fishing") or {}
        if isinstance(fishing, str):
            fishing = json.loads(fishing)

        ball_reco_cache[row["user_id"]] = {
            "user_name": row.get("user_name"),
            "is_patreon": row.get("is_patreon", False),
            "catch_rate_bonus": row.get("catch_rate_bonus", 0),
            "held_items": held_items,
            "pokemon": pokemon,
            "fishing": fishing,
            "enabled": row.get("enabled", False),  # <-- add this
        }

    return ball_reco_cache

def get_user_id_by_name(trainer_name: str) -> int | None:
    """
    Retrieve user ID from ball_reco_cache by trainer name.

    Args:
        trainer_name: The Discord trainer name to look up.
    Returns:
        The user ID if found, otherwise None.
    """
    for user_id, settings in ball_reco_cache.items():
        if settings.get("user_name") == trainer_name:
            return user_id
    return None

def check_if_id_in_ball_reco_cache(user_id: int) -> bool:
    """
    Check if a user ID exists in the ball recommendation cache.

    Args:
        user_id: The Discord user ID to check.
    Returns:
        True if the user ID exists in the cache, otherwise False.
    """
    return user_id in ball_reco_cache