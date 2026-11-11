import discord
from utils.database.pin_numbers_db import fetch_all_pin_numbers, remove_user_pin_numbers

from utils.essentials.pokemeow_helpers import get_pokemeow_reply_or_interaction_member
from utils.loggers.debug_log import debug_log, enable_debug
from utils.loggers.pretty_logs import pretty_log


async def lab_pc_unlock_listener(bot: discord.Client, message: discord.Message):
    debug_log(
        f"Lab PC unlock listener triggered: message_id={message.id}, channel_id={message.channel.id}"
    )

    # Get member object
    member = await get_pokemeow_reply_or_interaction_member(message)
    debug_log(f"Resolved lab PC unlock member: {member!r}")
    if not member:
        return

    user_id = member.id
    debug_log(f"Resolved member ID: {user_id}")
    if not user_id:
        debug_log("Resolved member has no user ID; returning")
        return

    # Check if user has pin
    pin_numbers = await fetch_all_pin_numbers(bot, user_id)
    debug_log(f"Fetched pin numbers for user {user_id}: {pin_numbers}")
    if not pin_numbers:
        debug_log("User has no pin numbers; returning")
        return

    # Remove user's pin numbers after lab PC unlock
    await remove_user_pin_numbers(bot, user_id)
    debug_log(f"Removed pin numbers for user {user_id}")
    pretty_log(
        tag="info", message=f"Reset pin numbers for {member.name} after lab PC unlock"
    )
