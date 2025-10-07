from datetime import datetime

from config.aesthetic import Image_Link
from config.straymons_constants import STRAYMONS__TEXT_CHANNELS
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

    goal_tracker_channel = bot.get_channel(STRAYMONS__TEXT_CHANNELS.goal_tracker)
    if goal_tracker_channel:
        await goal_tracker_channel.send(content=Image_Link.new_week)

    # Log the reset
    pretty_log(
        "info",
        "Weekly goals have been reset in the database and cache.",
        label="💠 WEEKLY GOAL RESET",
        bot=bot,
    )
