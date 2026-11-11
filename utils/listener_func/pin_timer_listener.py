import re

import discord

from utils.database.pokemeow_timers import fetch_timer, fetch_timer_due, upsert_pokemeow_timer

from utils.essentials.pokemeow_helpers import get_pokemeow_reply_member
from utils.listener_func.special_battle_npc_listener import (
    _safe_add_reaction_to_reference,
)
from utils.loggers.pretty_logs import pretty_log

TIMER_TYPE = "pin_answer"
REACTION_EMOJI = "📅"


# Extracts the timestamp from a string like '<t:1766190355:R>'


def extract_timestamp_from_message(message: discord.Message) -> int | None:
    content = message.content

    for embed in message.embeds:
        content += f"\n{embed.title or ''}\n{embed.description or ''}"
        for field in embed.fields:
            content += f"\n{field.name}\n{field.value}"

    match = re.search(r"<t:(\d+):[A-Za-z]>", content)
    return int(match.group(1)) if match else None


async def pin_timer_listener(bot: discord.Client, message: discord.Message):
    """Listens for special battle NPC timer messages and updates the database accordingly."""
    member = await get_pokemeow_reply_member(message)
    if not member:
        return

    user_id = member.id
    user_name = member.name
    channel_id = message.channel.id
    timer_type = TIMER_TYPE

    # Extract timestamp
    ends_on = extract_timestamp_from_message(message)
    if not ends_on:
        return

    existing_timer = await fetch_timer(bot, user_id, timer_type)
    if existing_timer:
        # Check if different
        if existing_timer["remind_on"] != ends_on:
            # Update the timer
            await upsert_pokemeow_timer(
                bot,
                user_id,
                user_name,
                timer_type,
                channel_id,
                message.channel.name,
                ends_on,
            )
            pretty_log(
                "info",
                f"Updated pin answer timer for {user_name}, ends_on {ends_on}",
            )
            await _safe_add_reaction_to_reference(
                bot=bot,
                message=message,
                reaction_emoji=REACTION_EMOJI,
            )
        elif existing_timer["remind_on"] == ends_on:
            pretty_log(
                "info",
                f"No update needed for pin answer timer for {user_name}, ends_on {ends_on}",
            )
    else:
        # Insert new timer
        await upsert_pokemeow_timer(
            bot,
            user_id,
            user_name,
            timer_type,
            channel_id,
            message.channel.name,
            ends_on,
        )
        await _safe_add_reaction_to_reference(
            bot=bot,
            message=message,
            reaction_emoji=REACTION_EMOJI,
        )
        pretty_log(
            "info",
            f"Inserted new pin answer timer for {user_name}, ends_on {ends_on}",
        )
