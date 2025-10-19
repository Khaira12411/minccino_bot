# 🟦────────────────────────────────────────────
#       🐾 User halloween contest alert Cache Loader 🐾
# ─────────────────────────────────────────────

import time

import discord
from utils.loggers.pretty_logs import pretty_log

halloween_contests_alert_cache: dict[int, dict] = {}
# Structure:
# user_id -> {
#   "user_name": str,
#   "notify": str
# }


async def load_halloween_contest_alert_cache(bot):
    """
    Load all halloween contest alerts into memory cache.
    """
    from utils.database.halloween_contest_alert import fetch_all_halloween_contest_alerts

    halloween_contests_alert_cache.clear()
    rows = await fetch_all_halloween_contest_alerts(bot)
    for row in rows:
        halloween_contests_alert_cache[row["user_id"]] = {
            "user_name": row.get("user_name"),
            "notify": row.get("notify"),
        }

    try:
        pretty_log(
            "info",
            f"Loaded {len(halloween_contests_alert_cache)} halloween contest alert entries into cache",
            label="🛡️  halloween contest Alert CACHE",
            bot=bot,
        )
    except Exception as e:
        # fallback to console if Discord logging fails
        print(
            f"[🛡️  halloween contest ALERT CACHE] Loaded {len(halloween_contests_alert_cache)} entries (pretty_log failed: {e})"
        )

    return halloween_contests_alert_cache


# 🟦────────────────────────────────────────────
#       🔹 Upsert halloween contest Alert in Cache 🔹
# ─────────────────────────────────────────────
def upsert_halloween_contest_alert_cache(user: discord.Member, notify: str):
    """
    Insert or update a user's halloween contest alert in cache.
    """
    user_id = user.id
    user_name = user.name

    halloween_contests_alert_cache[user_id] = {
        "user_name": user_name,
        "notify": notify,
    }
    pretty_log(
        "info",
        f"Upserted halloween contest alert for {user_name} ({user_id}) → {notify}",
        label="🐾 Res Fossil Alert CACHE",
    )


# 🟦────────────────────────────────────────────
#       🔍 Fetch Single halloween contest Alert 🔍
# ─────────────────────────────────────────────
def fetch_user_halloween_contest_alert_cache(user_id: int) -> dict | None:
    """
    Fetch a single user's halloween contest alert from cache.
    """
    return halloween_contests_alert_cache.get(user_id)


# 🟦────────────────────────────────────────────
#       📋 Fetch All halloween contest alerts 📋
# ─────────────────────────────────────────────
def fetch_all_halloween_contest_alert_cache() -> dict[int, dict]:
    """
    Fetch all halloween contest alerts from cache.
    """
    return halloween_contests_alert_cache


# 🟦────────────────────────────────────────────
#       ❌ Remove halloween contest alert from Cache ❌
# ─────────────────────────────────────────────
def remove_user_halloween_contest_alert_cache(user: discord.Member):
    """
    Remove a user's halloween contest alert from cache.
    """
    user_id = user.id
    user_name = user.name
    if user_id in halloween_contests_alert_cache:
        halloween_contests_alert_cache.pop(user_id)
        pretty_log(
            "info",
            f"Removed halloween contest alert for {user_name} from cache",
            label="🐾 halloween contest Alert CACHE",
        )


# 🟦────────────────────────────────────────────
#       ✏️ Update Alert Type in Cache ✏️
# ─────────────────────────────────────────────
def update_halloween_contest_notify_type_cache(user: discord.Member, new_notify_type: str):
    """
    Update the alert_type of a user in cache.
    """
    user_id = user.id
    user_name = user.name

    if user_id in halloween_contests_alert_cache:
        halloween_contests_alert_cache[user_id]["notify"] = new_notify_type
        pretty_log(
            "info",
            f"Updated alert_type for {user_name} → {new_notify_type}",
            label="🐾 halloween contest alert CACHE",
        )
