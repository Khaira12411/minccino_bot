import json

import discord
from discord import PartialEmoji, app_commands
from discord.ext import commands

from config.aesthetic import Emojis
from config.held_items import *
from group_func.toggle.held_item.held_items_db_func import (
    fetch_all_user_item_pings,
    set_user_item_subscription,
    update_user_name,
)
from utils.embeds.embed_settings_summary import build_summary_settings_embed
from utils.essentials.loader.loader import *
from utils.loggers.pretty_logs import pretty_log


# ----------------- Helper: build buttons -----------------
def build_item_buttons(user_subs: set, items: list[str]) -> list[discord.ui.Button]:
    buttons = []
    for item in items:
        is_sub = item in user_subs
        emoji_str = getattr(HELD_ITEM_EMOJI, item, "🐭")
        emoji = PartialEmoji.from_str(emoji_str) if ":" in emoji_str else emoji_str

        buttons.append(
            discord.ui.Button(
                label=f"{'✅' if is_sub else '❌'}",
                emoji=emoji,
                style=(
                    discord.ButtonStyle.success if is_sub else discord.ButtonStyle.gray
                ),
                custom_id=f"toggle_{item}",
            )
        )
    return buttons


# ----------------- Individual Item Toggle Button -----------------
class ItemToggleButton(discord.ui.Button):
    def __init__(self, item_name: str, checked: bool):
        self.item_name = item_name
        self.checked = checked

        # Special case: "All Held Items"
        if self.item_name == "all_held_items":
            emoji = "🐭"
            label_text = f"{emoji} {'✅' if checked else '❌'} All Held Items"
        else:
            emoji_str = getattr(HELD_ITEM_EMOJI, item_name, "🐭")
            if emoji_str.startswith("<:") and emoji_str.endswith(">"):
                emoji = discord.PartialEmoji.from_str(emoji_str)
                label_text = (
                    f"{'✅' if checked else '❌'} {item_name.replace('_',' ').title()}"
                )
            else:
                emoji = None
                label_text = f"{emoji_str} {'✅' if checked else '❌'} {item_name.replace('_',' ').title()}"

        super().__init__(
            label=label_text,
            style=discord.ButtonStyle.success if checked else discord.ButtonStyle.gray,
            custom_id=f"toggle_{item_name}",
            emoji=emoji,
        )

    async def callback(self, interaction: discord.Interaction):
        try:
            self.checked = not self.checked
            self.style = (
                discord.ButtonStyle.success
                if self.checked
                else discord.ButtonStyle.gray
            )

            # Update label for "All Held Items"
            if self.item_name == "all_held_items":
                self.label = f"🐭 {'✅' if self.checked else '❌'} All Held Items"
            else:
                emoji_str = getattr(HELD_ITEM_EMOJI, self.item_name, "🐭")
                if emoji_str.startswith("<:") and emoji_str.endswith(">"):
                    self.label = f"{'✅' if self.checked else '❌'} {self.item_name.replace('_',' ').title()}"
                else:
                    self.label = f"{emoji_str} {'✅' if self.checked else '❌'} {self.item_name.replace('_',' ').title()}"

            # Update selection in parent view
            if self.checked:
                self.view.selection_changed.add(self.item_name)
            else:
                self.view.selection_changed.discard(self.item_name)

            await interaction.response.edit_message(view=self.view)

        except Exception as e:
            from utils.loggers.pretty_logs import pretty_log

            pretty_log(
                "error",
                f"Failed to toggle held item '{self.item_name}' for user {interaction.user.id} | Error: {e}",
            )
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ Something went wrong toggling this item.", ephemeral=True
                )
            else:
                await interaction.followup.send(
                    "❌ Something went wrong toggling this item.", ephemeral=True
                )


# ----------------- Batch Buttons -----------------
class BatchButton(discord.ui.Button):
    def __init__(self, label: str, style: discord.ButtonStyle, callback_func):
        super().__init__(label=label, style=style)
        self.custom_callback = callback_func

    async def callback(self, interaction: discord.Interaction):
        try:
            await self.custom_callback(interaction)
        except Exception as e:
            from utils.loggers.pretty_logs import pretty_log

            pretty_log(
                "error",
                f"Batch button '{self.label}' failed for user {interaction.user.id} | Error: {e}",
            )
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ Something went wrong with this action.", ephemeral=True
                )
            else:
                await interaction.followup.send(
                    "❌ Something went wrong with this action.", ephemeral=True
                )


