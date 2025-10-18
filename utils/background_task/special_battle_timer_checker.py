import discord

from config.aesthetic import Emojis
from utils.database.special_npc_timer_db_func import (
    fetch_due_special_battle_timers,
    remove_special_battle_timer,
)
from utils.loggers.pretty_logs import pretty_log


# 🍭 Background task to check special battle timers
async def special_battle_timer_checker(bot: discord.Client):
    """Background task to check and notify about special battle timers."""
    due_timers = await fetch_due_special_battle_timers(bot)
    if not due_timers:
        return  # No due timers

    for timer in due_timers:
        user_id = timer["user_id"]
        npc_name = timer["npc_name"]
        channel_id = timer["channel_id"]

        # Notify the user in the specified channel
        channel = bot.get_channel(channel_id)
        if channel:
            member = channel.guild.get_member(user_id)
            if member:
                # Remove timer from database
                content = f"{Emojis.brown_coffee} {member.mention}, you can now battle {npc_name.title()} again!"
                desc = f";b npc {npc_name}"
                embed = discord.Embed(description=desc, color=0xC1B1A5)
                try:
                    await channel.send(content=content, embed=embed)
                    pretty_log(
                        "info",
                        f"Notified user {user_id} about special battle timer for npc {npc_name} and removed from database",
                    )
                    await remove_special_battle_timer(bot, user_id, npc_name)
                except Exception as e:
                    pretty_log(
                        "warn",
                        f"Failed to notify user {user_id} for npc {npc_name}: {e}",
                    )
            else:
                pretty_log(
                    "warn",
                    f"Member {user_id} not found in guild {channel.guild.id} for notifying about special battle timer for npc {npc_name}",
                )

        else:
            pretty_log(
                "warn",
                f"Channel {channel_id} not found for notifying user {user_id} about special battle timer for npc {npc_name}",
            )
