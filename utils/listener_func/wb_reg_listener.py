import re

import discord

from config.aesthetic import Emojis
from config.straymons_constants import STRAYMONS__TEXT_CHANNELS
from utils.database.channel_db_func import get_registered_personal_channel
from utils.database.wb_fight_db import upsert_wb_battle_reminder, fetch_wb_battle_reminder
from utils.essentials.pokemeow_helpers import get_pokemeow_reply_member
from utils.loggers.pretty_logs import pretty_log


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
    unix_seconds = extract_wb_unix_seconds(embed.description)
    boss_name = extract_wb_boss_name(embed.description)

    # Check if member already has a reminder for this
    wb_reminder_info = await fetch_wb_battle_reminder(bot, member.id)
    if wb_reminder_info:
        return  # Already has a reminder

    if unix_seconds and boss_name:
        await upsert_wb_battle_reminder(
            bot,
            member,
            channel_id,
            boss_name,
            unix_seconds,
        )
        pretty_log(
            "info",
            f"Registered world boss battle reminder for {member.name} at {unix_seconds} for boss {boss_name}.",
            bot=bot,
        )
        # React a calendar to the ;wb message
        await message.add_reaction(Emojis.calendar)
