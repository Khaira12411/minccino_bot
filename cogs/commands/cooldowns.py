# utils/commands/feeling_lucky.py
import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime


from config.aesthetic import *
from utils.loggers.pretty_logs import pretty_log
from config.current_setup import MINCCINO_COLOR

class FeelingLucky(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # ─────────────────────────────
    # /cooldowns command
    # ─────────────────────────────
    @app_commands.command(
        name="cooldowns", description="Check your Feeling Lucky cooldowns"
    )
    async def cooldowns(self, interaction: discord.Interaction):
        from utils.cache.fl_cache import feeling_lucky_cache

        user_id = interaction.user.id
        data = feeling_lucky_cache.get(user_id)

        if not data:
            desc = (
                "🍀 You have no active Feeling Lucky cooldown! You can use `;find` now."
            )
        else:
            cooldown_until = data.get("cooldown_until", 0)
            now = int(datetime.now().timestamp())
            if now >= cooldown_until:
                desc = "🍀 Your Feeling Lucky cooldown has expired! You can use `;find` now."
            else:
                # Show relative timestamp
                desc = (
                    f"🍀 You can use `;find` again <t:{cooldown_until}:R> "
                    f"({datetime.fromtimestamp(cooldown_until).strftime('%H:%M:%S')})"
                )

        embed = discord.Embed(
            title="Feeling Lucky Cooldown", description=desc, color=MINCCINO_COLOR
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)


# ─────────────────────────────
# Cog setup
# ─────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(FeelingLucky(bot))
