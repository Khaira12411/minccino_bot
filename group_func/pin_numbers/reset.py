import discord

from utils.database.pin_numbers_db import fetch_all_pin_numbers, remove_user_pin_numbers
from utils.essentials.loader.pretty_defer import *
from utils.listener_func.pokemon_pin_numbers_listener import create_pin_numbers_embed


async def reset_pin_numbers_func(
    bot: discord.Client,
    interaction: discord.Interaction,
):
    # Check if user has pin row
    all_pin_numbers = await fetch_all_pin_numbers(bot=bot, user_id=interaction.user.id)
    if not all_pin_numbers:
        await interaction.response.send_message(
            "You don't have any pin numbers set.", ephemeral=True
        )
        return
    loader = await pretty_defer(
        interaction=interaction, content="Resetting pin numbers...", ephemeral=False
    )
    await remove_user_pin_numbers(bot=bot, user_id=interaction.user.id)

    await loader.success(content="Pin numbers reset successfully.")
