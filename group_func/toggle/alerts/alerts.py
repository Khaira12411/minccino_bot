import discord
from discord import ButtonStyle
from discord.ext import commands

from config.aesthetic import Emojis
from utils.database.captcha_alert_db_func import (
    fetch_user_captcha_alert,
    upsert_user_captcha_alert,
)
from utils.database.res_fossil_alert_db_func import (
    fetch_user_res_fossils_alert,
    upsert_user_res_fossils_alert,
)
from utils.essentials.safe_response import safe_respond
from utils.loggers.pretty_logs import pretty_log


# 💗────────────────────────────────────────────
# [🎀 FUNCTION] Alert Settings
# 💗────────────────────────────────────────────
async def alert_settings_func(bot: commands.Bot, interaction: discord.Interaction):
    """Main entry for user alert settings."""

    try:
        captcha_alert = await fetch_user_captcha_alert(bot, interaction.user.id)
        res_fossils_alert = await fetch_user_res_fossils_alert(bot, interaction.user.id)

        # ✅ Fallback defaults to prevent NoneType issues
        captcha_alert = captcha_alert or {"notify": "off"}
        res_fossils_alert = res_fossils_alert or {"notify": "off"}

        view = AlertSettingsView(
            bot, interaction.user, captcha_alert, res_fossils_alert
        )

        message = await safe_respond(
            interaction, content="Modify your Alert Settings:", view=view
        )
        view.message = message  # store reference for timeout edit

        pretty_log(
            "ui",
            f"[Alert Settings] Displayed alert settings for {interaction.user.display_name}",
        )

    except Exception as e:
        pretty_log("error", f"Failed to load alert settings: {e}")
        await safe_respond(
            interaction,
            content="⚠️ An error occurred while loading your alert settings.",
            ephemeral=True,
        )


# 💗────────────────────────────────────────────
# [💬 HELPERS]
# 💗────────────────────────────────────────────
def get_captcha_button_text(captcha_alert):
    """Returns label text for captcha button depending on current settings."""
    if not captcha_alert or not captcha_alert.get("notify", False):
        return "Captcha Alerts: OFF"
    elif captcha_alert.get("ping_helper", False):
        return "Captcha Alerts: ON w/ Helper Ping"
    else:
        return "Captcha Alerts: ON"


def get_captcha_button_style(captcha_alert):
    """Returns button color depending on current settings."""
    if not captcha_alert or not captcha_alert.get("notify", False):
        return ButtonStyle.secondary  # gray - OFF
    elif captcha_alert.get("ping_helper", False):
        return ButtonStyle.blurple  # blurple - ON w/ Helper Ping
    else:
        return ButtonStyle.success  # green - ON


