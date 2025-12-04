import discord
from discord import ButtonStyle
from discord.ext import commands

from config.aesthetic import Emojis
from config.straymons_constants import STRAYMONS__EMOJIS
from utils.database.captcha_alert_db_func import (
    fetch_user_captcha_alert,
    upsert_user_captcha_alert,
)
from utils.database.faction_ball_alert_db_func import (
    fetch_user_faction_ball_alert,
    upsert_user_faction_ball_alert,
)
from utils.database.halloween_contest_alert import (
    fetch_user_halloween_contest_alert,
    upsert_user_halloween_contest_alert,
)
from utils.database.res_fossil_alert_db_func import (
    fetch_user_res_fossils_alert,
    upsert_user_res_fossils_alert,
)
from utils.database.wb_fight_db import (
    fetch_user_wb_battle_alert,
    upsert_user_wb_battle_alert,
)
from utils.essentials.safe_response import safe_respond
from utils.loggers.pretty_logs import pretty_log


# 💗────────────────────────────────────────────
# [🎀 FUNCTION] Alert Settings
# 💗────────────────────────────────────────────
async def alert_settings_func(bot: commands.Bot, interaction: discord.Interaction):
    """Main entry for user alert settings."""
    try:
        await interaction.response.defer()  # Defer immediately

        captcha_alert = await fetch_user_captcha_alert(bot, interaction.user.id)
        res_fossils_alert = await fetch_user_res_fossils_alert(bot, interaction.user.id)
        faction_ball_alert = await fetch_user_faction_ball_alert(
            bot, interaction.user.id
        )
        halloween_contest_alert = await fetch_user_halloween_contest_alert(
            bot, interaction.user.id
        )
        wb_battle_alert = await fetch_user_wb_battle_alert(bot, interaction.user.id)

        # Fallback defaults
        captcha_alert = captcha_alert or {"notify": "off"}
        res_fossils_alert = res_fossils_alert or {"notify": "off"}
        faction_ball_alert = faction_ball_alert or {"notify": "off"}
        halloween_contest_alert = halloween_contest_alert or {"notify": "off"}
        wb_battle_alert = wb_battle_alert or {"notify": "off"}

        view = AlertSettingsView(
            bot,
            interaction.user,
            captcha_alert,
            res_fossils_alert,
            faction_ball_alert,
            halloween_contest_alert,
            wb_battle_alert,
        )

        message = await interaction.followup.send(
            content="Modify your Alert Settings:", view=view, ephemeral=True
        )
        view.message = message

        pretty_log(
            "ui",
            f"[Alert Settings] Displayed alert settings for {interaction.user.display_name}",
        )

    except Exception as e:
        pretty_log("error", f"Failed to load alert settings: {e}")
        await interaction.followup.send(
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
        self,
        bot: commands.Bot,
        user: discord.Member,
        captcha_alert,
        res_fossils_alert,
        faction_ball_alert,
        halloween_contest_alert,
        wb_battle_alert,
    ):
        super().__init__(timeout=180)
        self.bot = bot
        self.user = user
        self.captcha_alert = captcha_alert
        self.res_fossils_alert = res_fossils_alert
        self.faction_ball_alert = faction_ball_alert
        self.halloween_contest_alert = halloween_contest_alert
        self.wb_battle_alert = wb_battle_alert
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
    # [🎯 BUTTON] Faction Ball Alert (4-State Cycle)
    # 💫────────────────────────────────────
    @discord.ui.button(
        label="Faction Ball Alert: OFF", style=ButtonStyle.secondary, emoji="🎯"
    )
    async def faction_ball_alert_button(
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
                str(self.faction_ball_alert.get("notify", "off")).lower()
                if self.faction_ball_alert
                else "off"
            )

            # 🔹 4-State Cycle: off → on → on_no_pings → react → off
            if current_state == "off":
                new_state = "on"
            elif current_state == "on":
                new_state = "on_no_pings"
            elif current_state == "on_no_pings":
                new_state = "react"
            else:  # react or any other state
                new_state = "off"

            await upsert_user_faction_ball_alert(self.bot, self.user, new_state)
            self.faction_ball_alert = {"notify": new_state}

            # 🔹 Refresh buttons
            self.update_button_styles()

            # 🔹 Display friendly text
            display_text = {
                "off": "Off",
                "on": "On",
                "on_no_pings": "On (No Pings)",
                "react": "React",
            }.get(new_state, "OFF")

            await interaction.edit_original_response(
                content=f"Modify your Alert Settings:\n🎯 Faction Ball Alert set to **{display_text}**",
                view=self,
            )

            pretty_log(
                tag="ui",
                message=f"{self.user.display_name} set Faction Ball Alert to {display_text}",
                bot=self.bot,
            )

        except Exception as e:
            pretty_log(
                tag="error",
                message=f"Error toggling Faction Ball Alert: {e}",
                bot=self.bot,
            )
            await interaction.followup.send(
                "⚠️ An error occurred while updating Faction Ball Alert.",
                ephemeral=True,
            )

    # 💫────────────────────────────────────
    # [🎯 BUTTON] WB Battle Alert (2-State Cycle)
    # 💫────────────────────────────────────
    @discord.ui.button(
        label="World Boss Battle Alert: OFF",
        style=ButtonStyle.secondary,
        emoji=STRAYMONS__EMOJIS.world_boss_spawned,
    )
    async def wb_battle_alert_button(
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
                str(self.wb_battle_alert.get("notify", "off")).lower()
                if self.wb_battle_alert
                else "off"
            )

            # 🔹 2-State Cycle: off → on → off
            new_state = "on" if current_state == "off" else "off"

            await upsert_user_wb_battle_alert(self.bot, self.user, new_state)
            self.wb_battle_alert = {"notify": new_state}

            # 🔹 Refresh buttons
            self.update_button_styles()

            # 🔹 Display friendly text
            display_text = "ON" if new_state == "on" else "OFF"

            await interaction.edit_original_response(
                content=f"Modify your World Boss Battle Alert Settings:\n🛡️ World Boss Battle Alert set to **{display_text}**",
                view=self,
            )

            pretty_log(
                tag="ui",
                message=f"{self.user.display_name} set World Boss Battle Alert to {display_text}",
                bot=self.bot,
            )

        except Exception as e:
            pretty_log(
                tag="error",
                message=f"Error toggling World Boss Battle Alert: {e}",
                bot=self.bot,
            )
            await interaction.followup.send(
                "⚠️ An error occurred while updating World Boss Battle Alert.",
                ephemeral=True,
            )

    # 💫────────────────────────────────────
    # [🎃 BUTTON] Halloween Contest Score Alert (3 -State Cycle)
    # 💫────────────────────────────────────
    @discord.ui.button(
        label="Halloween Contest Alert: OFF", style=ButtonStyle.secondary, emoji="🎃"
    )
    async def halloween_contest_alert_button(
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
                str(self.halloween_contest_alert.get("notify", "off")).lower()
                if self.halloween_contest_alert
                else "off"
            )

            # 🔹 3-State Cycle: off → on → on_no_pings → off
            if current_state == "off":
                new_state = "on"
            elif current_state == "on":
                new_state = "on_no_pings"
            else:
                new_state = "off"

            await upsert_user_halloween_contest_alert(self.bot, self.user, new_state)
            self.halloween_contest_alert = {"notify": new_state}

            # 🔹 Refresh buttons
            self.update_button_styles()

            # 🔹 Display friendly text
            display_text = {
                "off": "OFF",
                "on": "ON",
                "on_no_pings": "ON (No Pings)",
            }.get(new_state, "OFF")

            await interaction.edit_original_response(
                content=f"Modify your Halloween Contest Score Alert Settings:\n🎃 Halloween Contest Score Alert set to **{display_text}**",
                view=self,
            )

            pretty_log(
                tag="ui",
                message=f"{self.user.display_name} set Halloween Contest Score Alert to {display_text}",
                bot=self.bot,
            )

        except Exception as e:
            pretty_log(
                tag="error",
                message=f"Error toggling Halloween Contest Score Alert: {e}",
                bot=self.bot,
            )
            await interaction.followup.send(
                "⚠️ An error occurred while updating Halloween Contest Score Alert.",
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

        # 🎯 Faction Ball Alert Button (4 states)
        faction_ball_alert_state = (
            str(self.faction_ball_alert.get("notify", "off")).lower()
            if self.faction_ball_alert
            else "off"
        )

        if faction_ball_alert_state == "off":
            self.faction_ball_alert_button.style = ButtonStyle.secondary
            self.faction_ball_alert_button.label = "Faction Ball Alert: OFF"
        elif faction_ball_alert_state == "on":
            self.faction_ball_alert_button.style = ButtonStyle.success
            self.faction_ball_alert_button.label = "Faction Ball Alert: ON"
        elif faction_ball_alert_state == "on_no_pings":
            self.faction_ball_alert_button.style = ButtonStyle.primary
            self.faction_ball_alert_button.label = "Faction Ball Alert: ON (No Pings)"
        elif faction_ball_alert_state == "react":
            self.faction_ball_alert_button.style = ButtonStyle.danger
            self.faction_ball_alert_button.label = "Faction Ball Alert: REACT"
        else:
            self.faction_ball_alert_button.style = ButtonStyle.secondary
            self.faction_ball_alert_button.label = "Faction Ball Alert: OFF"

        # 🎃 Halloween Contest Alert Button (3 states)
        halloween_contest_alert_state = (
            str(self.halloween_contest_alert.get("notify", "off")).lower()
            if self.halloween_contest_alert
            else "off"
        )
        if halloween_contest_alert_state == "off":
            self.halloween_contest_alert_button.style = ButtonStyle.secondary
            self.halloween_contest_alert_button.label = "Halloween Contest Alert: OFF"
        elif halloween_contest_alert_state == "on":
            self.halloween_contest_alert_button.style = ButtonStyle.success
            self.halloween_contest_alert_button.label = "Halloween Contest Alert: ON"
        elif halloween_contest_alert_state == "on_no_pings":
            self.halloween_contest_alert_button.style = ButtonStyle.primary
            self.halloween_contest_alert_button.label = (
                "Halloween Contest Alert: ON (No Pings)"
            )
        else:
            self.halloween_contest_alert_button.style = ButtonStyle.secondary
            self.halloween_contest_alert_button.label = "Halloween Contest Alert: OFF"

        # 🛡️ WB Battle Alert Button (2 states)
        wb_battle_alert_state = (
            str(self.wb_battle_alert.get("notify", "off")).lower()
            if self.wb_battle_alert
            else "off"
        )
        if wb_battle_alert_state == "off":
            self.wb_battle_alert_button.style = ButtonStyle.secondary
            self.wb_battle_alert_button.label = "World Boss Battle Alert: OFF"
        elif wb_battle_alert_state == "on":
            self.wb_battle_alert_button.style = ButtonStyle.success
            self.wb_battle_alert_button.label = "World Boss Battle Alert: ON"
        else:
            self.wb_battle_alert_button.style = ButtonStyle.secondary
            self.wb_battle_alert_button.label = "World Boss Battle Alert: OFF"

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
