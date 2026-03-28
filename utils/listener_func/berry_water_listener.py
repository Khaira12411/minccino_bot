import re
import discord
from config.current_setup import KHY_USER_ID
from utils.database.berry_reminder import (
    fetch_user_all_berry_reminder,
    upsert_berry_reminder,
)
from utils.essentials.pokemeow_helpers import get_pokemeow_reply_member
from utils.loggers.debug_log import debug_log, enable_debug
from utils.loggers.pretty_logs import pretty_log
from config.straymons_constants import STRAYMONS__TEXT_CHANNELS
from config.aesthetic import *
enable_debug(f"{__name__}.handle_berry_water_message")
enable_debug(f"{__name__}.handle_growth_mulch_message")
def parse_berry_water_message(message: str):
    """
    Extracts slot_number, berry_name, stage, and reminds_on from a berry water message.
    Returns a dict or None if not matched.
    """
    # Slot number and berry name
    slot_match = re.search(
        r"Slot (\d+)[^\\n]*?([A-Za-z ]+):.*?[*]{2}([A-Za-z ]+)[*]{2}", message
    )
    # Stage
    stage_match = re.search(r"\*\*([A-Za-z ]+)\*\* \((\d+)/\d+\)", message)
    # Reminds_on (timestamp)
    reminds_on_match = re.search(r"at <t:(\d+):F>", message)

    if not (slot_match and stage_match and reminds_on_match):
        return None

    slot_number = int(slot_match.group(1))
    berry_name = slot_match.group(3).strip()
    stage = stage_match.group(1).strip()
    reminds_on = int(reminds_on_match.group(1))

    return {
        "slot_number": slot_number,
        "berry_name": berry_name,
        "stage": stage,
        "reminds_on": reminds_on,
    }


async def handle_berry_water_message(bot, message):

    debug_log(f"Handling berry water message: {message.content}")
    member = await get_pokemeow_reply_member(message)
    if not member:
        debug_log("No member found in pokemeow reply.")
        return
    user_id = member.id
    guild = message.guild

    parsed_data = parse_berry_water_message(message.content)
    if not parsed_data:
        debug_log("Message did not match berry water format.")
        return
    debug_log(f"Parsed berry water message: {parsed_data}")

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

    # Upsert the berry reminder in the database
    try:
        await upsert_berry_reminder(
            bot,
            user_id=user_id,
            user_name=user_name,
            slot_number=parsed_data["slot_number"],
            remind_on=parsed_data["reminds_on"],
            stage=parsed_data["stage"],
            channel_id=member_channel_id,
            channel_name=member_channel_name,
            berry_name=parsed_data["berry_name"],
        )
        pretty_log(
            "db",
            f"Upserted berry reminder for {user_name} (user_id: {user_id}) in slot {parsed_data['slot_number']}, reminds on {parsed_data['reminds_on']}, stage: {parsed_data['stage']}",
        )
        replied_message = message.reference and message.reference.resolved
        if replied_message:
            # Reaction emoji (you can customize this)
            reaction_emoji = Emojis.brown_check
            try:
                await replied_message.add_reaction(reaction_emoji)
                debug_log(
                    f"Added reaction {reaction_emoji} to message ID {replied_message.id}"
                )
            except Exception as e:
                debug_log(
                    f"Failed to add reaction to message ID {replied_message.id}: {e}"
                )

    except Exception as e:
        pretty_log(
            "warn",
            f"Failed to upsert berry reminder for user {user_id} in slot {parsed_data['slot_number']}: {e}",
        )

async def handle_growth_mulch_message(bot, message):
    debug_log(f"Handling growth mulch message: {message.content}")
    member = await get_pokemeow_reply_member(message)
    if not member:
        debug_log("No member found in pokemeow reply.")
        return
    user_id = member.id
    guild = message.guild

    if user_id != KHY_USER_ID:
        debug_log(f"Message from user_id {user_id} is not Khy{KHY_USER_ID}. Ignoring.")
        return

    content = f"{member.mention} please use `;berry` so I can update your next berry stage reminder!"
    await message.channel.send(content)
