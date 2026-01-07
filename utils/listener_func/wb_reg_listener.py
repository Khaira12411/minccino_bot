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
from utils.loggers.debug_log import debug_log, enable_debug
from utils.loggers.pretty_logs import pretty_log

enable_debug(f"{__name__}.register_wb_battle_reminder")
enable_debug(f"{__name__}.world_boss_waiter")
enable_debug(f"{__name__}.start_world_boss_task")
# Structure: {boss_name: {"time": unix_seconds, "users": set(user_ids), "task": asyncio.Task, "channels": {user_id: channel}}}
wb_tasks = {}


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


async def world_boss_waiter(bot, unix_seconds, wb_name):
    debug_log(f"world_boss_waiter: Started for boss {wb_name}")
    now = int(time.time())
    seconds_until_fight = unix_seconds - now
    if seconds_until_fight <= 0:
        debug_log(
            f"world_boss_waiter: seconds_until_fight <= 0 (unix_seconds={unix_seconds}, now={now}). No wait or notification needed."
        )
        return
    try:
        await asyncio.sleep(seconds_until_fight)
    except Exception as e:
        debug_log(
            f"world_boss_waiter: Failed during asyncio.sleep for boss {wb_name}: {e}"
        )
        return
    # Notify all users registered for this boss
    task_info = wb_tasks.get(wb_name)
    if not task_info:
        debug_log(
            f"world_boss_waiter: No task info found for boss {wb_name} at notification time."
        )
        return
    for user_id in list(task_info["users"]):
        channel = task_info["channels"].get(user_id)
        user = bot.get_user(user_id)
        if not channel or not user:
            debug_log(
                f"world_boss_waiter: Channel or user not found for user_id {user_id} and boss {wb_name}"
            )
            continue
        content = (
            f"{user.mention}, You can now join the World Boss Battle for **{wb_name}**!"
        )
        embed = discord.Embed(description=";wb f", color=MINCCINO_COLOR)
        try:
            await channel.send(content=content, embed=embed)
            debug_log(
                f"world_boss_waiter: Notification sent to {user.name} in channel {channel.id} for boss {wb_name}"
            )
        except Exception as e:
            debug_log(
                f"world_boss_waiter: Failed to send notification to {user_id} in channel {getattr(channel, 'id', None)}: {e}"
            )
    # Clean up after notification
    wb_tasks.pop(wb_name, None)


