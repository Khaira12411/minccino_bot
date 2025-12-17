import asyncio
import re
import time

import discord

from config.aesthetic import Emojis
from config.current_setup import MINCCINO_COLOR
from config.straymons_constants import STRAYMONS__TEXT_CHANNELS
from utils.database.channel_db_func import get_registered_personal_channel
from utils.database.wb_fight_db import (
    fetch_due_wb_battle_reminders,
    fetch_wb_battle_reminder,
    remove_user_wb_battle_alert,
    remove_wb_reminder,
    upsert_wb_battle_reminder,
)
from utils.essentials.pokemeow_helpers import get_pokemeow_reply_member
from utils.loggers.pretty_logs import pretty_log

wb_task = None


def extract_wb_unix_seconds(description: str) -> int | None:
    """
    Extracts the unix seconds from the line:
    '🔹 :crossed_swords: The battle begins <t:1763620682:R>'
    """
    match = re.search(r"<t:(\d+):R>", description)
    if match:
        return int(match.group(1))
    return None


def extract_wb_boss_name(description: str) -> str | None:
    """
    Extracts the boss name from the line:
    '🔹 :crossed_swords: Boss challenge: ... Shiny Gigantamax-Copperajah'
    """
    match = re.search(r"Boss challenge: [^>]+>\s*(.+)", description)
    if match:

        boss_name = match.group(1).strip()
        if "Shiny Gigantamax" in boss_name:
            boss_name = boss_name.replace("Shiny Gigantamax-", f"{Emojis.sgmax} ")
        elif "Gigantamax" in boss_name:
            boss_name = boss_name.replace("Gigantamax-", f"{Emojis.gmax} ")
        elif "Shiny Eternamax" in boss_name:
            boss_name = boss_name.replace("Shiny Eternamax-", f"{Emojis.sgmax} ")
        elif "Eternamax" in boss_name:
            boss_name = boss_name.replace("Eternamax-", f"{Emojis.gmax} ")

        return boss_name
    return None


async def world_boss_waiter(
    bot: discord.Client,
    unix_seconds,
    channel: discord.TextChannel,
    user: discord.User,
    wb_name: str,
):
    now = int(time.time())
    seconds_until_fight = unix_seconds - now
    if seconds_until_fight > 0:
        await asyncio.sleep(seconds_until_fight)
        content = (
            f"{user.mention}, You can now join the World Boss Battle for **{wb_name}**!"
        )
        embed = discord.Embed(
            description=";wb f",
            color=MINCCINO_COLOR,
        )
        await channel.send(content=content, embed=embed)
        """# Remove the reminder after sending notification
        await remove_wb_reminder(bot, user.id)"""


async def start_world_boss_task(
    bot: discord.Client,
    unix_seconds,
    channel: discord.TextChannel,
    user: discord.User,
    wb_name: str,
    message: discord.Message,
):
    global wb_task
    # If a task is running and not done, don't start another
    if wb_task and not wb_task.done():
        pretty_log("info", "World boss reminder task already scheduled.")
        return
    await message.add_reaction(Emojis.calendar)
    wb_task = asyncio.create_task(
        world_boss_waiter(
            bot=bot,
            unix_seconds=unix_seconds,
            channel=channel,
            user=user,
            wb_name=wb_name,
        )
    )
    pretty_log("info", "World boss reminder task started.")


async def register_wb_battle_reminder(
    bot: discord.Client,
    message: discord.Message,
):
    """
    Register a world boss battle reminder for the user who sent the command.
    Extracts the boss name and unix seconds from the embed description.
    Stores the reminder in the database.
    """

    embed = message.embeds[0] if message.embeds else None
    if not embed or not embed.description:
        pretty_log("info", "No embed description found in the message.")
        return

    member = await get_pokemeow_reply_member(message)
    if not member:
        pretty_log("info", "No replied member found for the message.")
        return

    # Check if member has their notify settings on
    from utils.cache.wb_battle_alert_cache import wb_battle_alert_cache

    alert_settings = wb_battle_alert_cache.get(member.id)
    if not alert_settings or alert_settings.get("notify") == "off":
        pretty_log(
            "info",
            f"Member {member.name} has no notify settings or it's turned off.",
        )
        return
    channel_id = await get_registered_personal_channel(bot, member.id)
    if not channel_id:
        # Fall back to one of the play channels
        channel_id = STRAYMONS__TEXT_CHANNELS.kanto_park
        pretty_log(
            "info",
            f"Member {member.name} has no registered personal channel. Using fallback channel {channel_id}.",
        )
    notify_channel = bot.get_channel(channel_id)
    if not notify_channel:
        pretty_log(
            "info",
            f"Notify channel ID {channel_id} not found for member {member.name}.",
        )
        return

    unix_seconds = extract_wb_unix_seconds(embed.description)
    if not unix_seconds:
        pretty_log("info", "No unix seconds found in the embed description.")
        return
    
    boss_name = extract_wb_boss_name(embed.description)

    now = int(time.time())
    seconds_until_fight = unix_seconds - now

    if unix_seconds and boss_name and seconds_until_fight > 0:
        await start_world_boss_task(
            bot=bot,
            unix_seconds=unix_seconds,
            channel=notify_channel,
            user=member,
            wb_name=boss_name,
            message=message,
        )
