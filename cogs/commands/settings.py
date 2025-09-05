# cogs/commands/settings_command.py

import discord
from discord import app_commands
from discord.ext import commands
from utils.cache.timers_cache import timer_cache
from utils.cache.held_item_cache import held_item_cache
from utils.cache.ball_reco_cache import ball_reco_cache
from utils.loggers.pretty_logs import pretty_log
from utils.embeds.user_settings_embed import build_user_settings_embed
from utils.essentials.role_checks import *
from utils.cache.reminders_cache import user_reminders_cache
class SettingsDropdown(discord.ui.Select):
    def __init__(self, user_id: int):
        options = [
            discord.SelectOption(label="Timer", value="timer"),
            discord.SelectOption(label="Ball Recommendation", value="ball_reco"),
            discord.SelectOption(label="Held Item Pings", value="held_items"),
            discord.SelectOption(label="Reminders", value="reminders"),
        ]
        super().__init__(
            placeholder="Choose a category...",
            min_values=1,
            max_values=1,
            options=options,
        )
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        try:
            user_id = self.user_id
            category = self.values[0]

            # Fetch cached data based on selection
            if category == "timer":
                data = timer_cache.get(user_id)
            elif category == "ball_reco":
                data = ball_reco_cache.get(user_id)
            elif category == "held_items":
                data = held_item_cache.get(user_id)
            elif category == "reminders":
                data = user_reminders_cache.get(user_id)
            else:
                data = None

            if not data:
                await interaction.response.send_message(
                    "❌ No data found for you.", ephemeral=True
                )
                return

            # Build embed using the new standalone function
            embed = build_user_settings_embed(interaction.user, category, data)
            await interaction.response.send_message(embed=embed, ephemeral=True)

        except Exception as e:
            pretty_log(
                "error",
                f"Failed to send settings embed for user {interaction.user.id} | {e}",
            )
            await interaction.response.send_message(
                "❌ Failed to load your settings.", ephemeral=True
            )


class SettingsView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__()
        self.add_item(SettingsDropdown(user_id))


class SettingsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="settings", description="View your current settings")
    @espeon_roles_only()
    async def settings(self, interaction: discord.Interaction):
        """Send select menu to pick settings category"""
        await interaction.response.send_message(
            "Select a category to view your settings:",
            view=SettingsView(interaction.user.id),
            ephemeral=True,
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(SettingsCog(bot))
