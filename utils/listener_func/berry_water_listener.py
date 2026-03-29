import re

import discord

from config.aesthetic import *
from config.current_setup import KHY_USER_ID
from config.straymons_constants import STRAYMONS__TEXT_CHANNELS
from utils.database.berry_reminder import (
    fetch_user_all_berry_reminder,
    upsert_berry_reminder,
    update_mulch_info,
    get_user_berry_reminder_slot
)
from utils.essentials.pokemeow_helpers import get_pokemeow_reply_member
from utils.loggers.debug_log import debug_log, enable_debug
from utils.loggers.pretty_logs import pretty_log

enable_debug(f"{__name__}.handle_berry_water_message")
enable_debug(f"{__name__}.handle_mulch_message")


def parse_berry_water_message(message: str):
    """
    Extracts slot_number, berry_name, stage, grows_on for each berry in a berry water message.
    Also extracts the emoji name of the watering can used, if present at the top of the message.
    Returns a dict with keys: 'watering_can_emoji', 'berries' (list of dicts, one per berry).
    """
    import re

    # Try to extract watering can emoji name from the first line
    watering_can_emoji = None
    first_line = message.splitlines()[0] if message.splitlines() else ""
    emoji_match = re.match(r"<:([a-zA-Z0-9_]+):\d+>", first_line)
    if emoji_match:
        watering_can_emoji = emoji_match.group(1)
        watering_can_emoji = watering_can_emoji.replace("_", " ").strip().lower()

    # Pattern to match each berry block
    berry_blocks = re.findall(
        r"Slot (\d+)[^\\n]*?:.*?[*]{2}([A-Za-z ]+)[*]{2}.*?[*]{2}([A-Za-z ]+)[*]{2}.*?at <t:(\\d+):F>",
        message,
        re.DOTALL,
    )

    results = []
    for block in berry_blocks:
        slot_number = int(block[0])
        berry_name = block[2].strip()
        stage = block[1].strip()
        grows_on = int(block[3])
        results.append(
            {
                "slot_number": slot_number,
                "berry_name": berry_name,
                "stage": stage,
                "grows_on": grows_on,
            }
        )
    return {"watering_can_emoji": watering_can_emoji, "berries": results}


async def handle_berry_water_message(bot, message):

    debug_log(f"Handling berry water message: {message.content}")
    member = await get_pokemeow_reply_member(message)
    if not member:
        debug_log("No member found in pokemeow reply.")
        return
    user_id = member.id
    guild = message.guild

    parsed_data_list = parse_berry_water_message(message.content)
    if not parsed_data_list:
        debug_log("Message did not match berry water format.")
        return
    debug_log(f"Parsed berry water message: {parsed_data_list}")

    if user_id != KHY_USER_ID:
        debug_log(f"Message from user_id {user_id} is not Khy{KHY_USER_ID}. Ignoring.")
        return

    from utils.cache.straymon_member_cache import fetch_straymon_member_cache

    cache_info = fetch_straymon_member_cache(user_id)
    member_channel_id = (
        cache_info["channel_id"] if cache_info else STRAYMONS__TEXT_CHANNELS.kanto_park
    )
    member_channel = guild.get_channel(member_channel_id) if member_channel_id else None
    member_channel_name = member_channel.name if member_channel else None

    user_name = member.name

    # Upsert each berry reminder in the database
    for parsed_data in parsed_data_list:
        try:
            await upsert_berry_reminder(
                bot,
                user_id=user_id,
                user_name=user_name,
                slot_number=parsed_data["slot_number"],
                grows_on=parsed_data["grows_on"],
                stage=parsed_data["stage"],
                channel_id=member_channel_id,
                channel_name=member_channel_name,
                berry_name=parsed_data["berry_name"],
            )
            pretty_log(
                "db",
                f"Upserted berry reminder for {user_name} (user_id: {user_id}) in slot {parsed_data['slot_number']}, reminds on {parsed_data['grows_on']}, stage: {parsed_data['stage']}",
            )
        except Exception as e:
            pretty_log(
                "warn",
                f"Failed to upsert berry reminder for user {user_id} in slot {parsed_data['slot_number']}: {e}",
            )

    # Add reaction to the replied message (if any)
    replied_message = message.reference and message.reference.resolved
    if replied_message:
        reaction_emoji = Emojis.brown_check
        try:
            await replied_message.add_reaction(reaction_emoji)
            debug_log(
                f"Added reaction {reaction_emoji} to message ID {replied_message.id}"
            )
        except Exception as e:
            debug_log(f"Failed to add reaction to message ID {replied_message.id}: {e}")


async def handle_mulch_message(bot, message):
    debug_log(f"Handling mulch message: {message.content}")
    member = await get_pokemeow_reply_member(message)
    if not member:
        debug_log("No member found in pokemeow reply.")
        return
    user_id = member.id
    guild = message.guild

    if user_id != KHY_USER_ID:
        debug_log(f"Message from user_id {user_id} is not Khy{KHY_USER_ID}. Ignoring.")
        return
    send_message = True
    if "growth mulch" in message.content.lower():
        debug_log("Message does not contain 'growth mulch'. Ignoring.")
        content = f"{member.mention} please use `;berry` so I can update your next berry stage reminder!"
    else:
        mulch_info = extract_mulch_info_message(message.content)
        if not mulch_info:
            return
        debug_log(f"Extracted mulch info: {mulch_info}")
        slot_number = mulch_info["slot_number"]
        mulch_type = mulch_info["mulch_type"]
        # Check if slot number exists for this user in the database
        existing_reminder = await get_user_berry_reminder_slot(bot, user_id, slot_number)
        if existing_reminder:
            await update_mulch_info(bot, user_id, slot_number, mulch_type)
            send_message = False
        else:
            content = f"{member.mention} I noticed you applied {mulch_type} to slot {slot_number}, but I couldn't find that slot in my database. Please use `;berry` so I can update your reminders!"

    if send_message:
        await message.channel.send(content)


def extract_mulch_info_message(message: str):
    """
    Extracts the mulch type and slot number from a mulch application message.
    Returns a dict with keys: 'mulch_type' and 'slot_number', or None if not found.
    """
    import re

    # Example: <:gooey_mulch:1486261017691557919> Applied **Gooey Mulch** to Slot 3 (<:planted:1486510464417402960> Hondew Tree)!
    pattern = re.compile(
        r"<:([a-zA-Z0-9_]+):\d+> Applied \*\*([A-Za-z ]+)\*\* to Slot (\d+)",
        re.IGNORECASE,
    )
    match = pattern.search(message)
    if match:
        emoji_name = match.group(1)
        mulch_type = match.group(2).strip()
        slot_number = int(match.group(3))
        return {
            "mulch_type": mulch_type,
            "slot_number": slot_number,
            "emoji_name": emoji_name,
        }
    return None
