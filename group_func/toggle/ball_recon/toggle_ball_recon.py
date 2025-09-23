import json

import discord
from discord import ButtonStyle, app_commands
from discord.ext import commands

from config.aesthetic import Emojis
from group_func.toggle.ball_recon.ball_recon_db_func import (
    fetch_user_rec,
    update_enabled,
    update_fishing,
    update_held_items,
    update_pokemon,
)
from utils.embeds.embed_settings_summary import build_summary_settings_embed
from utils.essentials.loader.loader import pretty_defer
from utils.essentials.safe_response import safe_respond
from utils.listener_func.catch_rate import rarity_emojis
from utils.loggers.pretty_logs import pretty_log

# ─────────────────────────────
# Toggle Buttons
# ─────────────────────────────


class RarityToggleButton(discord.ui.Button):
    def __init__(self, rarity_name: str, checked: bool, category: str, enabled: bool):
        self.rarity_name = rarity_name
        self.checked = checked
        self.category = category
        self.enabled_state = enabled  # ✅ renamed to avoid API confusion

        emoji_str = rarity_emojis.get(rarity_name, "❔")
        emoji = (
            discord.PartialEmoji.from_str(emoji_str) if ":" in emoji_str else emoji_str
        )
        super().__init__(
            label=f"{'✅' if checked else '❌'} {rarity_name.title()}",
            style=ButtonStyle.success if checked else ButtonStyle.gray,
            custom_id=f"toggle_{rarity_name}",
            emoji=emoji,
        )

    async def callback(self, interaction: discord.Interaction):
        if not self.enabled_state:
            await safe_respond(
                interaction,
                method="followup",
                content="⚠️ Your Ball Recommendation settings are disabled. Cannot toggle rarities.",
                ephemeral=True,
            )
            return

        try:
            # Flip state
            self.checked = not self.checked
            self.style = ButtonStyle.success if self.checked else ButtonStyle.gray
            self.label = f"{'✅' if self.checked else '❌'} {self.rarity_name.title()}"

            # Update parent view
            if self.checked:
                self.view.selection_changed.add(self.rarity_name)
            else:
                self.view.selection_changed.discard(self.rarity_name)

            # ✅ safe update
            await safe_respond(
                interaction,
                method="edit",
                view=self.view,
            )

        except Exception as e:
            pretty_log(
                "error",
                f"Failed to toggle rarity '{self.rarity_name}' for user {interaction.user.id} | {e}",
            )
            await safe_respond(
                interaction,
                method="followup",
                content="❌ Something went wrong.",
                ephemeral=True,
            )


# ─────────────────────────────
# Batch Buttons
# ─────────────────────────────


class RarityBatchButton(discord.ui.Button):
    def __init__(self, label: str, style: ButtonStyle, callback_func):
        super().__init__(label=label, style=style)
        self.custom_callback = callback_func

    async def callback(self, interaction: discord.Interaction):
        try:
            await self.custom_callback(interaction)

        except Exception as e:
            pretty_log(
                "error",
                f"Batch button '{self.label}' failed for user {interaction.user.id} | {e}",
            )
            await safe_respond(
                interaction,
                method="followup",
                content="❌ Something went wrong.",
                ephemeral=True,
            )


