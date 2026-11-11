import discord

from utils.database.pin_numbers_db import fetch_all_pin_numbers, upsert_pin_number_type
from utils.essentials.loader.pretty_defer import *
from utils.listener_func.pokemon_pin_numbers_listener import create_pin_numbers_embed


async def edit_pin_numbers_func(
    bot: discord.Client,
    interaction: discord.Interaction,
    pokemon_pin: str | None = None,
    fish_pin: str | None = None,
    safari_zone_pin: str | None = None,
):
    # Check if the user has inputted anything
    if not any([pokemon_pin, fish_pin, safari_zone_pin]):
        await interaction.response.send_message(
            "You must provide at least one pin number to edit.", ephemeral=True
        )
        return

    loader = await pretty_defer(
        interaction=interaction, content="Editing pin numbers...", ephemeral=False
    )
    if pokemon_pin:
        await upsert_pin_number_type(
            bot=bot,
            user_id=interaction.user.id,
            user_name=interaction.user.name,
            type="pokemon",
            value=pokemon_pin,
        )
    if fish_pin:
        await upsert_pin_number_type(
            bot=bot,
            user_id=interaction.user.id,
            user_name=interaction.user.name,
            type="fish",
            value=fish_pin,
        )
    if safari_zone_pin:
        await upsert_pin_number_type(
            bot=bot,
            user_id=interaction.user.id,
            user_name=interaction.user.name,
            type="sz",
            value=safari_zone_pin,
        )

    all_pin_numbers = await fetch_all_pin_numbers(bot=bot, user_id=interaction.user.id)
    embed = create_pin_numbers_embed(
        interaction.user,
        all_pin_numbers.get("pokemon_pin") if all_pin_numbers else None,
        all_pin_numbers.get("fish_pin") if all_pin_numbers else None,
        all_pin_numbers.get("sz_pin") if all_pin_numbers else None,
        footer_text="To view your pin numbers, use !pins or /pin view",
    )
    await loader.success(content="Pin numbers updated successfully.", embed=embed)
