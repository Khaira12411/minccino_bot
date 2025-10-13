import time

import discord
from utils.loggers.pretty_logs import pretty_log

straymon_member_cache: dict[int, dict] = {}
# Structure:
# user_id -> {
#   "user_name": str,
#   "channel_id": int
#   "faction": str
# }


async def load_straymon_member_cache(bot):
    """
    Load all straymon members into memory cache.
    Uses the fetch_all_straymon_members DB function.
    """
    from utils.database.straymon_info_db_func import fetch_all_straymon_members

    straymon_member_cache.clear()
    rows = await fetch_all_straymon_members(bot)
    for row in rows:
        straymon_member_cache[row["user_id"]] = {
            "user_name": row.get("user_name"),
            "channel_id": row.get("channel_id"),
            "faction": row.get("faction"),
        }

    try:
        pretty_log(
            "info",
            f"Loaded {len(straymon_member_cache)} straymon members into cache",
            label="💠 STRAYMON MEMBER CACHE",
            bot=bot,
        )
    except Exception as e:
        # fallback to console if Discord logging fails
        print(
            f"[💠 STRAYMON MEMBER CACHE] Loaded {len(straymon_member_cache)} entries (pretty_log failed: {e})"
        )

    return straymon_member_cache

def fetch_straymon_member_cache(user_id: int):
    """
    Fetch a straymon member from cache by user ID.
    Returns a dict with user_name and channel_id, or None if not found.
    """
    return straymon_member_cache.get(user_id)


def fetch_straymon_member_cache_by_name(user_name: str) -> dict | None:
    """
    Fetch a member's info from the Straymon cache by their user_name.
    """
    if not user_name:
        return None

    lowered_name = user_name.lower()

    for user_id, data in straymon_member_cache.items():
        if not data or not isinstance(data, dict):
            continue

        # ✅ FIX: Safe string conversion and comparison
        cached_user_name = data.get("user_name")
        if cached_user_name and str(cached_user_name).lower() == lowered_name:
            return data

    return None
