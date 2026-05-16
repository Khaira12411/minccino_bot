import asyncio
import re
import time

import discord

from config.aesthetic import Emojis
from utils.database.special_npc_timer_db_func import (
    fetch_ends_on_for_user_npc,
    get_special_battle_timer,
    upsert_special_battle_timer,
)
from utils.essentials.pokemeow_helpers import get_pokemeow_reply_member
from utils.loggers.pretty_logs import pretty_log

BATTLE_TIMER = 5 * 60  # 30 minutes in seconds
NPC_NAME = "alph_scientist"
REACTION_EMOJI = Emojis.calendar
_TRANSIENT_HTTP_STATUSES = {500, 502, 503, 504}
_MAX_REACTION_RETRIES = 3

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


async def _safe_add_reaction_to_reference(
    *,
    bot: discord.Client,
    message: discord.Message,
    reaction_emoji: str,
):
    """Add reaction to a referenced message with retries for transient Discord failures."""
    resolved_message = message.reference.resolved if message.reference else None
    if not isinstance(resolved_message, discord.Message):
        pretty_log(
            "warn",
            f"Skipping reaction for message {message.id}: missing resolved referenced message.",
            bot=bot,
        )
        return

    for attempt in range(1, _MAX_REACTION_RETRIES + 1):
        try:
            await resolved_message.add_reaction(reaction_emoji)
            return
        except discord.DiscordServerError as error:
            if attempt == _MAX_REACTION_RETRIES:
                pretty_log(
                    "warn",
                    f"Failed to add reaction after retries for message {message.id}: {error}",
                    bot=bot,
                )
                return
            await asyncio.sleep(2 ** (attempt - 1))
        except discord.HTTPException as error:
            if (
                error.status in _TRANSIENT_HTTP_STATUSES
                and attempt < _MAX_REACTION_RETRIES
            ):
                await asyncio.sleep(2 ** (attempt - 1))
                continue
            pretty_log(
                "warn",
                (
                    f"Failed to add reaction for message {message.id} "
                    f"(status={error.status}): {error}"
                ),
                bot=bot,
            )
            return


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
    npc_name = NPC_NAME

    # Extract timestamp
    ends_on = extract_timestamp_from_message(message.content)
    if not ends_on:
        return

    existing_timer = await fetch_ends_on_for_user_npc(bot, user_id, npc_name)
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
            await _safe_add_reaction_to_reference(
                bot=bot,
                message=message,
                reaction_emoji=REACTION_EMOJI,
            )
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
        await _safe_add_reaction_to_reference(
            bot=bot,
            message=message,
            reaction_emoji=REACTION_EMOJI,
        )
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
    npc_name = NPC_NAME

    # Ends on timestamp = now + BATTLE_TIMER
    ends_on = int(time.time()) + BATTLE_TIMER

    # Upsert the special battle timer
    await upsert_special_battle_timer(
        bot, user_id, user_name, npc_name, ends_on, channel_id
    )
    await _safe_add_reaction_to_reference(
        bot=bot,
        message=message,
        reaction_emoji=REACTION_EMOJI,
    )
