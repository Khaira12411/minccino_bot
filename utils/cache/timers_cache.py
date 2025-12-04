from group_func.toggle.timer.timer_db_func import fetch_all_timers
from utils.loggers.pretty_logs import pretty_log

# 🟣────────────────────────────────────────────
#       🐭 Timer Cache Loader 🐭
# ─────────────────────────────────────────────

timer_cache = (
    {}
)  # user_id -> {"pokemon_setting": str, "fish_setting": str, "battle_setting": str}


async def load_timer_cache(bot):
    """
    Load all user timer settings into memory cache.
    Uses the fetch_all_timers DB function.
    """
    timer_cache.clear()

    rows = await fetch_all_timers(bot)
    for row in rows:
        timer_cache[row["user_id"]] = {
            "user_name": row.get("user_name"),
            "pokemon_setting": row.get("pokemon_setting"),
            "fish_setting": row.get("fish_setting"),
            "battle_setting": row.get("battle_setting"),
        }

    # 🐭 Debug log
    pretty_log(
        message=f"Loaded {len(timer_cache)} users' timer settings into cache",
        label="⌚ TIMER CACHE",
        bot=bot,
    )

    return timer_cache

def set_timer_cache(
    user_id: int,
    user_name: str,
    pokemon_setting: str,
    fish_setting: str,
    battle_setting: str,
):
    """
    Update the in-memory timer cache for a specific user.
    """
    timer_cache[user_id] = {
        "user_name": user_name,
        "pokemon_setting": pokemon_setting,
        "fish_setting": fish_setting,
        "battle_setting": battle_setting,
    }
    pretty_log(
        message=f"Updated timer cache for user {user_id} ({user_name})",
        label="⌚ TIMER CACHE",
    )

def update_pokemon_setting_in_cache(user_id: int, pokemon_setting: str):
    """
    Update only the pokemon_setting field in the timer cache for a specific user.
    """
    if user_id in timer_cache:
        timer_cache[user_id]["pokemon_setting"] = pokemon_setting
        pretty_log(
            message=f"Updated pokemon_setting in timer cache for user {user_id} to {pokemon_setting}",
            label="⌚ TIMER CACHE",
        )

def update_battle_setting_in_cache(user_id: int, battle_setting: str):
    """
    Update only the battle_setting field in the timer cache for a specific user.
    """
    if user_id in timer_cache:
        timer_cache[user_id]["battle_setting"] = battle_setting
        pretty_log(
            message=f"Updated battle_setting in timer cache for user {user_id} to {battle_setting}",
            label="⌚ TIMER CACHE",
        )
