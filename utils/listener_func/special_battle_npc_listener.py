import re
import time

import discord

from utils.database.special_npc_timer_db_func import (
    get_special_battle_timer,
    upsert_special_battle_timer,
    fetch_ends_on_for_user_npc,
)
from utils.essentials.pokemeow_helpers import get_pokemeow_reply_member
from utils.loggers.pretty_logs import pretty_log
from config.aesthetic import Emojis
BATTLE_TIMER = 30 * 60  # 30 minutes in seconds

REACTION_EMOJI = Emojis.calendar

# Extracts the timestamp from a string like '<t:1766190355:R>'


def extract_timestamp_from_message(content: str) -> int | None:
    """
    Extracts the integer timestamp from a Discord timestamp tag in the format <t:XXXXXXXXXX:R>.
    Returns the timestamp as an int if found, otherwise None.
    """
    match = re.search(r"<t:(\d+):[A-Za-z]>", content)
    if match:
        return int(match.group(1))
    return None


async def special_battle_npc_timer_listener(
    bot: discord.Client, message: discord.Message
):
    """Listens for special battle NPC timer messages and updates the database accordingly."""
    member = await get_pokemeow_reply_member(message)
    if not member:
        return

    user_id = member.id
    user_name = member.name
    channel_id = message.channel.id
    npc_name = "xmas_blue"

    # Extract timestamp
    ends_on = extract_timestamp_from_message(message.content)
    if not ends_on:
        return

    existing_timer = await fetch_ends_on_for_user_npc(bot, user_id, "xmas_blue")
    if existing_timer:
        # Check if different
        if existing_timer != ends_on:
            # Update the timer
            await upsert_special_battle_timer(
                bot, user_id, user_name, npc_name, ends_on, channel_id
            )
            pretty_log(
                "info",
                f"Updated special battle timer for {user_name}, npc {npc_name}, ends_on {ends_on}",
            )
            await message.reference.resolved.add_reaction(REACTION_EMOJI)
        elif existing_timer == ends_on:
            pretty_log(
                "info",
                f"No update needed for special battle timer for {user_name}, npc {npc_name}, ends_on {ends_on}",
            )
    else:
        # Insert new timer
        await upsert_special_battle_timer(
            bot, user_id, user_name, npc_name, ends_on, channel_id
        )
        await message.reference.resolved.add_reaction(REACTION_EMOJI)
        pretty_log(
            "info",
            f"Inserted new special battle timer for {user_name}, npc {npc_name}, ends_on {ends_on}",
        )


# 🍭 Listener for special battle NPC timers
async def special_battle_npc_listener(bot: discord.Client, message: discord.Message):

    member = await get_pokemeow_reply_member(message)
    if not member:
        return
    user_id = member.id
    user_name = str(member)

    channel_id = message.channel.id
    npc_name = "xmas_blue"

    # Ends on timestamp = now + BATTLE_TIMER
    ends_on = int(time.time()) + BATTLE_TIMER

    # Upsert the special battle timer
    await upsert_special_battle_timer(
        bot, user_id, user_name, npc_name, ends_on, channel_id
    )
    await message.reference.resolved.add_reaction(REACTION_EMOJI)
