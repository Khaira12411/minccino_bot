import asyncio

import discord

from utils.database.pokemeow_timers import fetch_all_due_timers, remove_pokemeow_timer
from utils.essentials.retry_function import _retry_discord_call
from utils.loggers.pretty_logs import pretty_log

TIMER_MAP = {"pin_answer": "you can now guess the pin again!"}

_POKEMEOW_TIMER_CHECKER_LOCK = asyncio.Lock()


# 🍭 Background task to check pokemeow timers
async def pokemeow_timer_checker(bot: discord.Client):
    """Background task to check and notify about pokemeow timers."""

    if _POKEMEOW_TIMER_CHECKER_LOCK.locked():
        pretty_log(
            "warn",
            "Pokemeow timer checker is already running; skipping overlapping run",
        )
        return

    async with _POKEMEOW_TIMER_CHECKER_LOCK:
        await _process_due_pokemeow_timers(bot)


async def _process_due_pokemeow_timers(bot: discord.Client):
    """Send due timer notifications while the checker lock is held."""

    # Fetch due pokemeow timers
    due_timers = await fetch_all_due_timers(bot)
    if not due_timers:
        return  # No due timers

    for timer in due_timers:
        user_id = timer["user_id"]
        timer_type = timer["timer_type"]
        channel_id = timer["channel_id"]

        # Notify the user in the specified channel
        channel = bot.get_channel(channel_id)
        if channel:
            member = channel.guild.get_member(user_id)
            if member:
                # Remove timer from database
                content = f"⏲️ {member.mention}, {TIMER_MAP.get(timer_type, '')}"
                embed = None
                try:
                    await _retry_discord_call(
                        channel.send, content=content, embed=embed
                    )
                    pretty_log(
                        "info",
                        f"Notified {member.name} about pokemeow timer for {timer_type} and removed from database",
                    )
                    await remove_pokemeow_timer(bot, user_id, timer_type)
                except Exception as e:
                    pretty_log(
                        "warn",
                        f"Failed to notify {member.name} for {timer_type}: {e}",
                    )
            else:
                await remove_pokemeow_timer(bot, user_id, timer_type)
                pretty_log(
                    "warn",
                    f"Member not found in guild {channel.guild.id} for notifying about pokemeow timer for {timer_type}",
                )

        else:
            await remove_pokemeow_timer(bot, user_id, timer_type)
            pretty_log(
                "warn",
                f"Channel {channel_id} not found for notifying about pokemeow timer for {timer_type}",
            )
