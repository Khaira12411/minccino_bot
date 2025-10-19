import discord
from utils.loggers.pretty_logs import pretty_log

from utils.database.daily_fa_ball import clear_daily_faction_ball
from utils.database.hallowen_contest_top_db import clear_halloween_con_top
# 🍥──────────────────────────────────────────────
#   Daily Faction Ball Reset Task
# 🍥──────────────────────────────────────────────
async def daily_ball_reset(bot):
    """Resets the daily faction ball data."""
    try:
        await clear_daily_faction_ball(bot)
        pretty_log(
            tag="background_task",
            message="Daily faction ball data has been reset.",
            bot=bot,
        )
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to reset daily faction ball data: {e}",
            bot=bot,
        )

    #todo remove after november 7
    try:
        await clear_halloween_con_top(bot)
        pretty_log(
            tag="background_task",
            message="Halloween contest top data has been cleared.",
            bot=bot,
        )
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to clear halloween contest top data: {e}",
            bot=bot,
        )
