from typing import Literal

import discord
from discord import app_commands
from discord.ext import commands

from utils.essentials.command_safe import run_command_safe
from group_func.pin_numbers import *

desc = "Pin number commands"

# 🐾────────────────────────────────────────────
#     🎐 Pin Number Command Group Cog
# 🐾────────────────────────────────────────────
class PinNumberCommandGroup(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ⚡ Top-level group (only register once!)
    pin_group = app_commands.Group(
        name="pin",
        description=desc,
    )

    # 🤍💫────────────────────────────────────────────💫🤍
    #        🎐 Pin Number Group Commands
    # 🤍💫────────────────────────────────────────────💫🤍
    # 🤍─────────────────────────────────────────────
    # 🪄 /pin edit
    # 🤍─────────────────────────────────────────────
    @pin_group.command(name="edit", description="Edits an existing pin number")
    async def edit_pin(
        self,
        interaction: discord.Interaction,
        pokemon_pin: str =None,
        fish_pin: str = None,
        safari_zone_pin: str = None,
    ):

        slash_cmd_name = "pin edit"

        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=edit_pin_numbers_func,
            pokemon_pin=pokemon_pin,
            fish_pin=fish_pin,
            safari_zone_pin=safari_zone_pin,
        )

    edit_pin.extras = {"category": "Public"}

    # 🤍─────────────────────────────────────────────
    # 🪄 /pin reset
    # 🤍─────────────────────────────────────────────
    @pin_group.command(name="reset", description="Resets all pin numbers")
    async def reset_pin(
        self,
        interaction: discord.Interaction,
    ):

        slash_cmd_name = "pin reset"

        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=reset_pin_numbers_func,
        )

    reset_pin.extras = {"category": "Public"}
    # 🤍─────────────────────────────────────────────
    # 🪄 /pin view
    # 🤍─────────────────────────────────────────────
    @pin_group.command(name="view", description="Views all pin numbers")
    async def view_pin(
        self,
        interaction: discord.Interaction,
    ):

        slash_cmd_name = "pin view"

        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=view_pin_numbers_func,
        )

    view_pin.extras = {"category": "Public"}


# 💙✨────────────────────────────────────────────✨💙
#        ✨ Pin Group Setup – Add Some Magic
# 💙✨────────────────────────────────────────────✨💙
async def setup(bot: commands.Bot):
    cog = PinNumberCommandGroup(bot)
    await bot.add_cog(cog)
