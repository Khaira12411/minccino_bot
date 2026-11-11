import discord

from utils.database.catchlist_db import reset_all_catchlist
from utils.loggers.pretty_logs import pretty_log

# 🍥──────────────────────────────────────────────
#   Monthly Catchlist Reset Task
# 🍥──────────────────────────────────────────────
async def monthly_catchlist_reset(bot: discord.Client):
    await reset_all_catchlist(bot)
    pretty_log("info", "Monthly catchlist reset completed.")