class DisplayModeButton(discord.ui.Button):
    def __init__(
        self, current_mode: str, user_id: int, category: str, view: discord.ui.View
    ):
        """
        current_mode: either "Best Ball" or "All Balls"
        view: the RaritySelectView instance to store the selected mode
        """
        self.user_id = user_id
        self.category = category
        self.view_ref = view  # store reference to the parent view
        self.mode = current_mode
        label = f"Display Mode: {self.mode}"
        super().__init__(
            label=label, style=ButtonStyle.primary, custom_id="display_mode_toggle"
        )
    #
    async def callback(self, interaction: discord.Interaction):
        # Flip mode
        self.mode = "All Balls" if self.mode == "Best Ball" else "Best Ball"
        self.label = f"Display Mode: {self.mode}"

        try:
            # Save immediately in DB
            from group_func.toggle.ball_recon.ball_recon_db_func import update_display_mode
            await update_display_mode(
                bot=interaction.client,
                user_id=self.user_id,
                category=self.category,
                mode=self.mode,
            )

            # Reload cache
            from utils.cache.ball_reco_cache import load_ball_reco_cache
            await load_ball_reco_cache(interaction.client)

            # Keep the view in sync
            if hasattr(self.view_ref, "display_mode"):
                self.view_ref.display_mode = self.mode
                self.view_ref.original_display_mode = self.mode

            # Update the view in place
            await safe_respond(interaction, method="edit", view=self.view_ref)

            # ✅ Ephemeral confirmation
            await safe_respond(
                interaction,
                method="followup",
                content=f"✅ Display Mode changed to **{self.mode}** for `{self.category.title()}`.",
                ephemeral=True,
            )

        except Exception as e:
            from utils.loggers.pretty_logs import pretty_log
            pretty_log(
                "error",
                f"Failed to save display mode toggle for user {self.user_id} | {e}",
            )
            await safe_respond(
                interaction,
                method="followup",
                content="❌ Failed to update display mode. Please try again later.",
                ephemeral=True,
            )


# ─────────────────────────────
# Rarity Selection View (Fixed)
# ─────────────────────────────
# ─────────────────────────────
# Rarity Selection View (Fixed with Display Mode Tracking)
# ─────────────────────────────
class RaritySelectView(discord.ui.View):
    def __init__(
        self,
        bot,
        user_id: int,
        rarities: list[str],
        user_subs: set,
        category: str,
        enabled: bool = True,
        display_mode: str = "Best Ball",  # default
    ):
        super().__init__(timeout=300)
        self.bot = bot
        self.user_id = user_id
        self.rarities = rarities
        self.user_subs = set(user_subs)
        self.selection_changed = set(user_subs)
        self.update_db_func = None  # will be set dynamically
        self.enabled = enabled
        self.category = category

        # Track display mode
        self.display_mode: str = display_mode
        self.original_display_mode: str = display_mode  # for change detection

        # Add individual rarity toggle buttons
        for rarity in rarities:
            checked = (rarity in self.user_subs) if enabled else False
            button = RarityToggleButton(
                rarity, checked, category=self.category, enabled=enabled
            )
            if not enabled:
                button.style = ButtonStyle.gray
            self.add_item(button)

        # Add batch buttons
        self.add_item(RarityBatchButton("Add All", ButtonStyle.blurple, self.add_all))
        self.add_item(
            RarityBatchButton("Remove All", ButtonStyle.gray, self.remove_all)
        )
        self.add_item(RarityBatchButton("Save", ButtonStyle.green, self.save_selection))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user_id

    # ────────────── Batch Actions ──────────────
    async def add_all(self, interaction: discord.Interaction):
        if not self.enabled:
            await safe_respond(
                interaction,
                content="⚠️ Your Ball Recommendation setting is disabled. Cannot modify selections.",
                ephemeral=True,
                method="followup",
            )
            return

        for child in self.children:
            if isinstance(child, RarityToggleButton):
                child.checked = True
                child.style = ButtonStyle.success
                self.selection_changed.add(child.rarity_name)
                child.label = f"✅ {child.rarity_name.title()}"

        await safe_respond(interaction, method="edit", view=self)
        await safe_respond(
            interaction,
            content="✅ All rarities selected.",
            ephemeral=True,
            method="followup",
        )

    async def remove_all(self, interaction: discord.Interaction):
        if not self.enabled:
            await safe_respond(
                interaction,
                content="⚠️ Your Ball Recommendation setting is disabled. Cannot modify selections.",
                ephemeral=True,
                method="followup",
            )
            return

        for child in self.children:
            if isinstance(child, RarityToggleButton):
                child.checked = False
                child.style = ButtonStyle.gray
                self.selection_changed.discard(child.rarity_name)
                child.label = f"❌ {child.rarity_name.title()}"

        await safe_respond(interaction, method="edit", view=self)
        await safe_respond(
            interaction,
            content="✅ All rarities removed.",
            ephemeral=True,
            method="followup",
        )

    async def save_selection(self, interaction: discord.Interaction):
        try:
            # Detect changes
            changed_rarities = self.selection_changed.symmetric_difference(
                self.user_subs
            )
            display_mode_changed = self.display_mode != self.original_display_mode

            if not changed_rarities and not display_mode_changed:
                await safe_respond(
                    interaction,
                    method="auto",
                    content="⚠️ No changes detected.",
                    ephemeral=True,
                )
                return

            # Build dict for changes
            changes_dict = {"pokemon": {}, "held_items": {}, "fishing": {}}
            for r in changed_rarities:
                new_state = r in self.selection_changed
                if self.category == "pokemon":
                    changes_dict["pokemon"][r] = new_state
                elif self.category == "held_items":
                    changes_dict["held_items"][r] = new_state
                elif self.category == "fishing":
                    changes_dict["fishing"][r] = new_state
                else:
                    changes_dict[self.category][r] = new_state

            # Update rarities in database
            if self.update_db_func:
                await self.update_db_func(
                    interaction.client,
                    self.user_id,
                    {r: (r in self.selection_changed) for r in self.rarities},
                )

            # Update display mode in DB if changed
            if display_mode_changed:
                from group_func.toggle.ball_recon.ball_recon_db_func import (
                    update_display_mode,
                )

                await update_display_mode(
                    bot=interaction.client,
                    user_id=self.user_id,
                    category=self.category,
                    mode=self.display_mode,
                )

            # Refresh baseline
            self.user_subs = set(self.selection_changed)
            self.original_display_mode = self.display_mode

            # Sync button visuals
            for child in self.children:
                if isinstance(child, RarityToggleButton):
                    if child.rarity_name in self.user_subs:
                        child.checked = True
                        child.style = ButtonStyle.success
                        child.label = f"✅ {child.rarity_name.title()}"
                    else:
                        child.checked = False
                        child.style = ButtonStyle.gray
                        child.label = f"❌ {child.rarity_name.title()}"

            # Build embed
            title_map = {
                "pokemon": "Pokemon Ball Recommendation Updated",
                "held_items": "Pokemon w/ Held Items Ball Recommendation Updated",
                "fishing": "Fishing Ball Recommendations Updated",
            }
            title = title_map.get(self.category, "Subscription Updated")

            from utils.embeds.embed_settings_summary import build_summary_settings_embed

            embed = build_summary_settings_embed(
                user=interaction.user,
                title=title,
                changes=changes_dict,
                mode="rarity",
                description=None,
            )

            await safe_respond(
                interaction,
                method="auto",
                embed=embed,
            )

            # Reload cache
            from utils.cache.ball_reco_cache import load_ball_reco_cache

            await load_ball_reco_cache(interaction.client)

        except Exception as e:
            pretty_log(
                "error",
                f"Failed to save {self.category} selection for user {interaction.user.display_name}: {e}",
                label="STRAYMONS",
                bot=interaction.client,
            )
            await safe_respond(
                interaction,
                method="auto",
                content="❌ Failed to save your settings. Please try again later.",
                ephemeral=True,
            )


