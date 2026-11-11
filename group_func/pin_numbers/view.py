import discord

from utils.database.pin_numbers_db import fetch_all_pin_numbers
from utils.essentials.loader.pretty_defer import *
from utils.listener_func.pokemon_pin_numbers_listener import create_pin_numbers_embed
from utils.loggers.debug_log import debug_log


async def view_pin_numbers_func(bot: discord.Client, interaction: discord.Interaction):
    """Sends a message with the saved pin numbers for the user."""
    user_id = interaction.user.id

    all_pin_numbers = await fetch_all_pin_numbers(bot, user_id)
    if not all_pin_numbers:
        await interaction.response.send_message("No pin numbers found.", ephemeral=True)
        return

    loader = await pretty_defer(
        interaction=interaction, content="Fetching pin numbers...", ephemeral=False
    )
    debug_log(f"All pin numbers for user {user_id}: {all_pin_numbers!r}")
    pokemon_pin = all_pin_numbers.get("pokemon_pin")
    fish_pin = all_pin_numbers.get("fish_pin")
    safari_pin = all_pin_numbers.get("sz_pin")
    debug_log(
        f"Resolved individual pin numbers for user {user_id}: pokemon_pin={pokemon_pin}, fish_pin={fish_pin}, safari_pin={safari_pin}"
    )
    footer_text = "To edit your pin numbers, use /pin edit"
    pin_numbers_embed = create_pin_numbers_embed(
        interaction.user, pokemon_pin, fish_pin, safari_pin, footer_text=footer_text
    )

    await loader.success(content="", embed=pin_numbers_embed)