# ----------------- Dynamic View (with proper emojis) -----------------
class ItemSelectView(discord.ui.View):
    def __init__(self, bot, user_id: int, items: list[str], user_subs: set):
        super().__init__(timeout=300)
        self.bot = bot
        self.user_id = user_id
        self.items = items
        self.user_subs = set(user_subs)
        self.selection_changed = set(user_subs)

        # Add item toggle buttons
        for item in items:
            self.add_item(ItemToggleButton(item, item in self.user_subs))

        # Add batch buttons
        self.add_item(BatchButton("Add All", discord.ButtonStyle.blurple, self.add_all))
        self.add_item(
            BatchButton("Remove All", discord.ButtonStyle.gray, self.remove_all)
        )
        self.add_item(
            BatchButton("Save", discord.ButtonStyle.green, self.save_selection)
        )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user_id

    async def add_all(self, interaction: discord.Interaction):
        for child in self.children:
            if isinstance(child, ItemToggleButton):
                child.checked = True
                child.style = discord.ButtonStyle.success
                self.selection_changed.add(child.item_name)

                emoji_str = getattr(HELD_ITEM_EMOJI, child.item_name, "🐭")
                if emoji_str.startswith("<:") and emoji_str.endswith(">"):
                    child.label = f"✅ {child.item_name.replace('_',' ').title()}"
                else:
                    child.label = (
                        f"{emoji_str} ✅ {child.item_name.replace('_',' ').title()}"
                    )

        await interaction.response.edit_message(view=self)

    async def remove_all(self, interaction: discord.Interaction):
        for child in self.children:
            if isinstance(child, ItemToggleButton):
                child.checked = False
                child.style = discord.ButtonStyle.gray
                self.selection_changed.discard(child.item_name)

                emoji_str = getattr(HELD_ITEM_EMOJI, child.item_name, "🐭")
                if emoji_str.startswith("<:") and emoji_str.endswith(">"):
                    child.label = f"❌ {child.item_name.replace('_',' ').title()}"
                else:
                    child.label = (
                        f"{emoji_str} ❌ {child.item_name.replace('_',' ').title()}"
                    )

        await interaction.response.edit_message(view=self)

    #

    async def save_selection(self, interaction: discord.Interaction):
        handle = await pretty_defer(interaction, content="Saving your selections...")

        try:
            # ✅ Detect what actually changed
            changed_items = self.selection_changed.symmetric_difference(self.user_subs)
            if not changed_items:
                await handle.stop(content="⚠️ No changes detected.")
                return

            # ✅ Keep user_name in sync (only if there are actual changes)
            await update_user_name(self.bot, self.user_id, str(interaction.user))

            sub_changes = []
            for item in changed_items:
                old_state = item in self.user_subs
                new_state = item in self.selection_changed
                sub_changes.append((item, old_state, new_state))

                pretty_log(
                    "info",
                    f"Setting held item '{item}' -> {new_state} for user {self.user_id}",
                )

                await set_user_item_subscription(
                    self.bot, self.user_id, item, subscribed=new_state
                )

            # ✅ Refresh baseline
            self.user_subs = set(self.selection_changed)

            # ✅ Reload cache
            from utils.cache.held_item_cache import load_held_item_cache

            await load_held_item_cache(self.bot)

            # ✅ Build summary embed for the changes
            desc_lines = []
            for item, old, new in sub_changes:
                status_change = "✅" if new else "❌"
                emoji_str = getattr(HELD_ITEM_EMOJI, item, "🐭")
                desc_lines.append(
                    f"{status_change} {emoji_str} {item.replace('_',' ').title()}: "
                    f"{'On' if old else 'Off'} -> {'On' if new else 'Off'}"
                )

            embed = build_summary_settings_embed(
                title=f"{Emojis.brown_heart_message} Held Items Update",
                changes=sub_changes,
                mode="held_items_ping",
                user=interaction.user,
            )

            await handle.stop(embed=embed)  # ✅ Only embed, no view/buttons

        except Exception as e:
            pretty_log(
                "error",
                f"Failed to save held item selections for user {self.user_id} | Error: {e}",
            )
            await handle.stop(
                content="❌ An error occurred while saving your selections. Please try again later."
            )


