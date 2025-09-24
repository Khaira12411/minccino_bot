# 🟦────────────────────────────────────────────
#       🍀 Feeling Lucky Cooldown Cache 🍀
# ─────────────────────────────────────────────

import time
from utils.loggers.pretty_logs import pretty_log


# 🍀────────────────────────────────────────────
#       Feeling Lucky Cache Loader
# ─────────────────────────────────────────────

feeling_lucky_cache: dict[int, dict] = {}
# Structure:
# user_id -> {
#   "user_name": str,
#   "cooldown_until": int
# }


async def load_feeling_lucky_cache(bot):
    """
    Load all feeling lucky cooldowns into memory cache.
    Uses the fetch_all_feeling_lucky DB function.
    """
    feeling_lucky_cache.clear()
    from utils.database.fl_cd_db_func import fetch_all_feeling_lucky_cd

    rows = await fetch_all_feeling_lucky_cd(bot)
    for row in rows:
        feeling_lucky_cache[row["user_id"]] = {
            "user_name": row.get("user_name"),
            "cooldown_until": row.get("cooldown_until"),
        }

    pretty_log(
        message=f"Loaded {len(feeling_lucky_cache)} users' feeling lucky cooldowns into cache",
        label="🍀 FEELING LUCKY CACHE",
        bot=bot,
    )

    return feeling_lucky_cache


# 🟦────────────────────────────────────────────
#       🍀 Cache Functions
# ─────────────────────────────────────────────


def upsert_feeling_lucky_cache(user_id: int, user_name: str, cooldown_until: int):
    """
    Insert or update a row in the cache.
    """
    feeling_lucky_cache[user_id] = {
        "user_name": user_name,
        "cooldown_until": cooldown_until,
    }
    pretty_log(
        "info",
        f"Upserted cooldown for {user_name} ({user_id}) until {cooldown_until}",
        label="🍀 FEELING LUCKY CACHE",
    )


def fetch_feeling_lucky_cache(user_id: int) -> dict | None:
    """
    Fetch a single row from the cache.
    """
    return feeling_lucky_cache.get(user_id)


def fetch_all_feeling_lucky_cache() -> dict[int, dict]:
    """
    Fetch the entire cache.
    """
    return feeling_lucky_cache


def remove_feeling_lucky_cache(user_id: int):
    """
    Remove a row from the cache.
    """
    if user_id in feeling_lucky_cache:
        feeling_lucky_cache.pop(user_id)
        pretty_log(
            "info",
            f"Removed cooldown entry for {user_id} from cache",
            label="🍀 FEELING LUCKY CACHE",
        )


def is_user_on_cooldown(user_id: int) -> bool:
    """
    Returns True if user is still on cooldown, False otherwise.
    """
    data = feeling_lucky_cache.get(user_id)
    if not data:
        return False
    return time.time() < data.get("cooldown_until", 0)