# 💗────────────────────────────────────────────
# [🌸 VIEW CLASS] Alert Settings View (patched)
# 💗────────────────────────────────────────────
class AlertSettingsView(discord.ui.View):
    def __init__(
        self, bot: commands.Bot, user: discord.Member, captcha_alert, res_fossils_alert
    ):
        super().__init__(timeout=180)
        self.bot = bot
        self.user = user
        self.captcha_alert = captcha_alert
        self.res_fossils_alert = res_fossils_alert
        self.message = None  # set later
        self.update_button_styles()


    # 💫────────────────────────────────────
    # [🧩 BUTTON] Captcha Alerts (3-State Cycle)
    # 💫────────────────────────────────────
    @discord.ui.button(
        label="Captcha Alerts: OFF", style=ButtonStyle.secondary, emoji="🧩"
    )
    async def captcha_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user != self.user:
            await interaction.response.send_message(
                "You cannot interact with this button.", ephemeral=True
            )
            return

        await interaction.response.defer()
        try:
            current_state = (
                str(self.captcha_alert.get("notify", "off")).lower()
                if self.captcha_alert
                else "off"
            )

            # 🔹 Cycle the 3 states
            if current_state == "off":
                new_state = "on"
            elif current_state == "on":
                new_state = "on_with_helper_ping"
            else:
                new_state = "off"

            await upsert_user_captcha_alert(self.bot, self.user, new_state)
            self.captcha_alert = {"notify": new_state}

            # 🔹 Refresh buttons
            self.update_button_styles()

            # 🔹 Fancy readable label
            display_text = (
                "OFF"
                if new_state == "off"
                else "ON" if new_state == "on" else "ON with Captcha Helper Ping"
            )

            await interaction.edit_original_response(
                content=f"Modify your Alert Settings:\n🧩 Captcha Alerts set to **{display_text}**",
                view=self,
            )

            pretty_log(
                "ui",
                f"{self.user.display_name} set Captcha Alerts to {display_text}",
            )

        except Exception as e:
            pretty_log("error", f"Error toggling Captcha Alerts: {e}")
            await interaction.followup.send(
                "⚠️ An error occurred while updating Captcha Alerts.",
                ephemeral=True,
            )

    # 💫────────────────────────────────────
    # [🦕 BUTTON] Research Fossils Alerts
    # 💫────────────────────────────────────
    @discord.ui.button(
        label="Research Fossils: OFF", style=ButtonStyle.secondary, emoji="🦕"
    )
    async def res_fossils_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user != self.user:
            await interaction.response.send_message(
                "You cannot interact with this button.", ephemeral=True
            )
            return

        await interaction.response.defer()
        try:
            current_state = str(
                (self.res_fossils_alert and self.res_fossils_alert.get("notify", "off"))
            ).lower() in ["on", "true", "yes"]
            new_state = "off" if current_state else "on"

            await upsert_user_res_fossils_alert(self.bot, self.user, new_state)
            self.res_fossils_alert = {"notify": new_state}
            self.update_button_styles()

            await interaction.edit_original_response(
                content=f"Modify your Alert Settings:\n🦕 Research Fossils Alerts set to **{'ON' if new_state == 'on' else 'OFF'}**",
                view=self,
            )

            pretty_log(
                "ui",
                f"{self.user.display_name} {'enabled' if new_state == 'on' else 'disabled'} Research Fossils Alerts",
            )

        except Exception as e:
            pretty_log("error", f"Error toggling Research Fossils Alerts: {e}")
            await interaction.followup.send(
                "⚠️ An error occurred while updating Research Fossils Alerts.",
                ephemeral=True,
            )

    # 💫────────────────────────────────────
    # [🎨 STYLE UPDATE FUNCTION]
    # 💫────────────────────────────────────
    def update_button_styles(self):
        # 🧩 Captcha Button
        captcha_state = (
            str(self.captcha_alert.get("notify", "off")).lower()
            if self.captcha_alert
            else "off"
        )

        if captcha_state == "off":
            self.captcha_button.style = ButtonStyle.secondary
            self.captcha_button.label = "Captcha Alerts: OFF"
        elif captcha_state == "on":
            self.captcha_button.style = ButtonStyle.success
            self.captcha_button.label = "Captcha Alerts: ON"
        elif captcha_state == "on_with_helper_ping":
            self.captcha_button.style = ButtonStyle.blurple
            self.captcha_button.label = "Captcha Alerts: ON (Helper Ping)"
        else:
            self.captcha_button.style = ButtonStyle.secondary
            self.captcha_button.label = "Captcha Alerts: OFF"

        # 🦕 Research Fossils Button
        notify_val = (
            str(self.res_fossils_alert.get("notify", "off")).lower()
            if self.res_fossils_alert
            else "off"
        )
        res_enabled = notify_val in ["on", "true", "yes", "enabled", "1"]
        self.res_fossils_button.style = (
            ButtonStyle.success if res_enabled else ButtonStyle.secondary
        )
        self.res_fossils_button.label = (
            f"Research Fossils: {'ON' if res_enabled else 'OFF'}"
        )

    # 💫────────────────────────────────────
    # [⏰ TIMEOUT HANDLER]
    # 💫────────────────────────────────────
    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            if self.message:
                await self.message.edit(
                    content="⏰ Alert Settings timed out — reopen the menu to modify again.",
                    view=self,
                )
        except Exception:
            pass
