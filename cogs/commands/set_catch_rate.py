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


class BallSettings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="set-catch-rate",
        description="Set your catch rate bonus and Patreon status",
    )
    @app_commands.describe(
        catch_rate="Enter a number between 0 and 100",
        is_patreon="Are you a Patreon member?",
    )
    @espeon_roles_only()
    async def set_catch_rate(
        self,
        interaction: discord.Interaction,
        catch_rate: float,
        is_patreon: bool,
    ):
        from utils.cache.ball_reco_cache import load_ball_reco_cache

        # Validate catch rate
        if catch_rate < 0 or catch_rate > 100:
            await interaction.response.send_message(
                "❌ Catch rate must be between 0 and 100.", ephemeral=True
            )
            return

        handle = await pretty_defer(interaction, content="💾 Saving your settings...")

        try:
            existing = await fetch_user_rec(self.bot, interaction.user.id)
            if existing:
                await upsert_user_rec(
                    self.bot,
                    user_id=interaction.user.id,
                    user_name=str(interaction.user),
                    catch_rate_bonus=catch_rate,
                    is_patreon=is_patreon,
                    held_items=existing.get("held_items", {}),
                    pokemon=existing.get("pokemon", {}),
                    fishing=existing.get("fishing", {}),
                )
            else:
                await upsert_user_rec(
                    self.bot,
                    user_id=interaction.user.id,
                    user_name=str(interaction.user),
                    catch_rate_bonus=catch_rate,
                    is_patreon=is_patreon,
                )
            await load_ball_reco_cache(self.bot)
            embed = discord.Embed(
                title="🎯 Catch Rate Settings Saved! 🎯",
                color=0xA78BFA,  # Cute purple
            )
            embed.add_field(
                name="Catch Rate Bonus", value=f"{catch_rate}%", inline=True
            )
            embed.add_field(
                name="Patreon Status",
                value="💜 Yes" if is_patreon else "💛 No",
                inline=True,
            )
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