# ----------------- Main dropdown -----------------
class HeldItemDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Battle Items", value="battle"),
            discord.SelectOption(label="Type Boosters", value="type"),
            discord.SelectOption(label="Evolution Items", value="evolution"),
        ]
        super().__init__(
            placeholder="Choose category...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        try:
            # Fetch user's current subscriptions
            all_users = await fetch_all_user_item_pings(interaction.client)
            user_row = next(
                (u for u in all_users if u["user_id"] == interaction.user.id), {}
            )

            user_subs = set()
            held_item_pings = user_row.get("held_item_pings", {})
            if isinstance(held_item_pings, str):
                # Parse JSON string into a dict
                held_item_pings = json.loads(held_item_pings)

            if isinstance(held_item_pings, dict):
                user_subs = {item for item, sub in held_item_pings.items() if sub}

            # Determine which items to display
            if self.values[0] == "battle":
                items = battle_items
            elif self.values[0] == "type":
                items = type_boosters
            else:
                items = evolution_items

            view = ItemSelectView(
                bot=interaction.client,
                user_id=interaction.user.id,
                items=items,
                user_subs=user_subs,
            )
            await interaction.response.send_message(
                f"Select your held item ping for **{self.values[0]}**:",
                view=view,
                ephemeral=True,
            )

        except Exception as e:
            from utils.loggers.pretty_logs import pretty_log

            pretty_log(
                "error",
                f"Failed to display held item dropdown for user {interaction.user.id} | Error: {e}",
            )
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ Failed to load your held items settings. Please try again later.",
                    ephemeral=True,
                )
            else:
                await interaction.followup.send(
                    "❌ Failed to load your held items settings. Please try again later.",
                    ephemeral=True,
                )


import json


