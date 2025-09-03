import discord
from discord import app_commands
from discord.ext import commands
from utils.loggers.pretty_logs import pretty_log
from utils.essentials.loader.loader import *
from group_func.toggle.ball_recon.ball_recon_db_func import (
    fetch_user_rec,
    upsert_user_rec,
)
from utils.essentials.role_checks import *
import json  # <-- needed for decoding JSON strings


class BallSettings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="set-catch-boost",
        description="Set your catch boost",
    )
    @app_commands.describe(
        catch_boost="Enter a number between 0 and 100 (Check ;perks for catch rate, if the channel is boosted add 5 more)",
    )
    @espeon_roles_only()
    async def set_catch_rate(
        self,
        interaction: discord.Interaction,
        catch_boost: float,
    ):
        from utils.cache.ball_reco_cache import load_ball_reco_cache

        # Validate catch rate
        if catch_boost < 0 or catch_boost > 100:
            await interaction.response.send_message(
                "❌ Catch rate must be between 0 and 100.", ephemeral=True
            )
            return

        handle = await pretty_defer(interaction, content="💾 Saving your settings...")

        try:
            existing = await fetch_user_rec(self.bot, interaction.user.id)

            # Ensure JSON fields are proper dicts
            held_items = {}
            pokemon = {}
            fishing = {}

            if existing:
                for field_name, container in [
                    ("held_items", held_items),
                    ("pokemon", pokemon),
                    ("fishing", fishing),
                ]:
                    field_data = existing.get(field_name, {})
                    if isinstance(field_data, str):
                        try:
                            container.update(json.loads(field_data))
                        except json.JSONDecodeError:
                            container.update({})
                    else:
                        container.update(field_data)

            # Save/update user record
            await upsert_user_rec(
                self.bot,
                user_id=interaction.user.id,
                user_name=str(interaction.user),
                catch_rate_bonus=catch_boost,
                is_patreon=False,
                held_items=held_items if existing else None,
                pokemon=pokemon if existing else None,
                fishing=fishing if existing else None,
            )

            # Reload cache
            await load_ball_reco_cache(self.bot)

            embed = discord.Embed(
                title="🎯 Catch Rate Settings Saved! 🎯",
                color=0xA78BFA,  # Cute purple
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
