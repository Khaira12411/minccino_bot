import discord
from utils.loggers.pretty_logs import pretty_log
from .cache_list import user_alerts_cache
from utils.database.user_alerts_db import fetch_all_user_alerts

# Cache Structure:
# {
#   user_id: {
#     alert_type: {
#       "user_name": str,
#       "notify": str
#     },
#     ...
#   },
#   ...
# }
async def load_user_alert_cache(bot: discord.Client):
    """Load the user alert cache from the database."""
    user_alerts_cache.clear()
    try:
        alerts = await fetch_all_user_alerts(bot)
        if not alerts:
            pretty_log(
                message="⚠️ No user alerts found to load into cache.",
                tag="cache",
            )
            return

        for alert in alerts:
            user_id = alert["user_id"]
            alert_type = alert["alert_type"]
            alert_entry = {
                "user_name": alert["user_name"],
                "notify": alert["notify"],
            }
            if user_id not in user_alerts_cache:
                user_alerts_cache[user_id] = {}
            user_alerts_cache[user_id][alert_type] = alert_entry

        pretty_log(
            message=f"✅ Loaded user alert cache with {len(user_alerts_cache)} users.",
            tag="cache",
        )
        return user_alerts_cache

    except Exception as e:
        pretty_log(
            message=f"❌ Error loading user alert cache: {e}",
            tag="cache",
        )

def upsert_user_alert_cache(
    user_id: int,
    alert_type: str,
    user_name: str,
    notify: str,
):
    """Upsert a user alert into the cache."""
    if user_id not in user_alerts_cache:
        user_alerts_cache[user_id] = {}
    user_alerts_cache[user_id][alert_type] = {
        "user_name": user_name,
        "notify": notify,
    }
    pretty_log(
        tag="cache",
        message=f"Upserted alert for user_id {user_id}, alert_type {alert_type} into cache.",

    )
def remove_user_alerts_for_user_cache(user_id: int):
    """Remove all alerts for a user from the cache."""
    if user_id in user_alerts_cache:
        del user_alerts_cache[user_id]
        pretty_log(
            tag="cache",
            message=f"Removed all alerts for user_id {user_id} from cache.",
        )
    else:
        pretty_log(
            tag="info",
            message=f"Attempted to remove alerts for non-existent user_id {user_id} from cache.",
        )

def delete_user_alert_cache(user_id: int, alert_type: str):
    """Delete a user alert from the cache."""
    if user_id in user_alerts_cache and alert_type in user_alerts_cache[user_id]:
        del user_alerts_cache[user_id][alert_type]
        if not user_alerts_cache[user_id]:
            del user_alerts_cache[user_id]
        pretty_log(
            tag="cache",
            message=f"Deleted alert for user_id {user_id}, alert_type {alert_type} from cache.",
        )
    else:
        pretty_log(
            tag="info",
            message=f"Attempted to delete non-existent alert for user_id {user_id}, alert_type {alert_type} from cache.",
        )
def fetch_user_alert_notify_cache(user_id: int, alert_type: str) -> str | None:
    """Fetch the notify setting for a user alert from the cache."""
    if user_id in user_alerts_cache and alert_type in user_alerts_cache[user_id]:
        return user_alerts_cache[user_id][alert_type]["notify"]
    return None

def update_user_alert_notify_cache(
    user_id: int,
    alert_type: str,
    notify: str,
):
    """Update the notify setting for a user alert in the cache."""
    if user_id in user_alerts_cache and alert_type in user_alerts_cache[user_id]:
        user_alerts_cache[user_id][alert_type]["notify"] = notify
        pretty_log(
            tag="cache",
            message=f"Updated notify setting for user_id {user_id}, alert_type {alert_type} to {notify} in cache.",
        )
    else:
        pretty_log(
            tag="info",
            message=f"Attempted to update notify setting for non-existent alert for user_id {user_id}, alert_type {alert_type} in cache.",
        )