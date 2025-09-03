# 🟣────────────────────────────────────────────
#           💜 Toggle Command Group 💜
# ─────────────────────────────────────────────
from typing import Literal

import discord
from discord import app_commands
from discord.ext import commands

from group_func.owner import *

# from utils.essentials.command_group_counter import *
from utils.essentials.command_safe import run_command_safe
from utils.essentials.role_checks import *


# 🟣────────────────────────────────────────────
#     💜 Owner Command Group Cog Setup 💜
# ─────────────────────────────────────────────
class OwnerGroup(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # 🟣────────────────────────────────────────────
    #    💜 Owner Top Level Command Group 💜
    # 🟣────────────────────────────────────────────
    owner_group = app_commands.Group(name="owner", description="Owner Command Group")

    # 🟣────────────────────────────────────────────
    #    💜 Owner Sub Command Group 💜
    # 🟣────────────────────────────────────────────
    test_group = app_commands.Group(
        name="test",
        description="Owner test commands",
    )

    # attach subgroup to parent group
    owner_group.add_command(test_group)

    # 🟣────────────────────────────────────────────
    #     💜 Owner Top level Command Group 💜
    # ─────────────────────────────────────────────
    # 🟣────────────────────────────────────────────
    #      💜 /owner extract-rarities 💜
    # 🟣────────────────────────────────────────────
    @owner_group.command(
        name="extract-rarities",
        description="Extracts and Updates rarities.py from a message link",
    )
    @app_commands.describe(
        message_link="Message link to extract the rarities from",
    )
    @khy_only()
    async def extract_rarities(
        self, interaction: discord.Interaction, message_link: str
    ):
        slash_cmd_name = "toggle test held-item-ping"

        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=extract_rarities_func,
            message_link=message_link,
        )

    extract_rarities.extras = {"category": "Owner"}

    # 🟣────────────────────────────────────────────
    #     💜 Owner Test Command Group 💜
    # ─────────────────────────────────────────────
    # 🟣────────────────────────────────────────────
    #     💜 /owner test ball-recommendation 💜
    # 🟣────────────────────────────────────────────
    @test_group.command(
        name="ball-recommendation",
        description="Mock a Pokemon, held item, or fishing spawn and test recommendation",
    )
    @app_commands.describe(
        spawn_type="Type of spawn: pokemon, held_item, or fishing",
        pokemon="Pokemon name",
        rarity="Rarity (common, uncommon, rare, superrare, legendary, shiny, golden)",
        catch_rate_bonus="Catch rate bonus for this user",
        is_patreon="Whether this user is a Patreon",
        is_exclusive="For Pokemon/held item: triggers Masterball bypass if True",
        water_state="For fishing: Water state",
    )
    @khy_only()
    async def test_recommend(
        self,
        interaction: discord.Interaction,
        spawn_type: Literal["Pokemon", "Pokemon w/ Held Item", "Fishing"],
        pokemon: str,
        rarity: Literal[
            "Common",
            "Uncommon",
            "Rare",
            "Superrare",
            "Legendary",
            "Shiny",
            "Full odds Shiny",
            "Golden",
        ],
        catch_rate_bonus: int = 0,
        is_patreon: bool = False,
        is_exclusive: bool = False,
        water_state: Literal[
            "Calm", "Moderate", "Strong", "Intense", "Special"
        ] = "calm",
    ):
        slash_cmd_name = "ball-recommendation"

        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=test_recommend_func,
            spawn_type=spawn_type,
            pokemon=pokemon,
            rarity=rarity,
            catch_rate_bonus=catch_rate_bonus,
            is_patreon=is_patreon,
            is_exclusive=is_exclusive,
            water_state=water_state,
        )

    test_recommend.extras = {"category": "Owner"}

    # 🟣────────────────────────────────────────────
    #      💜 /owner test held-item-ping 💜
    # 🟣────────────────────────────────────────────
    @test_group.command(
        name="held-item-ping",
        description="Mocks a pokemeow catch embed to test held item ping",
    )

    @app_commands.describe(
        pokemon="Pokemon name",
    )
    @khy_only()
    async def test_held_item_ping(self, interaction: discord.Interaction, pokemon: str):
        slash_cmd_name = "toggle test held-item-ping"

        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=test_held_item_ping_func,
            pokemon=pokemon,
        )

    test_held_item_ping.extras = {"category": "Owner"}


# 🟣────────────────────────────────────────────
#           💜 Cog Setup Function 💜
# ─────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = OwnerGroup(bot)
    await bot.add_cog(cog)
    owner_group = OwnerGroup.owner_group  # top-level app_commands.Group
    # await log_command_group_full_paths_to_cache(bot=bot, group=timer_group)
