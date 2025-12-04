from datetime import datetime

import discord
from discord import ButtonStyle
from discord.ext import commands

from config.aesthetic import *
from config.current_setup import MINCCINO_COLOR
from group_func.toggle.timer.timer_db_func import (
    fetch_timer,
    set_timer,
    update_battle_setting,
    update_pokemon_setting,
)
from utils.embeds.design_embed import design_embed
from utils.essentials.loader.pretty_defer import *
from utils.loggers.debug_log import debug_log, enable_debug
from utils.loggers.pretty_logs import pretty_log

enable_debug(f"{__name__}.timer_settings_func")
enable_debug(f"{__name__}.TimerSettingsView")


# 💗────────────────────────────────────────────
# [🎀 FUNCTION] Timer Settings
# 💗────────────────────────────────────────────
async def timer_settings_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
):
    """Handle the timer settings interaction."""
    try:
        # 🐾 Defer the interaction
        await interaction.response.defer(ephemeral=True)

        # 🐾 Grab the user info
        user = interaction.user
        user_id = user.id
        timer_setting = await fetch_timer(bot=bot, user_id=user_id)
        pretty_log(
            tag="info",
            message=f"Fetched timer settings from DB for {user} | {timer_setting}",
            label="STRAYMONS",
            bot=bot,
        )
        pokemon_settings = timer_setting.get("pokemon_setting", "Off")
        fish_settings = timer_setting.get("fish_setting", "Off")
        battle_settings = timer_setting.get("battle_setting", "Off")
        # 🐾 Debug log
        pretty_log(
            tag="info",
            message=f"Fetched timer settings for {user}: Pokemon: {pokemon_settings}, Battle: {battle_settings}",
            label="STRAYMONS",
            bot=bot,
        )
        # 🌸 Prepare the Timer Settings View
        view = TimerSettingsView(
            bot=bot,
            user=user,
            pokemon_setting=pokemon_settings,
            battle_setting=battle_settings,
        )

        # ✨ Send the Timer Settings Menu
        message = await interaction.edit_original_response(
            content="Modify your Timer Settings:",
            view=view,
        )

        # Store the message in the view for timeout handling
        view.message = message

        pretty_log(
            tag="info",
            message=f"Displayed timer settings menu for {user}",
            label="STRAYMONS",
            bot=bot,
        )

    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Error in timer_settings_func: {e}",
            label="STRAYMONS",
            bot=bot,
        )


