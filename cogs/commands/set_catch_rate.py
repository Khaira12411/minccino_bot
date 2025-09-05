import json

import discord
from discord import app_commands
from discord.ext import commands

from group_func.toggle.ball_recon.ball_recon_db_func import (
    fetch_user_rec,
    upsert_user_rec,
)
from utils.essentials.loader.loader import *
from utils.essentials.role_checks import *
from utils.loggers.pretty_logs import pretty_log

# ✅ Default schemas for all categories
DEFAULT_HELD_ITEMS = {
    "rare": False,
    "shiny": False,
    "common": False,
    "uncommon": False,
    "legendary": False,
    "superrare": False,
}
DEFAULT_POKEMON = {
    "rare": False,
    "shiny": False,
    "common": False,
    "uncommon": False,
    "legendary": False,
    "superrare": False,
}
DEFAULT_FISHING = {
    "rare": False,
    "shiny": False,
    "common": False,
    "golden": False,
    "uncommon": False,
    "legendary": False,
    "superrare": False,
}


class BallSettings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="set-catch-boost",
        description="Set your catch boost",
    )
    @app_commands.describe(
        catch_boost="Enter a number between 0 and 100 (Check ;perks for catch rate, if the channel is boosted add 5 more)",
        is_patreon="Are you a Pokemeow Patreon?",
    )
    @espeon_roles_only()
    async def set_catch_rate(
        self,
        interaction: discord.Interaction,
        catch_boost: float,
        is_patreon: bool,
    ):
        from utils.cache.ball_reco_cache import load_ball_reco_cache

        if catch_boost < 0 or catch_boost > 100:
            await interaction.response.send_message(
                "❌ Catch rate must be between 0 and 100.", ephemeral=True
            )
            return

        handle = await pretty_defer(interaction, content="💾 Saving your settings...")

        try:
            existing = await fetch_user_rec(self.bot, interaction.user.id)

            def normalize(data, defaults):
                """Merge stored data with defaults (fill missing with False)."""
                if isinstance(data, str):
                    try:
                        data = json.loads(data)
                    except json.JSONDecodeError:
                        data = {}
                if not isinstance(data, dict):
                    data = {}
                return {key: bool(data.get(key, False)) for key in defaults.keys()}

            # ✅ Ensure every schema is fully populated
            held_items = normalize(
                existing.get("held_items") if existing else {}, DEFAULT_HELD_ITEMS
            )
            pokemon = normalize(
                existing.get("pokemon") if existing else {}, DEFAULT_POKEMON
            )
            fishing = normalize(
                existing.get("fishing") if existing else {}, DEFAULT_FISHING
            )

            # Save/update user record
            await upsert_user_rec(
                self.bot,
                user_id=interaction.user.id,
                user_name=str(interaction.user),
                catch_rate_bonus=catch_boost,
                is_patreon=is_patreon,
                held_items=held_items,
                pokemon=pokemon,
                fishing=fishing,
            )

            # Reload cache
            await load_ball_reco_cache(self.bot)

            embed = discord.Embed(
                title="🎯 Catch Rate Settings Saved! 🎯",
                color=0xA78BFA,
            )
            embed.add_field(name="Catch Boost", value=f"{catch_boost}%", inline=True)
            embed.set_footer(
                text=f"Saved for {interaction.user}",
                icon_url=interaction.user.display_avatar.url,
            )

            await handle.stop(embed=embed)

        except Exception as e:
            pretty_log(
                tag="error",
                message=f"Failed to save catch rate for user {interaction.user.id}: {e}",
                label="STRAYMONS",
                bot=self.bot,
            )
            await handle.stop(
                content="❌ Failed to save your settings. Please try again later."
            )


async def setup(bot: commands.Bot):
    await bot.add_cog(BallSettings(bot))
