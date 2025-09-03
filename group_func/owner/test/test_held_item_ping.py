# 🍃───────────────────────────────────────
#              Command Name Command
# 🍃───────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands

from utils.listener_func.held_item_ping import held_item_ping_handler


async def test_held_item_ping_func(
    bot: commands.Bot, interaction: discord.Interaction, pokemon: str
):
    # Create a mock embed like PokeMeow spawn
    desc = f"<:chamber_waitress_nicki:1372944838093312111>  **{interaction.user.name}** found a wild <:held_item:1375498561298628628><:574:721591013952716843><:dexcaught:667082939632189451>**{pokemon}**!"
    embed = discord.Embed(description=desc)

    # Build a fake message object to feed the handler
    class FakeMessage:
        def __init__(self):
            self.id = 0
            self.channel = interaction.channel
            self.embeds = [embed]
            self.reference = type(
                "Ref",
                (),
                {"resolved": type("Orig", (), {"author": interaction.user})()},
            )()

    fake_msg = FakeMessage()

    # Call your held_item_ping_handler directly
    await held_item_ping_handler(bot, fake_msg)

    await interaction.response.send_message(
        f"Mock held item ping triggered for {pokemon}", ephemeral=True
    )
