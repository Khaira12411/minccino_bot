import asyncio
import re

import discord

from config.aesthetic import Emojis
from config.current_setup import HANA_USER_ID, KHY_USER_ID
from utils.essentials.pokemeow_helpers import get_pokemeow_reply_member
from utils.loggers.debug_log import debug_log, enable_debug
from utils.loggers.pretty_logs import pretty_log

enable_debug(f"{__name__}.egg_ready_to_hatch_listener")
enable_debug(f"{__name__}.egg_hatched_listener")
OWNER_IDS = [KHY_USER_ID, HANA_USER_ID]


def extract_user_id(message: str) -> int | None:
    match = re.search(r"<@(\d+)>", message)
    if match:
        return match.group(1).strip()
    return None


async def egg_ready_to_hatch_listener(bot: discord.Client, message: discord.Message):
    """
    Listens for egg hatching messages and adds a reaction.
    """
    user_id = extract_user_id(message.content)
    debug_log(f"Extracted user ID: {user_id}")
    if not user_id:
        debug_log("No user ID found in the message.")
        return
    if user_id not in OWNER_IDS:
        debug_log(f"User ID {user_id} not in OWNER_IDS.")
        return

    user = bot.get_user(user_id)
    debug_log(f"Fetched user: {user}")
    if not user:
        debug_log(f"User with ID {user_id} not found.")
        return

    content = f"{Emojis.egg_shake}, **{user.name}**  Use </egg hatch:1015311084594405485> to hatch your egg! "
    await message.channel.send(content)

    pretty_log(
        "info",
        f"Egg hatch listener triggered for user {user_id} in channel {message.channel.id}",
    )


async def egg_hatched_listener(bot: discord.Client, message: discord.Message):
    """
    Listens for egg hatched messages and sends a congratulatory message.
    """
    embed = message.embeds[0] if message.embeds else None
    member = await get_pokemeow_reply_member(message)
    debug_log(f"Fetched member: {member}")
    if not member:
        debug_log("No member found from the Pokemeow reply.")
        return
    member_id = member.id
    if member_id not in OWNER_IDS:
        debug_log(f"Member ID {member_id} not in OWNER_IDS.")
        return
    # Delay 1 second
    await asyncio.sleep(1)
    content = f"{Emojis.egg}, **{member.name}**  Use </egg hold:1015311084594405485> to hold another egg!"
    await message.channel.send(content)
    pretty_log(
        "info",
        f"Egg hatched listener triggered for user {member_id} in channel {message.channel.id}",
    )