async def start_world_boss_task(
    bot: discord.Client,
    unix_seconds,
    channel: discord.TextChannel,
    user: discord.User,
    wb_name: str,
    message: discord.Message,
):
    # Add user to the boss task, or create a new one if not present
    user_id = user.id
    if wb_name in wb_tasks:
        task_info = wb_tasks[wb_name]
        # If user_id is already registered for this boss, do nothing
        if user_id in task_info["users"]:
            debug_log(
                f"start_world_boss_task: User ID {user_id} already registered for boss {wb_name}, skipping."
            )
            pretty_log(
                "info",
                f"User ID {user_id} already registered for world boss reminder for {wb_name}.",
            )
            return
        # If the time is different, update if later, else ignore
        if unix_seconds > task_info["time"]:
            task_info["time"] = unix_seconds
        task_info["users"].add(user_id)
        task_info["channels"][user_id] = channel
        debug_log(
            f"start_world_boss_task: Added user ID {user_id} to existing boss task for {wb_name}"
        )
        pretty_log(
            "info",
            f"Added user ID {user_id} to existing world boss reminder for {wb_name}.",
        )
        try:
            await message.add_reaction(Emojis.calendar)
        except Exception as e:
            debug_log(
                f"start_world_boss_task: Failed to add reaction to message for user ID {user_id}: {e}"
            )
        return
    # Otherwise, create a new task for this boss
    try:
        await message.add_reaction(Emojis.calendar)
    except Exception as e:
        debug_log(
            f"start_world_boss_task: Failed to add reaction to message for user {user.name}: {e}"
        )
    try:
        wb_tasks[wb_name] = {
            "time": unix_seconds,
            "users": set([user_id]),
            "channels": {user_id: channel},
            "task": asyncio.create_task(world_boss_waiter(bot, unix_seconds, wb_name)),
        }
        pretty_log("info", f"World boss reminder task started for {wb_name}.")
        debug_log(
            f"start_world_boss_task: Task started for boss {wb_name} with user {user.name}"
        )
    except Exception as e:
        debug_log(
            f"start_world_boss_task: Failed to create world boss waiter task for boss {wb_name} and user {user.name}: {e}"
        )


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
    if not embed:
        debug_log(
            "register_wb_battle_reminder: No embed found in the message. Cannot register world boss reminder."
        )
        pretty_log("info", "No embed found in the message.")
        return
    if not embed.description:
        debug_log(
            "register_wb_battle_reminder: Embed found but no description present. Cannot extract boss info."
        )
        pretty_log("info", "No embed description found in the message.")
        return

    member = await get_pokemeow_reply_member(message)
    if not member:
        debug_log(
            "register_wb_battle_reminder: No replied member found for the message. Cannot determine user to notify."
        )
        pretty_log("info", "No replied member found for the message.")
        return

    # Check if member has their notify settings on
    from utils.cache.wb_battle_alert_cache import wb_battle_alert_cache

    alert_settings = wb_battle_alert_cache.get(member.id)
    if not alert_settings:
        debug_log(
            f"register_wb_battle_reminder: Member {member.name} has no alert settings in cache. Skipping notification."
        )
        pretty_log(
            "info",
            f"Member {member.name} has no notify settings or it's turned off.",
        )
        return
    if alert_settings.get("notify") == "off":
        debug_log(
            f"register_wb_battle_reminder: Member {member.name} has notify setting OFF. Skipping notification."
        )
        pretty_log(
            "info",
            f"Member {member.name} has no notify settings or it's turned off.",
        )
        return
    channel_id = await get_registered_personal_channel(bot, member.id)
    if not channel_id:
        debug_log(
            f"register_wb_battle_reminder: Member {member.name} has no registered personal channel. Falling back to default channel {STRAYMONS__TEXT_CHANNELS.kanto_park}."
        )
        # Fall back to one of the play channels
        channel_id = STRAYMONS__TEXT_CHANNELS.kanto_park
        pretty_log(
            "info",
            f"Member {member.name} has no registered personal channel. Using fallback channel {channel_id}.",
        )
    notify_channel = bot.get_channel(channel_id)
    if not notify_channel:
        debug_log(
            f"register_wb_battle_reminder: Notify channel ID {channel_id} not found for member {member.name}. Cannot send notification."
        )
        pretty_log(
            "info",
            f"Notify channel ID {channel_id} not found for member {member.name}.",
        )
        return

    unix_seconds = extract_wb_unix_seconds(embed.description)
    if not unix_seconds:
        debug_log(
            f"register_wb_battle_reminder: No unix seconds found in embed description: {embed.description}"
        )
        pretty_log("info", "No unix seconds found in the embed description.")
        return

    boss_name = extract_wb_boss_name(embed.description)
    if not boss_name:
        debug_log(
            f"register_wb_battle_reminder: No boss name could be extracted from embed description: {embed.description}"
        )
        pretty_log("info", "No boss name found in the embed description.")
        return

    now = int(time.time())
    seconds_until_fight = unix_seconds - now

    if seconds_until_fight <= 0:
        debug_log(
            f"register_wb_battle_reminder: World boss fight for {boss_name} is already available or in the past (unix_seconds={unix_seconds}, now={now}). No reminder scheduled."
        )
        pretty_log(
            "info",
            "World boss fight is already available or in the past. No reminder scheduled.",
        )
        return

    try:
        await start_world_boss_task(
            bot=bot,
            unix_seconds=unix_seconds,
            channel=notify_channel,
            user=member,
            wb_name=boss_name,
            message=message,
        )
        debug_log(
            f"World boss reminder registered for user {member.name} in channel {notify_channel.id} for boss {boss_name} at unix {unix_seconds}"
        )
    except Exception as e:
        debug_log(
            f"register_wb_battle_reminder: Failed to start world boss task or add reaction for user {member.name}: {e}"
        )
        pretty_log("error", f"Failed to start world boss task or add reaction: {e}")