# ─────────────────────────────
# Dropdown to choose category
# ─────────────────────────────
class RarityDropdown(discord.ui.Select):
    def __init__(self, bot, user_id: int):
        self.bot = bot
        self.user_id = user_id
        options = [
            discord.SelectOption(label="Pokemon", value="pokemon"),
            discord.SelectOption(label="Pokemon w/ Held Item", value="held_items"),
            discord.SelectOption(label="Fishing", value="fishing"),
            discord.SelectOption(label="Enabled/Disabled", value="enabled_toggle"),
        ]
        super().__init__(
            placeholder="Choose a category...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        try:
            user_id = interaction.user.id
            user_rec = await fetch_user_rec(interaction.client, user_id) or {}
            user_rec.setdefault("pokemon", {})
            user_rec.setdefault("held_items", {})
            user_rec.setdefault("fishing", {})
            user_rec.setdefault("enabled", True)

            category = self.values[0]
            handle = await pretty_defer(interaction, ephemeral=True)

            # ---------------- ⚡ Handle enabled toggle ----------------
            if category == "enabled_toggle":
                new_enabled = not user_rec["enabled"]
                await update_enabled(interaction.client, user_id, new_enabled)

                from utils.cache.ball_reco_cache import load_ball_reco_cache

                await load_ball_reco_cache(interaction.client)
                user_rec = await fetch_user_rec(interaction.client, user_id) or {}

                changes_dict = {}
                for sub in ["pokemon", "held_items", "fishing"]:
                    settings = user_rec.get(sub, {})
                    if isinstance(settings, str):
                        settings = json.loads(settings)
                    changes_dict[sub] = settings

                title = (
                    "💌 Ball Recommendations Enabled"
                    if new_enabled
                    else "🚫 Ball Recommendations Disabled"
                )
                description = (
                    "Minccino will now ping you for ball recommendations again. ✨"
                    if new_enabled
                    else "You will not be pinged for ball recommendations."
                )

                embed = build_summary_settings_embed(
                    user=interaction.user,
                    title=title,
                    changes=changes_dict,
                    mode="rarity",
                    description=description,
                )
                await handle.stop(content="Done", embed=embed)
                return

            # ---------------- 🎣 Normal rarity selection ----------------
            current = user_rec.get(category, {})
            if isinstance(current, str):
                current = json.loads(current)

            all_rarities = list(rarity_emojis.keys())
            filtered_rarities = (
                [r for r in all_rarities if r != "golden"]
                if category in ["pokemon", "held_items"]
                else all_rarities
            )

            msg_map = {
                "pokemon": "Select your rarities that you want ball recommendation for:",
                "held_items": "Select your Pokemon w/ Held Item rarities that you want ball recommendation for:",
                "fishing": "Select your Fishing rarities that you want ball recommendation for:",
            }
            msg_content = msg_map.get(category, "Select rarities:")

            # ---------------- ⚡ Create the view ----------------
            view = RaritySelectView(
                bot=interaction.client,
                user_id=user_id,
                rarities=filtered_rarities,
                user_subs={k for k, v in current.items() if v},
                enabled=user_rec.get("enabled", True),
                category=category,
            )

            view.update_db_func = {
                "pokemon": update_pokemon,
                "held_items": update_held_items,
                "fishing": update_fishing,
            }.get(category)

            # ---------------- ⚡ Add display mode button from cache ----------------
            from utils.cache.ball_reco_cache import ball_reco_cache

            # fixed
            display_mode = "Best Ball"  # default fallback
            user_cache = ball_reco_cache.get(user_id, {})
            category_data = user_cache.get(category, {})
            if isinstance(category_data, dict):
                display_mode = category_data.get("display_mode", display_mode)

            view.add_item(
                DisplayModeButton(
                    current_mode=display_mode,
                    user_id=user_id,
                    category=category,
                    view=view,
                )
            )

            await safe_respond(
                interaction,
                method="auto",
                content=msg_content,
                view=view,
            )

        except Exception as e:
            pretty_log(
                "error",
                f"Failed to open RarityDropdown for user {interaction.user.id}: {e}",
                label="STRAYMONS",
                bot=interaction.client,
            )
            await safe_respond(
                interaction,
                method="auto",
                content="❌ Error opening rarity menu. Try again later.",
                ephemeral=True,
            )


class RarityDropdownView(discord.ui.View):
    def __init__(self, bot, user_id: int):
        super().__init__()
        self.add_item(RarityDropdown(bot, user_id))


# ─────────────────────────────
# Command
# ─────────────────────────────


async def toggle_ball_rec_func(bot: commands.Bot, interaction: discord.Interaction):
    try:
        row = await fetch_user_rec(bot=bot, user_id=interaction.user.id)
        if not row:
            await safe_respond(
                interaction,
                content="Please set your catch rate first using the /set-catch-boost command!",
                ephemeral=True,
                method="auto",
            )
            return

        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True, thinking=False)

        await safe_respond(
            interaction,
            content="Pick a category to manage your ball recommendation settings:\n (If you are new, select the enabled/disabled first!)",
            view=RarityDropdownView(bot, interaction.user.id),
            ephemeral=True,
            method="edit",
        )

    except Exception as e:
        pretty_log(
            "error",
            f"Failed to open ball recommendation menu for user {interaction.user.id}: {e}",
            label="STRAYMONS",
            bot=bot,
        )
        await safe_respond(
            interaction,
            content="❌ Error opening the menu. Try again later.",
            ephemeral=True,
            method="auto",
        )
