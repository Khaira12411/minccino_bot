# 🟦────────────────────────────────────────────
#       🐾 User faction ball alert Cache Loader 🐾
# ─────────────────────────────────────────────

import time

import discord
from utils.loggers.pretty_logs import pretty_log

faction_ball_alert_cache: dict[int, dict] = {}
# Structure:
# user_id -> {
#   "user_name": str,
#   "notify": str
# }


async def load_faction_ball_alert_cache(bot):
    """
    Load all faction ball alerts into memory cache.
    """
    from utils.database.faction_ball_alert_db_func import fetch_all_faction_ball_alerts

    faction_ball_alert_cache.clear()
    rows = await fetch_all_faction_ball_alerts(bot)
    for row in rows:
        faction_ball_alert_cache[row["user_id"]] = {
            "user_name": row.get("user_name"),
            "notify": row.get("notify"),
        }

    try:
        pretty_log(
            "info",
            f"Loaded {len(faction_ball_alert_cache)} faction ball alert entries into cache",
            label="🛡️  faction ball Alert CACHE",
            bot=bot,
        )
    except Exception as e:
        # fallback to console if Discord logging fails
        pretty_log(
            "error",
            f"Failed to log faction ball alert cache load: {e}",
            label="🛡️  faction ball Alert CACHE",
        )
    return faction_ball_alert_cache


# 🟦────────────────────────────────────────────
#       🔹 Upsert faction ball Alert in Cache 🔹
# ─────────────────────────────────────────────
def upsert_faction_ball_alert_cache(user: discord.Member, notify: str):
    """
    Insert or update a user's faction ball alert in cache.
    """
    user_id = user.id
    user_name = user.name

    faction_ball_alert_cache[user_id] = {
        "user_name": user_name,
        "notify": notify,
    }
    pretty_log(
        "info",
        f"Upserted faction ball alert for {user_name} ({user_id}) → {notify}",
        label="🐾 faction ball Alert CACHE",
    )


# 🟦────────────────────────────────────────────
#       🔍 Fetch Single faction ball Alert 🔍
# ─────────────────────────────────────────────
def fetch_user_faction_ball_alert_cache(user_id: int) -> dict | None:
    """
    Fetch a single user's faction ball alert from cache.
    """
    return faction_ball_alert_cache.get(user_id)


# 🟦────────────────────────────────────────────
#       📋 Fetch All faction ball alerts 📋
# ─────────────────────────────────────────────
def fetch_all_faction_ball_alert_cache() -> dict[int, dict]:
    """
    Fetch all faction ball alerts from cache.
    """
    return faction_ball_alert_cache


# 🟦────────────────────────────────────────────
#       ❌ Remove faction ball alert from Cache ❌
# ─────────────────────────────────────────────
def remove_user_faction_ball_alert_cache(user: discord.Member):
    """
    Remove a user's faction ball alert from cache.
    """
    user_id = user.id
    user_name = user.name
    if user_id in faction_ball_alert_cache:
        faction_ball_alert_cache.pop(user_id)
        pretty_log(
            "info",
            f"Removed faction ball alert for {user_name} from cache",
            label="🐾 faction ball Alert CACHE",
        )


# 🟦────────────────────────────────────────────
#       ✏️ Update Alert Type in Cache ✏️
# ─────────────────────────────────────────────
def update_faction_ball_alert_notify_type_cache(user: discord.Member, new_notify_type: str):
    """
    Update the alert_type of a user in cache.
    """
    user_id = user.id
    user_name = user.name

    if user_id in faction_ball_alert_cache:
        faction_ball_alert_cache[user_id]["notify"] = new_notify_type
        pretty_log(
            "info",
            f"Updated alert_type for {user_name} → {new_notify_type}",
            label="🐾 faction ball alert CACHE",
        )

def fetch_user_id_via_user_name_cache(user_name: str) -> int | None:
    """
    Fetch a user's ID based on their name from cache.
    """
    for user_id, data in faction_ball_alert_cache.items():
        if data.get("user_name") == user_name:
            return user_id
    return None