import re
import discord

from config.current_setup import KHY_USER_ID
from config.straymons_constants import STRAYMONS__TEXT_CHANNELS
from utils.database.berry_reminder import (
    fetch_user_all_berry_reminder,
    upsert_berry_reminder,
    update_water_can_type_for_slot,
)
from utils.essentials.pokemeow_helpers import get_pokemeow_reply_member
from utils.loggers.debug_log import debug_log, enable_debug
from utils.loggers.pretty_logs import pretty_log

enable_debug(f"{__name__}.handle_berry_pouch_message")
def extract_best_watering_tool_from_embed(embed) -> str:
    """
    Given a discord.Embed, finds the 'Watering Tools' field and extracts the best available watering tool.
    Hierarchy: sprayduck > spraylotad > wailmer pail.
    Returns the name of the best tool found, or None if none are available.
    """
    # Find the 'Watering Tools' field
    watering_tools_value = None
    for field in getattr(embed, "fields", []):
        if field.name and "watering tools" in field.name.lower():
            watering_tools_value = field.value
            break
    if not watering_tools_value:
        return None



    sprayduck_pattern = re.compile(
        r"<:sprayduck:[0-9]+>\s*\*\*(\d+)\*\*x", re.IGNORECASE
    )
    spraylotad_pattern = re.compile(
        r"<:spraylotad:[0-9]+>\s*\*\*(\d+)\*\*x", re.IGNORECASE
    )
    wailmer_pattern = re.compile(
        r"<:wailmer_pail:[0-9]+>\s*\*\*(\d+)\*\*x", re.IGNORECASE
    )

    sprayduck = sprayduck_pattern.search(watering_tools_value)
    spraylotad = spraylotad_pattern.search(watering_tools_value)
    wailmer = wailmer_pattern.search(watering_tools_value)

    sprayduck_count = int(sprayduck.group(1)) if sprayduck else 0
    spraylotad_count = int(spraylotad.group(1)) if spraylotad else 0
    wailmer_count = int(wailmer.group(1)) if wailmer else 0

    if sprayduck_count > 0:
        return "sprayduck"
    elif spraylotad_count > 0:
        return "spraylotad"
    elif wailmer_count > 0:
        return "wailmer_pail"
    else:
        return None


async def handle_berry_pouch_message(bot, message):
    embed = message.embeds[0] if message.embeds else None
    if not embed:
        return
    member = await get_pokemeow_reply_member(message)
    if not member:
        debug_log("No member found in pokemeow reply.")
        return
    user_id = member.id
    guild = message.guild
    if user_id != KHY_USER_ID:
        debug_log(f"Message from user_id {user_id} is not Khy{KHY_USER_ID}. Ignoring.")
        return

    # Check if she has any plants
    user_berries = await fetch_user_all_berry_reminder(bot, user_id)
    if not user_berries:
        debug_log("User has no berry reminders in the database. Ignoring.")
        return
    current_water_can_type = extract_best_watering_tool_from_embed(embed)
    if not current_water_can_type:
        debug_log("No watering tools found in embed. Ignoring.")
        return
    debug_log(f"Extracted watering tool from embed: {current_water_can_type}")
    # Update the water can type for all of the user's berry reminders if not the same
    for berry in user_berries:
        slot_number = berry["slot_number"]
        if berry["water_can_type"] != current_water_can_type:
            await update_water_can_type_for_slot(
                bot,
                user_id,
                slot_number,
                current_water_can_type,
            )
            debug_log(
                f"Updated water can type to {current_water_can_type} for user_id {user_id} in slot {slot_number}"
            )
            pretty_log(
                "db",
                f"Updated water can type to {current_water_can_type} for user_id {user_id} in slot {slot_number}",
            )
    pretty_log(
        "db",
        f"Finished processing berry pouch message for user_id {user_id}. Updated water can type to {current_water_can_type} for all slots.",
    )
