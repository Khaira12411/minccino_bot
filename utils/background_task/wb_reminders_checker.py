import discord

from config.current_setup import MINCCINO_COLOR
from utils.database.wb_fight_db import (
    fetch_due_wb_battle_reminders,
    remove_user_wb_battle_alert,
    remove_wb_reminder,
)
from utils.loggers.pretty_logs import pretty_log


async def check_wb_battle_reminders(bot: discord.Client):
    """
    Check for due world boss battle reminders and send notifications to users.
    """

    due_reminders = await fetch_due_wb_battle_reminders(bot)
    for reminder in due_reminders:
        user_id = reminder["user_id"]
        user_name = reminder["user_name"]
        wb_name = reminder["wb_name"]
        channel_id = reminder["channel_id"]
        user = bot.get_user(user_id)
        if not user:
            # Remove reminder and alert
            await remove_user_wb_battle_alert(bot, user_id)
            await remove_wb_reminder(bot, user_id)
            continue

        try:
            channel = bot.get_channel(channel_id)
            if channel:
                content = f"{user.mention}, You can now join the World Boss Battle"
                embed = discord.Embed(
                    description=";wb f",
                    color=MINCCINO_COLOR,
                )
                await channel.send(content=content, embed=embed)
                pretty_log(
                    "info",
                    f"Sent WB battle reminder to {user_name} for {wb_name}.",
                    bot=bot,
                )
            else:
                pretty_log(
                    "warn",
                    f"Channel ID {channel_id} not found for WB battle reminder of user {user_name}.",
                    bot=bot,
                )

            # Remove the reminder after sending notification
            await remove_wb_reminder(bot, user_id)

        except Exception as e:
            pretty_log(
                "error",
                f"Failed to send WB battle reminder to {user_name} for {wb_name}: {e}",
                bot=bot,
            )
