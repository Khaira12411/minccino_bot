import discord
from utils.database.pin_numbers_db import fetch_all_pin_numbers

from utils.loggers.debug_log import debug_log

from .pokemon_pin_numbers_listener import create_pin_numbers_embed


async def pin_command_listener(bot: discord.Client, message: discord.Message):
    """Sends a message with the saved pin numbers for the user."""
    member = message.author
    user_id = member.id
    debug_log(f"Resolved member ID: {user_id}")
    if not user_id:
        debug_log("Resolved member has no user ID; returning")
        return

    all_pin_numbers = await fetch_all_pin_numbers(bot, user_id)
    debug_log(f"All pin numbers for user {user_id}: {all_pin_numbers!r}")
    pokemon_pin = all_pin_numbers.get("pokemon_pin") if all_pin_numbers else None
    fish_pin = all_pin_numbers.get("fish_pin") if all_pin_numbers else None
    safari_pin = all_pin_numbers.get("sz_pin") if all_pin_numbers else None
    debug_log(
        f"Resolved individual pin numbers for user {user_id}: pokemon_pin={pokemon_pin}, fish_pin={fish_pin}, safari_pin={safari_pin}"
    )
    footer_text = "To edit your pin numbers, use /pin-edit"
    pin_numbers_embed = create_pin_numbers_embed(
        member, pokemon_pin, fish_pin, safari_pin, footer_text=footer_text
    )

    await message.reply(embed=pin_numbers_embed)
