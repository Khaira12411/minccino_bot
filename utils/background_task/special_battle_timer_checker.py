import discord

from config.aesthetic import Emojis
from utils.database.special_npc_timer_db_func import (
    fetch_due_special_battle_timers,
    remove_special_battle_timer,
)
from utils.loggers.pretty_logs import pretty_log

# 🍭 Helper function to fetch spooky_hour row
async def fetch_spooky_hour(bot: discord.Client):
    """
    Fetches the spooky_hour row.
    Returns a dict with ends_on and message_id, or None if not found.
    """
    query = "SELECT ends_on, message_id FROM spooky_hour LIMIT 1"
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(query)
        if row:
            return {"ends_on": row["ends_on"], "message_id": row["message_id"]}
        return None
    except Exception as e:
        pretty_log(
            "error",
            f"Failed to fetch spooky_hour row: {e}",
        )
        return None


# 🍭 Background task to check special battle timers
async def special_battle_timer_checker(bot: discord.Client):
    """Background task to check and notify about special battle timers."""

    # Check if spooky hour is active
    """spooky_hour = await fetch_spooky_hour(bot)
    if not spooky_hour:
        return  # Spooky hour not active"""

    # Fetch due special battle timers
    due_timers = await fetch_due_special_battle_timers(bot)
    if not due_timers:
        return  # No due timers

    for timer in due_timers:
        user_id = timer["user_id"]
        npc_name = timer["npc_name"]
        channel_id = timer["channel_id"]

        # Notify the user in the specified channel
        channel = bot.get_channel(channel_id)
        display_npc_name = npc_name.replace("_", " ").title()
        if channel:
            member = channel.guild.get_member(user_id)
            if member:
                # Remove timer from database
                content = f"{Emojis.battle_spawn} {member.mention}, you can now battle {display_npc_name} again!"
                desc = f";b npc {npc_name}"
                embed = discord.Embed(description=desc, color=0xC1B1A5)
                try:
                    await channel.send(content=content, embed=embed)
                    pretty_log(
                        "info",
                        f"Notified member.name about special battle timer for npc {npc_name} and removed from database",
                    )
                    await remove_special_battle_timer(bot, user_id, npc_name)
                except Exception as e:
                    pretty_log(
                        "warn",
                        f"Failed to notify {member.name} for npc {npc_name}: {e}",
                    )
            else:
                pretty_log(
                    "warn",
                    f"Member {member.name} not found in guild {channel.guild.id} for notifying about special battle timer for npc {npc_name}",
                )

        else:
            pretty_log(
                "warn",
                f"Channel {channel_id} not found for notifying {member.name} about special battle timer for npc {npc_name}",
            )
