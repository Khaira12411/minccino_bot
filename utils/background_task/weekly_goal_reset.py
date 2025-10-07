from datetime import datetime
from utils.loggers.pretty_logs import pretty_log

# -----------------------------
# 🔹 Weekly Goal Reset Task
# -----------------------------
async def reset_weekly_goals(bot):
    """Reset the weekly_goal_tracker table and in-memory cache."""
    from utils.cache.weekly_goal_tracker_cache import (
        weekly_goal_cache,
        weekly_goal_cache_dirty,
    )
    async with bot.pg_pool.acquire() as conn:
        # Clear DB
        await conn.execute("TRUNCATE TABLE weekly_goal_tracker;")

    # Clear in-memory cache
    weekly_goal_cache.clear()
    weekly_goal_cache_dirty.clear()

    #Log the reset
    pretty_log(
        "info",
        "Weekly goals have been reset in the database and cache.",
        label="💠 WEEKLY GOAL RESET",
        bot=bot,
    )
