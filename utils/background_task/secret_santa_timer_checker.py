import discord

from config.aesthetic import Emojis
from config.current_setup import STRAYMONS_GUILD_ID
from config.straymons_constants import STRAYMONS__TEXT_CHANNELS
from utils.database.misc_pokemeow_reminders_db import (
    fetch_due_secret_santa_reminders,
    remove_secret_santa_reminder,
)
from utils.loggers.pretty_logs import pretty_log


async def secret_santa_timer_checker(bot: discord.Client):
    """Background task to check and notify about Secret Santa reminders."""

    # Fetch due Secret Santa reminders
    due_reminders = await fetch_due_secret_santa_reminders(bot)
    if not due_reminders:
        return  # No due reminders

    for reminder in due_reminders:
        user_id = reminder["user_id"]
        user_name = reminder["user_name"]
        channel_id = reminder["channel_id"]

        # Notify the user in the specified channel
        channel = bot.get_channel(channel_id)
        if not channel:
            straymons_guild = bot.get_guild(STRAYMONS_GUILD_ID)
            if straymons_guild:

                channel = straymons_guild.get_channel(
                    STRAYMONS__TEXT_CHANNELS.off_topic
                )

        if channel:
            member = channel.guild.get_member(user_id)
            if not member:
                # Remove Stale Reminder if member not found
                await remove_secret_santa_reminder(bot, user_id)

            if member:
                content = f"{Emojis.santa_mouse} {member.mention}, you can now do `;ss gift <amount>` again!"
                try:
                    await channel.send(content)
                    pretty_log(
                        "info",
                        f"Sent Secret Santa reminder to {user_name} in channel {channel_id}",
                    )
                except Exception as e:
                    pretty_log(
                        "warn",
                        f"Failed to send Secret Santa reminder to user {user_id}: {e}",
                    )

        # Remove reminder from database
        await remove_secret_santa_reminder(bot, user_id)