# 💗────────────────────────────────────────────
# [🌸 VIEW CLASS] Timer Settings View
# 💗────────────────────────────────────────────
class TimerSettingsView(discord.ui.View):
    def __init__(
        self,
        bot: commands.Bot,
        user: discord.Member,
        pokemon_setting,
        battle_setting,
    ):
        super().__init__(timeout=180)  # 3 minutes timeout
        self.bot = bot
        self.user = user
        self.pokemon_setting = pokemon_setting
        self.battle_setting = battle_setting
        self.message = None  # set later
        self.update_buttons_styles()

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [🎯 BUTTON] Pokemon (4 - State Cycle)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    @discord.ui.button(
        label="Pokemon: Off",
        style=ButtonStyle.secondary,
        emoji=Emojis_Balls.small_pokeball,
    )
    async def pokemon_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(
                "This is not your timer settings menu!", ephemeral=True
            )
            return

        # Defer
        await interaction.response.defer()

        # Cycle thru
        try:
            pretty_log(
                tag="info", message=f"Current pokemon setting: {self.pokemon_setting}"
            )
            current_state = (
                str(self.pokemon_setting).lower() if self.pokemon_setting else "off"
            )
            pretty_log(tag="info", message=f"Current pokemon state: {current_state}")
            # 4- State Cycle: off - > on -> on_no_pings -> react -> off
            if current_state == "off":
                new_state = "on"
            elif current_state == "on":
                new_state = "on_no_pings"
            elif current_state == "on_no_pings" or current_state == "on w/o pings":
                new_state = "react"
            elif current_state == "react":
                new_state = "off"
            else:
                new_state = "off"

            # 💾 Update the Pokemon timer setting in DB
            await update_pokemon_setting(
                bot=self.bot,
                user_id=self.user.id,
                pokemon_setting=new_state,
            )

            self.pokemon_setting = new_state

            # Refresh buttons
            self.update_buttons_styles()

            # Display friendly text
            display_text = {
                "off": "Off",
                "on": "On",
                "on_no_pings": "On (No pings)",
                "react": "React ",
            }.get(new_state, "Off")

            await interaction.edit_original_response(
                content=f"Modify your Timer Settings:\n{Emojis_Balls.small_pokeball} Pokemon Timer set to **{display_text}**",
                view=self,
            )
            pretty_log(
                tag="info",
                message=f"User {self.user} set Pokemon timer to {new_state}",
                label="STRAYMONS",
                bot=self.bot,
            )

        except Exception as e:
            pretty_log(
                tag="error",
                message=f"Error getting current pokemon timer state: {e}",
                label="STRAYMONS",
                bot=self.bot,
            )
            await interaction.followup.send(
                "An error occurred while updating your Pokemon timer setting.",
                ephemeral=True,
            )

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [🧩 Button] Battle Timer (3 State Cycle)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    @discord.ui.button(label="Battle: Off", style=ButtonStyle.secondary, emoji="⚔️")
    async def battle_button(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(
                "This is not your timer settings menu!", ephemeral=True
            )
            return

        # Defer
        await interaction.response.defer()

        # Cycle thru
        try:
            pretty_log(
                tag="info", message=f"Current battle setting: {self.battle_setting}"
            )
            current_state = (
                str(self.battle_setting).lower() if self.battle_setting else "off"
            )
            pretty_log(tag="info", message=f"Current battle state: {current_state}")

            # 3- State Cycle: off - > on -> on_no_pings -> off
            if current_state == "off":
                new_state = "on"
            elif current_state == "on":
                new_state = "on_no_pings"
            elif current_state == "on_no_pings" or current_state == "on w/o pings":
                new_state = "off"
            else:
                new_state = "off"

            # 💾 Update the Battle timer setting in DB
            await update_battle_setting(
                bot=self.bot,
                user_id=self.user.id,
                battle_setting=new_state,
            )
            self.battle_setting = new_state

            # Refresh buttons
            self.update_buttons_styles()

            # Display friendly text
            display_text = {
                "off": "Off",
                "on": "On",
                "on_no_pings": "On (No pings)",
            }.get(new_state, "Off")

            await interaction.edit_original_response(
                content=f"Modify your Timer Settings:\n⚔️ Battle Timer set to **{display_text}**",
                view=self,
            )
            pretty_log(
                tag="info",
                message=f"User {self.user} set Battle timer to {new_state}",
                label="STRAYMONS",
                bot=self.bot,
            )

        except Exception as e:
            pretty_log(
                tag="error",
                message=f"Error getting current battle timer state: {e}",
                label="STRAYMONS",
                bot=self.bot,
            )
            await interaction.followup.send(
                "An error occurred while updating your Battle timer setting.",
                ephemeral=True,
            )

    # 💫────────────────────────────────────
    # [🎨 STYLE UPDATE FUNCTION]
    # 💫────────────────────────────────────
    def update_buttons_styles(self):
        # Update Pokemon button style (4 States)
        pokemon_state = str(self.pokemon_setting) if self.pokemon_setting else "off"

        if pokemon_state == "off":
            self.pokemon_button.style = ButtonStyle.secondary
            self.pokemon_button.label = "Pokemon Timer: Off"
        elif pokemon_state == "on":
            self.pokemon_button.style = ButtonStyle.success
            self.pokemon_button.label = "Pokemon Timer: On"
        elif pokemon_state in ("on_no_pings", "on w/o pings"):
            self.pokemon_button.style = ButtonStyle.blurple
            self.pokemon_button.label = "Pokemon Timer: On (No pings)"
        elif pokemon_state == "react":
            self.pokemon_button.style = ButtonStyle.danger
            self.pokemon_button.label = "Pokemon Timer: React"
        else:
            self.pokemon_button.style = ButtonStyle.secondary
            self.pokemon_button.label = "Pokemon Timer: Off"

        # Update Battle button style (3 States)
        battle_state = str(self.battle_setting) if self.battle_setting else "off"
        if battle_state == "off":
            self.battle_button.style = ButtonStyle.secondary
            self.battle_button.label = "Battle Timer: Off"
        elif battle_state == "on":
            self.battle_button.style = ButtonStyle.success
            self.battle_button.label = "Battle Timer: On"
        elif battle_state in ("on_no_pings", "on w/o pings"):
            self.battle_button.style = ButtonStyle.blurple
            self.battle_button.label = "Battle Timer: On (No pings)"
        else:
            self.battle_button.style = ButtonStyle.secondary
            self.battle_button.label = "Battle Timer: Off"

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # [⏳ TIMEOUT HANDLER]
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    async def on_timeout(self):
        # Disable all buttons on timeout
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True
        # Edit the original message to reflect disabled buttons
        if self.message:
            try:
                await self.message.edit(view=self)
                pretty_log(
                    tag="info",
                    message=f"Timer settings menu for {self.user} has timed out.",
                    label="STRAYMONS",
                    bot=self.bot,
                )
            except Exception as e:
                pass
