# cogs/commands/settings_command.py

import discord
from discord import app_commands
from discord.ext import commands

from utils.cache.ball_reco_cache import ball_reco_cache
from utils.cache.cache_list import timer_cache
from utils.cache.held_item_cache import held_item_cache
from utils.cache.reminders_cache import user_reminders_cache
from utils.cache.res_fossil_cache import res_fossils_alert_cache
from utils.cache.user_captcha_alert_cache import user_captcha_alert_cache
from utils.embeds.user_settings_embed import build_user_settings_embed
from utils.essentials.loader.loader import *
from utils.essentials.role_checks import *
from utils.loggers.pretty_logs import pretty_log


# -------------------- Cache reload helpers --------------------
async def reload_timer_cache(bot: commands.Bot):
    from utils.cache.timers_cache import load_timer_cache

    await load_timer_cache(bot=bot)


async def reload_ball_reco_cache(bot: commands.Bot):
    from utils.cache.ball_reco_cache import load_ball_reco_cache

    await load_ball_reco_cache(bot=bot)


async def reload_held_item_cache(bot: commands.Bot):
    from utils.cache.held_item_cache import load_held_item_cache

    await load_held_item_cache(bot=bot)


async def reload_reminders_cache(bot: commands.Bot):
    from utils.cache.reminders_cache import load_user_reminders_cache

    await load_user_reminders_cache(bot=bot)


async def reload_captcha_alert_cache(bot: commands.Bot):
    from utils.cache.user_captcha_alert_cache import load_user_captcha_alert_cache

    await load_user_captcha_alert_cache(bot=bot)


async def reload_res_fossil_cache(bot: commands.Bot):
    from utils.cache.res_fossil_cache import load_res_fossils_alert_cache

    await load_res_fossils_alert_cache(bot=bot)


# -------------------- Dropdown for settings --------------------
class SettingsDropdown(discord.ui.Select):
    def __init__(self, user_id: int, bot: commands.Bot):
        options = [
            discord.SelectOption(label="Timer", value="timer"),
            discord.SelectOption(label="Alerts", value="alerts"),
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
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        # 💜 Pretty defer
        defer_handle = await pretty_defer(
            interaction, content="Fetching your settings..."
        )

        try:
            user_id = self.user_id
            category = self.values[0]

            # --- Fetch cached data & reload if missing ---
            data = None
            if category == "timer":
                data = timer_cache.get(user_id)
                if not data:
                    await reload_timer_cache(self.bot)
                    data = timer_cache.get(user_id)
            elif category == "captcha_alert":
                data = user_captcha_alert_cache.get(user_id)
                if not data:
                    await reload_captcha_alert_cache(self.bot)
                    data = user_captcha_alert_cache.get(user_id)

            elif category == "ball_reco":
                data = ball_reco_cache.get(user_id)
                if not data:
                    await reload_ball_reco_cache(self.bot)
                    data = ball_reco_cache.get(user_id)
            elif category == "held_items":
                data = held_item_cache.get(user_id)
                if not data:
                    await reload_held_item_cache(self.bot)
                    data = held_item_cache.get(user_id)
            elif category == "reminders":
                data = user_reminders_cache.get(user_id)
                if not data:
                    await reload_reminders_cache(self.bot)
                    data = user_reminders_cache.get(user_id)
            elif category == "alerts":
                captcha_data = user_captcha_alert_cache.get(user_id)
                if not captcha_data:
                    await reload_captcha_alert_cache(self.bot)
                    captcha_data = user_captcha_alert_cache.get(user_id)
                res_fossil_data = res_fossils_alert_cache.get(user_id)
                if not res_fossil_data:
                    await reload_res_fossil_cache(self.bot)
                    res_fossil_data = res_fossils_alert_cache.get(user_id)
                data = {
                    "captcha_alert": captcha_data,
                    "res_fossil_alert": res_fossil_data,
                }

            if not data:
                await defer_handle.stop(
                    content="❌ No data found for you. Try again in a moment.",
                    embed=None,
                )
                return

            # --- Build embed & stop loader ---
            embed = build_user_settings_embed(interaction.user, category, data)
            await defer_handle.stop(embed=embed, content=None)

        except Exception as e:
            pretty_log(
                "error",
                f"Failed to send settings embed for user {interaction.user.id} | {e}",
            )
            await defer_handle.stop(
                content="❌ Failed to load your settings.", embed=None
            )


# -------------------- View --------------------
class SettingsView(discord.ui.View):
    def __init__(self, user_id: int, bot: commands.Bot):
        super().__init__()
        self.add_item(SettingsDropdown(user_id, bot))


# -------------------- Cog --------------------
class SettingsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="settings", description="View your current settings")
    @espeon_roles_only()
    async def settings(self, interaction: discord.Interaction):
        """Send select menu to pick settings category"""
        # 💜 Pretty defer
        defer_handle = await pretty_defer(
            interaction, content="Preparing your settings..."
        )

        try:
            view = SettingsView(interaction.user.id, self.bot)
            await defer_handle.stop(
                content="Select a category to view your settings:", embed=None
            )
            await interaction.followup.send(view=view, ephemeral=True)
        except Exception as e:
            pretty_log(
                "error",
                f"Failed to send settings menu for user {interaction.user.id} | {e}",
            )
            await defer_handle.stop(
                content="❌ Failed to load your settings menu.", embed=None
            )


# -------------------- Setup --------------------
async def setup(bot: commands.Bot):
    await bot.add_cog(SettingsCog(bot))
