# 🟦────────────────────────────────────────────
#       🐾 User res fossils alert Cache Loader 🐾
# ─────────────────────────────────────────────

import time

import discord
from utils.loggers.pretty_logs import pretty_log

res_fossils_alert_cache: dict[int, dict] = {}
# Structure:
# user_id -> {
#   "user_name": str,
#   "notify": str
# }


async def load_res_fossils_alert_cache(bot):
    """
    Load all res fossils alerts into memory cache.
    """
    from utils.database.res_fossil_alert_db_func import fetch_all_res_fossils_alerts

    res_fossils_alert_cache.clear()
    rows = await fetch_all_res_fossils_alerts(bot)
    for row in rows:
        res_fossils_alert_cache[row["user_id"]] = {
            "user_name": row.get("user_name"),
            "notify": row.get("notify"),
        }

    try:
        pretty_log(
            "info",
            f"Loaded {len(res_fossils_alert_cache)} res fossils alert entries into cache",
            label="🛡️  Res Fossils Alert CACHE",
            bot=bot,
        )
    except Exception as e:
        # fallback to console if Discord logging fails
        print(
            f"[🛡️  RES FOSSILS ALERT CACHE] Loaded {len(res_fossils_alert_cache)} entries (pretty_log failed: {e})"
        )

    return res_fossils_alert_cache


# 🟦────────────────────────────────────────────
#       🔹 Upsert Res Fossils Alert in Cache 🔹
# ─────────────────────────────────────────────
def upsert_res_fossils_alert_cache(user:discord.Member, notify: str):
    """
    Insert or update a user's res fossils alert in cache.
    """
    user_id = user.id
    user_name = user.name

    res_fossils_alert_cache[user_id] = {
        "user_name": user_name,
        "notify": notify,
    }
    pretty_log(
        "info",
        f"Upserted res fossils alert for {user_name} ({user_id}) → {notify}",
        label="🐾 Res Fossil Alert CACHE",
    )


# 🟦────────────────────────────────────────────
#       🔍 Fetch Single Res Fossils Alert 🔍
# ─────────────────────────────────────────────
def fetch_user_res_fossils_alert_cache(user_id: int) -> dict | None:
    """
    Fetch a single user's res fossils alert from cache.
    """
    return res_fossils_alert_cache.get(user_id)


# 🟦────────────────────────────────────────────
#       📋 Fetch All res fossils alerts 📋
# ─────────────────────────────────────────────
def fetch_all_res_fossils_alert_cache() -> dict[int, dict]:
    """
    Fetch all res fossils alerts from cache.
    """
    return res_fossils_alert_cache


# 🟦────────────────────────────────────────────
#       ❌ Remove res fossils alert from Cache ❌
# ─────────────────────────────────────────────
def remove_user_res_fossils_alert_cache(user: discord.Member):
    """
    Remove a user's res fossils alert from cache.
    """
    user_id = user.id
    user_name = user.name
    if user_id in res_fossils_alert_cache:
        res_fossils_alert_cache.pop(user_id)
        pretty_log(
            "info",
            f"Removed res fossils alert for {user_name} from cache",
            label="🐾 Res Fossils Alert CACHE",
        )


# 🟦────────────────────────────────────────────
#       ✏️ Update Alert Type in Cache ✏️
# ─────────────────────────────────────────────
def update_res_fossil_notify_type_cache(user:discord.Member, new_notify_type: str):
    """
    Update the alert_type of a user in cache.
    """
    user_id = user.id
    user_name = user.name

    if user_id in res_fossils_alert_cache:
        res_fossils_alert_cache[user_id]["notify"] = new_notify_type
        pretty_log(
            "info",
            f"Updated alert_type for {user_name} → {new_notify_type}",
            label="🐾 res fossils alert CACHE",
        )
