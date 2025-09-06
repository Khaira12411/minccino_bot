# 🟣────────────────────────────────────────────
#           💜 Toggle Command Group 💜
# ─────────────────────────────────────────────
from typing import Literal

import discord
from discord import app_commands
from discord.ext import commands

from group_func.toggle import *
from group_func.toggle.ball_recon.toggle_ball_recon import toggle_ball_rec_func
from group_func.toggle.held_item import *

# from utils.essentials.command_group_counter import *
from utils.essentials.command_safe import run_command_safe
from utils.essentials.role_checks import *


# 🟣────────────────────────────────────────────
#     💜 Toggle Command Group Cog Setup 💜
# ─────────────────────────────────────────────
class ToggleGroup(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # 🟣────────────────────────────────────────────
    #    💜 Toggle Top Level Command Group 💜
    # 🟣────────────────────────────────────────────
    toggle_group = app_commands.Group(name="toggle", description="Toggle Command Group")

    # 🟣────────────────────────────────────────────
    #    💜 Toggle Sub Command Group 💜
    # 🟣────────────────────────────────────────────
    ping_group = app_commands.Group(
        name="ping",
        description="Toggle ping commands",
    )

    # attach subgroup to parent group
    toggle_group.add_command(ping_group)

    # 🟣────────────────────────────────────────────
    #     💜 Toggle Top level Command Group 💜
    # ─────────────────────────────────────────────
    @toggle_group.command(
        name="pokemon-timer",
        description="Sets or removes your pokemon command timer",
    )
    @espeon_roles_only()
    async def timer_pokemon_set(
        self,
        interaction: discord.Interaction,
        mode: Literal["On", "On w/o pings", "React", "Off"],
    ):
        slash_cmd_name = "toggle timer-pokemon"

        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=timer_pokemon_set_func,
            mode=mode,
        )

    timer_pokemon_set.extras = {"category": "Public"}

    # 🟣────────────────────────────────────────────
    #     💜 /toggle reminders 💜
    # 🟣────────────────────────────────────────────
    @toggle_group.command(
        name="reminders",
        description="Modifies your reminders' settings",
    )
    @espeon_roles_only()
    async def toggle_reminders(
        self,
        interaction: discord.Interaction,
    ):
        slash_cmd_name = "toggle reminders"

        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=toggle_reminders_func,
        )

    toggle_reminders.extras = {"category": "Owner"}

    # 🟣────────────────────────────────────────────
    #     💜 Toggle Ping Command Group 💜
    # ─────────────────────────────────────────────
    # 🟣────────────────────────────────────────────
    #     💜 /toggle ping held-item 💜
    # 🟣────────────────────────────────────────────
    @ping_group.command(
        name="held-item",
        description="Subscribe or unsubscribe to Pokemon held item alerts",
    )
    @espeon_roles_only()
    async def toggle_held_item(
        self,
        interaction: discord.Interaction,
    ):
        slash_cmd_name = "toggle ping held-item"

        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=toggle_held_item_func,
        )

    toggle_held_item.extras = {"category": "Public"}

    # 🟣────────────────────────────────────────────
    #      💜 /toggle ping ball-recommendaton 💜
    # 🟣────────────────────────────────────────────
    @ping_group.command(
        name="ball-recommendaton",
        description="Subscribe or unsubscribe to Pokemon held item alerts",
    )
    @espeon_roles_only()
    async def toggle_ball_recon(
        self,
        interaction: discord.Interaction,
    ):
        slash_cmd_name = "toggle ping ball-recommendaton"

        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=toggle_ball_rec_func,
        )

    toggle_ball_recon.extras = {"category": "Public"}


# 🟣────────────────────────────────────────────
#           💜 Cog Setup Function 💜
# ─────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = ToggleGroup(bot)
    await bot.add_cog(cog)
    toggle_group = ToggleGroup.toggle_group  # top-level app_commands.Group
    # await log_command_group_full_paths_to_cache(bot=bot, group=timer_group)