# ----------------- All Held Items View -----------------
class AllHeldItemsView(discord.ui.View):
    def __init__(self, bot, user_id: int, is_subscribed: bool):
        super().__init__(timeout=300)
        self.bot = bot
        self.user_id = user_id
        self.selection_changed = set()
        if is_subscribed:
            self.selection_changed.add("all_held_items")

        # Add the toggle button
        self.toggle_button = ItemToggleButton(
            "all_held_items", "all_held_items" in self.selection_changed
        )
        self.add_item(self.toggle_button)

        # Add Remove All Held Items Ping button (red, with emoji)
        self.remove_all_button = BatchButton(
            "❌ Remove All Held Items Ping", discord.ButtonStyle.red, self.remove_all
        )
        self.add_item(self.remove_all_button)

        # Add Save button (green)
        self.add_item(
            BatchButton("💾 Save", discord.ButtonStyle.green, self.save_selection)
        )

    #

    async def save_selection(self, interaction: discord.Interaction):
        async def process_save():
            all_held = "all_held_items" in self.selection_changed
            pretty_log(
                "info",
                f"Setting 'All Held Items' -> {all_held} for user {self.user_id}",
            )

            # Fetch all user rows
            all_rows = await fetch_all_user_item_pings(self.bot)
            user_row = next(
                (row for row in all_rows if row["user_id"] == self.user_id), None
            )

            await update_user_name(self.bot, self.user_id, str(interaction.user))
            # Ensure we have the JSON object
            held_items_raw = user_row["held_item_pings"] if user_row else "{}"

            try:
                held_items = (
                    json.loads(held_items_raw)
                    if isinstance(held_items_raw, str)
                    else held_items_raw
                )
            except Exception:
                held_items = {}  # fallback if parsing fails

            sub_changes = []
            for item in HELD_ITEMS_DICT.keys():
                old_sub = held_items.get(item, False)
                new_sub = all_held

                if old_sub != new_sub:
                    sub_changes.append((item, old_sub, new_sub))

                await set_user_item_subscription(
                    self.bot, self.user_id, item, subscribed=new_sub
                )

            # Update the 'all_held_items' flag
            await set_user_item_subscription(
                self.bot, self.user_id, "all_held_items", subscribed=all_held
            )

            # Reset baseline after saving
            self.user_subs = set(self.selection_changed)

            return sub_changes

        # Use pretty_defer loader
        handle = await pretty_defer(interaction, content="Saving your settings...")

        try:
            sub_changes = await process_save()

            await handle.stop(
                content="✅ Your 'All Held Items' settings has been saved!"
            )

            if sub_changes:
                desc_lines = []
                for item, old, new in sub_changes:
                    status_change = "✅" if new else "❌"
                    desc_lines.append(
                        f"{status_change} {item.replace('_',' ').title()}: {'On' if old else 'Off'} -> {'On' if new else 'Off'}"
                    )

                embed = discord.Embed(
                    title="💎 All Held Items Update 💎",
                    description="\n".join(desc_lines),
                    color=0xFFD0F0,
                )

                await interaction.followup.send(embed=embed, ephemeral=True)
                from utils.cache.held_item_cache import load_held_item_cache

                await load_held_item_cache(self.bot)

        except Exception as e:
            pretty_log(
                "error",
                f"Failed to save 'All Held Items' for user {self.user_id} | Error: {e}",
            )
            await handle.stop(
                content="❌ Failed to save your settings. Please try again later."
            )

    #
    async def remove_all(self, interaction: discord.Interaction):
        """Remove all held item pings and reset all flags."""

        handle = await pretty_defer(interaction, content="Removing all held items...")

        try:
            self.selection_changed.discard("all_held_items")

            sub_changes = []
            for item in HELD_ITEMS_DICT.keys():
                await set_user_item_subscription(
                    self.bot, self.user_id, item, subscribed=False
                )
                sub_changes.append((item, True, False))

            await set_user_item_subscription(
                self.bot, self.user_id, "all_held_items", subscribed=False
            )

            # Update toggle button
            self.toggle_button.checked = False
            self.toggle_button.label = "Add All Held Items ❌"
            self.toggle_button.style = discord.ButtonStyle.gray

            # Update Remove All button to show emoji feedback
            self.remove_all_button.label = "❌ Remove All Held Items Ping"

            await handle.stop(content="✅ All Held Items removed!")
            await interaction.edit_original_response(view=self)
            embed = build_summary_settings_embed(
                title=f"{Emojis.brown_heart_message} All Held Items Removed",
                changes=sub_changes,
                mode="held_items_ping",
                simple=True,
                user=interaction.user,
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            pretty_log(
                "error",
                f"Failed to remove 'All Held Items' settings for user {self.user_id} | Error: {e}",
            )
            await handle.stop(
                content="❌ Failed to remove your held items settings. Please try again later."
            )


# ----------------- Updated Dropdown Options -----------------
# ----------------- Updated Dropdown Options -----------------
class HeldItemDropdown(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(label="Battle Items", value="battle"),
            discord.SelectOption(label="Type Boosters", value="type"),
            discord.SelectOption(label="Evolution Items", value="evolution"),
            discord.SelectOption(
                label="All Held Items 🐭", value="all"
            ),  # New general category
        ]
        super().__init__(
            placeholder="Choose category...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        try:
            # Fetch user's current subscriptions
            all_users = await fetch_all_user_item_pings(interaction.client)
            user_row = next(
                (u for u in all_users if u["user_id"] == interaction.user.id), {}
            )

            user_subs = set()
            held_item_pings = user_row.get("held_item_pings", {})
            if isinstance(held_item_pings, str):
                held_item_pings = json.loads(held_item_pings)

            if isinstance(held_item_pings, dict):
                user_subs = {item for item, sub in held_item_pings.items() if sub}

            # Determine which view to show
            if self.values[0] == "battle":
                items = battle_items
                view = ItemSelectView(
                    interaction.client, interaction.user.id, items, user_subs
                )
                msg_content = f"Select your pings for **Battle Items**:"
            elif self.values[0] == "type":
                items = type_boosters
                view = ItemSelectView(
                    interaction.client, interaction.user.id, items, user_subs
                )
                msg_content = f"Select your pings for **Type Boosters**:"
            elif self.values[0] == "evolution":
                items = evolution_items
                view = ItemSelectView(
                    interaction.client, interaction.user.id, items, user_subs
                )
                msg_content = f"Select your items for **Evolution Items**:"
            else:  # All Held Items
                is_subscribed = "all_held_items" in user_subs
                view = AllHeldItemsView(
                    interaction.client, interaction.user.id, is_subscribed
                )
                msg_content = (
                    "⚠️ Subscribing to **All Held Items pings 🐭** will notify you for *any Pokemon with a held item*, "
                    "including special items. Toggle below to subscribe."
                )

            await interaction.response.send_message(
                msg_content, view=view, ephemeral=True
            )

        except Exception as e:
            pretty_log(
                "error",
                f"Failed to display held item dropdown for user {interaction.user.id} | Error: {e}",
            )
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "❌ Failed to load your held items settings. Please try again later.",
                    ephemeral=True,
                )
            else:
                await interaction.followup.send(
                    "❌ Failed to load your held items settings. Please try again later.",
                    ephemeral=True,
                )


class HeldItemDropdownView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(HeldItemDropdown())


async def toggle_held_item_func(bot: commands.Bot, interaction: discord.Interaction):
    """Open the held items subscription menu."""
    await interaction.response.send_message(
        "Pick a category:", view=HeldItemDropdownView(), ephemeral=True
    )
