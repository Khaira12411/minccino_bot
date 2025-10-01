# 🟦────────────────────────────────────────────
#       🐾 User Captcha Alert Cache Loader 🐾
# ─────────────────────────────────────────────

import time
from utils.loggers.pretty_logs import pretty_log

user_captcha_alert_cache: dict[int, dict] = {}
# Structure:
# user_id -> {
#   "user_name": str,
#   "alert_type": str
# }


async def load_user_captcha_alert_cache(bot):
    """
    Load all user captcha alerts into memory cache.
    """
    from utils.database.captcha_alert_db_func import fetch_all_captcha_alerts

    user_captcha_alert_cache.clear()
    rows = await fetch_all_captcha_alerts(bot)
    for row in rows:
        user_captcha_alert_cache[row["user_id"]] = {
            "user_name": row.get("user_name"),
            "alert_type": row.get("alert_type"),
        }

    try:
        pretty_log(
            "info",
            f"Loaded {len(user_captcha_alert_cache)} captcha alert entries into cache",
            label="🛡️  CAPTCHA ALERT CACHE",
            bot=bot,
        )
    except Exception as e:
        # fallback to console if Discord logging fails
        print(
            f"[🛡️  CAPTCHA ALERT CACHE] Loaded {len(user_captcha_alert_cache)} entries (pretty_log failed: {e})"
        )

    return user_captcha_alert_cache


# 🟦────────────────────────────────────────────
#       🔹 Upsert Captcha Alert in Cache 🔹
# ─────────────────────────────────────────────
def upsert_user_captcha_alert_cache(user_id: int, user_name: str, alert_type: str):
    """
    Insert or update a user's captcha alert in cache.
    """
    user_captcha_alert_cache[user_id] = {
        "user_name": user_name,
        "alert_type": alert_type,
    }
    pretty_log(
        "info",
        f"Upserted captcha alert for {user_name} ({user_id}) → {alert_type}",
        label="🐾 CAPTCHA ALERT CACHE",
    )


# 🟦────────────────────────────────────────────
#       🔍 Fetch Single Captcha Alert 🔍
# ─────────────────────────────────────────────
def fetch_user_captcha_alert_cache(user_id: int) -> dict | None:
    """
    Fetch a single user's captcha alert from cache.
    """
    return user_captcha_alert_cache.get(user_id)


# 🟦────────────────────────────────────────────
#       📋 Fetch All Captcha Alerts 📋
# ─────────────────────────────────────────────
def fetch_all_user_captcha_alert_cache() -> dict[int, dict]:
    """
    Fetch all captcha alerts from cache.
    """
    return user_captcha_alert_cache


# 🟦────────────────────────────────────────────
#       ❌ Remove Captcha Alert from Cache ❌
# ─────────────────────────────────────────────
def remove_user_captcha_alert_cache(user_id: int):
    """
    Remove a user's captcha alert from cache.
    """
    if user_id in user_captcha_alert_cache:
        user_captcha_alert_cache.pop(user_id)
        pretty_log(
            "info",
            f"Removed captcha alert for user {user_id} from cache",
            label="🐾 CAPTCHA ALERT CACHE",
        )


# 🟦────────────────────────────────────────────
#       ✏️ Update Alert Type in Cache ✏️
# ─────────────────────────────────────────────
def update_user_alert_type_cache(user_id: int, new_alert_type: str):
    """
    Update the alert_type of a user in cache.
    """
    if user_id in user_captcha_alert_cache:
        user_captcha_alert_cache[user_id]["alert_type"] = new_alert_type
        pretty_log(
            "info",
            f"Updated alert_type for {user_id} → {new_alert_type}",
            label="🐾 CAPTCHA ALERT CACHE",
        )
