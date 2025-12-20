import re

import discord

from config.aesthetic import Emojis
from utils.database.misc_pokemeow_reminders_db import (
    fetch_secret_santa_reminder,
    insert_secret_santa_reminder,
    update_secret_santa_reminder,
    upsert_secret_santa_reminder,
)
from utils.essentials.pokemeow_helpers import get_pokemeow_reply_member
from utils.loggers.pretty_logs import pretty_log

REACTION_EMOJI = Emojis.santa_mouse


def extract_timestamp(message: str) -> int | None:
    """
    Extracts the Unix timestamp from a message containing a Discord timestamp tag like <t:1766135362:f>.
    Returns the timestamp as an integer, or None if not found.
    """
    match = re.search(r"<t:(\d+):[a-zA-Z]>", message)
    if match:
        return int(match.group(1))
    return None


# 🍭 Listener for Secret Santa participation
async def secret_santa_listener(bot: discord.Client, message: discord.Message):
    """
    Listener that triggers when a user participates in Secret Santa.
    Sets a reminder for 4 hours later.
    """

    member = await get_pokemeow_reply_member(message)
    if not member:
        return
    user_id = member.id
    user_name = member.name
    channel_id = message.channel.id

    # Upsert Secret Santa reminder for 4 hours later
    await upsert_secret_santa_reminder(bot, user_id, user_name, channel_id)
    await message.reference.resolved.add_reaction(
        REACTION_EMOJI
    )  # React with Santa emoji to confirm participation


async def secret_santa_timer_listener(bot: discord.Client, message: discord.Message):
    """
    Listener that triggers when a user participates in Secret Santa.
    Sets a reminder for 4 hours later.
    """

    member = await get_pokemeow_reply_member(message)
    if not member:
        return
    user_id = member.id
    user_name = member.name
    channel_id = message.channel.id

    # Fetch timestamp from message
    timestamp = extract_timestamp(message.content)
    if not timestamp:
        return

    # Fetch existing reminder
    existing_reminder = await fetch_secret_santa_reminder(bot, user_id)
    if existing_reminder:
        # Check if existing reminder is same as extracted timestamp
        if existing_reminder.get("remind_on") == timestamp:
            pretty_log(
                "info",
                f"User {user_name} ({user_id}) already has a Secret Santa reminder set for {timestamp}. No action taken.",
            )
            return
        else:
            # Update existing reminder with new timestamp
            await update_secret_santa_reminder(bot, user_id, user_name, timestamp)
            pretty_log(
                "info",
                f"Updated Secret Santa reminder for {user_name} ({user_id}) to new timestamp {timestamp}.",
            )
            await message.reference.resolved.add_reaction(
                REACTION_EMOJI
            )  # React with Santa emoji to confirm participation
            return

    # Upsert Secret Santa reminder for 4 hours later
    await insert_secret_santa_reminder(bot, user_id, user_name, timestamp, channel_id)
    await message.reference.resolved.add_reaction(
        REACTION_EMOJI
    )  # React with Santa emoji to confirm participation
