# utils/cache/user_reminders_cache.py
import copy

from group_func.toggle.reminders.user_reminders_db_func import fetch_all_rows
from utils.loggers.pretty_logs import pretty_log

# user_id -> reminders dict
# Example:
# {
#   123: {
#       "relics": {"has_exchanged": True, "enabled": True, "mode": "channel"},
#       "catchbot": {"enabled": False, "mode": "off", "repeating": None}
#   }
# }
user_reminders_cache: dict[int, dict] = {}


async def load_user_reminders_cache(bot):
    """
    Load all user reminders into memory.
    """
    user_reminders_cache.clear()
    try:
        rows = await fetch_all_rows(bot)
        for row in rows:
            reminders = row.get("reminders", {})
            # Ensure the structure is consistent
            relics = reminders.get("relics", {})
            relics.setdefault("has_exchanged", False)
            relics.setdefault("enabled", True)
            relics.setdefault("mode", "off")

            catchbot = reminders.get("catchbot", {})
            catchbot.setdefault("enabled", True)
            catchbot.setdefault("mode", "off")
            catchbot.setdefault("repeating", None)

            user_reminders_cache[row["user_id"]] = {
                "relics": relics,
                "catchbot": catchbot,
            }

        pretty_log(
            tag="",
            label="⚾ USER REMINDERS",
            message=f"Loaded {len(user_reminders_cache)} user reminders into cache.",
            bot=bot,
        )
    except Exception as e:
        pretty_log("error", f"Failed to load user reminders cache: {e}", bot=bot)

    return copy.deepcopy(user_reminders_cache)

from typing import Optional


def calculate_remind_next_on(user_settings: dict, ends_on: int) -> Optional[int]:
    """
    Calculate the remind_next_on timestamp for a user.

    Args:
        user_settings (dict): e.g., {"mode": "dms", "enabled": True, "repeating": 12}
        ends_on (int): Unix timestamp of the main event

    Returns:
        Optional[int]: Unix timestamp for next reminder or None if not applicable
    """
    mode = user_settings.get("mode", "off")
    if mode == "off":
        return None

    repeating = user_settings.get("repeating")
    if not repeating:
        return None

    # Convert minutes to seconds and add to ends_on
    return ends_on + int(repeating) * 60
