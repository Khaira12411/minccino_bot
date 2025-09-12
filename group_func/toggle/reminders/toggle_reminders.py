import discord
from discord import ButtonStyle, ui
from discord.ext import commands

from config.aesthetic import *
from group_func.toggle.reminders.user_reminders_db_func import *
from utils.embeds.embed_settings_summary import *
from utils.essentials.loader.loader import *
from utils.essentials.safe_response import safe_respond
from utils.loggers.pretty_logs import pretty_log
import copy

MODE_LABELS = {
    "off": "🚫 Off",
    "channel": "📢 Channel",
    "dms": "📩 DMs",
}

CATEGORY_EMOJIS = {
    "relics": Emojis.relic,  # relic emoji
    "catchbot": Emojis.robot,  # catchbot emoji
}


# ─────────────────────────────
# Mode Button
# ─────────────────────────────
class ReminderModeButton(ui.Button):
    def __init__(self, category: str, mode: str):
        self.category = category
        self.mode = mode or "off"

        # Always use the category emoji
        emoji = CATEGORY_EMOJIS.get(category, "❔")
        label = f"Mode: {MODE_LABELS.get(self.mode, self.mode.title())}"

        style = ButtonStyle.gray if self.mode == "off" else ButtonStyle.green
        super().__init__(label=label, style=style, emoji=emoji)

    async def callback(self, interaction: discord.Interaction):
        # Cycle through options
        order = ["off", "channel", "dms"]
        next_mode = order[(order.index(self.mode) + 1) % len(order)]
        self.mode = next_mode

        # Emoji stays the same, only label changes
        self.emoji = CATEGORY_EMOJIS.get(self.category, "❔")
        self.label = f"Mode: {MODE_LABELS.get(self.mode, self.mode.title())}"
        self.style = ButtonStyle.gray if next_mode == "off" else ButtonStyle.green

        self.view.selection_changed[self.category]["mode"] = next_mode
        await interaction.response.edit_message(view=self.view)


# ─────────────────────────────
# Repeating Button + Modal
# ─────────────────────────────
class ReminderRepeatingButton(ui.Button):
    def __init__(self, category: str, interval: int | None):
        self.category = category
        self.interval = interval

        # Always use category emoji (mascot)
        emoji = CATEGORY_EMOJIS.get(category, "❔")

        if not interval or interval <= 0:
            label = "Repeating: 🚫 Off"
            style = ButtonStyle.gray
        else:
            label = f"Repeating: 🔁 Every {interval} mins"
            style = ButtonStyle.green

        super().__init__(label=label, style=style, emoji=emoji)

    async def callback(self, interaction: discord.Interaction):
        modal = ReminderRepeatingModal(self.category, self.view)
        await interaction.response.send_modal(modal)


class ReminderRepeatingModal(ui.Modal):
    def __init__(self, category: str, parent_view: ui.View):
        super().__init__(title=f"Set repeating interval for {category.title()}")
        self.category = category
        self.parent_view: ReminderButtonsView = parent_view
        self.input = ui.TextInput(
            label="Minutes (min 10)", placeholder="10", required=True
        )
        self.add_item(self.input)
    #
    async def on_submit(self, interaction: discord.Interaction):
        try:
            raw_value = self.input.value.strip().lower()

            if raw_value == "off":
                value = 0
            else:
                try:
                    value = int(raw_value)
                except ValueError:
                    await interaction.response.send_message(
                        "⚠️ Must be a number ≥ 10 or 'off'.", ephemeral=True
                    )
                    return
                if value < 10:
                    value = 10

            # Save to selection
            self.parent_view.selection_changed[self.category]["repeating"] = value

            # Update button
            for child in self.parent_view.children:
                if (
                    isinstance(child, ReminderRepeatingButton)
                    and child.category == self.category
                ):
                    emoji = CATEGORY_EMOJIS.get(self.category, "❔")
                    if value <= 0:
                        child.label = "Repeating: 🚫 Off"
                        child.style = ButtonStyle.gray
                    else:
                        child.label = f"Repeating: 🔁 Every {value} mins"
                        child.style = ButtonStyle.green
                    child.emoji = emoji

            await interaction.response.edit_message(view=self.parent_view)

        except Exception as e:
            await interaction.response.send_message(f"⚠️ Error: {e}", ephemeral=True)


# ─────────────────────────────
# Buttons View (per category)
# ─────────────────────────────
class ReminderButtonsView(ui.View):
    def __init__(self, bot, user_id: int, category: str, selection_changed: dict):
        super().__init__(timeout=300)
        self.bot = bot
        self.user_id = user_id
        self.category = category
        self.selection_changed = selection_changed

        # Mode button
        mode = selection_changed[category].get("mode", "off")
        self.add_item(ReminderModeButton(category, mode))

        # Repeating button (only catchbot)
        if category == "catchbot":
            self.add_item(
                ReminderRepeatingButton(
                    category, selection_changed[category].get("repeating")
                )
            )

        # Save button
        save_button = ui.Button(label="Save", style=ButtonStyle.green)
        save_button.callback = self._save_callback
        self.add_item(save_button)

    #
    async def _save_callback(self, interaction: discord.Interaction):
        try:
            await save_user_reminders(
                bot=self.bot,
                user_id=self.user_id,
                user=interaction.user,
                category=self.category,
                selection_changed=self.selection_changed,
                interaction=interaction,  # pass interaction for followup
            )
        except Exception as e:
            pretty_log(
                "error",
                f"Unexpected error in _save_callback for {self.user_id}: {e}",
                bot=self.bot,
            )


# save button function
# adjust path if needed


async def save_user_reminders(
    bot,
    user_id: int,
    user: discord.Member,
    category: str,
    selection_changed: dict,
    interaction: discord.Interaction,
):
    """
    Core save logic for user reminders. Returns the built embed (or None if failed).
    Uses field-level updater so existing data is preserved.
    """
    from group_func.toggle.reminders.user_reminders_db_func import (
        fetch_user_row,
        update_user_reminders_fields,
    )
    from utils.cache.reminders_cache import load_user_reminders_cache

    # 🌸 Start loader
    loader = await pretty_defer(
        interaction,
        content=f"Saving {category.title()} reminders...",
        ephemeral=True,
    )

    old_reminders = {}
    changed_items = []

    # ───────────── Fetch old reminders ─────────────
    try:
        user_row = await fetch_user_row(bot, user_id)
        old_reminders = user_row["reminders"] if user_row else {}
        print(f"[DEBUG] Old reminders for {user_id}: {old_reminders}")
    except Exception as e:
        pretty_log(
            "error", f"Failed to fetch old reminders for {user_id}: {e}", bot=bot
        )
        user_row = None

    print(f"[DEBUG] Selection changed for {user_id}: {selection_changed}")

    # ───────────── Compute differences ─────────────
    try:
        for cat, data in selection_changed.items():
            old_data = old_reminders.get(cat, {})
            for k, v in data.items():
                old_val = old_data.get(k)
                new_val = v

                print(f"[DEBUG] Compare {cat}.{k}: old={old_val}, new={new_val}")

                if old_val != new_val:
                    changed_items.append((cat, k, old_val, new_val))

        print(f"[DEBUG] Changed items for {user_id}: {changed_items}")

    except Exception as e:
        pretty_log("error", f"Failed to compute changes for {user_id}: {e}", bot=bot)

    # ───────────── Incremental DB updates ─────────────
    try:
        # Prepare multi-field updates dict
        updates = {}
        for cat, key, _old, new in changed_items:
            field_path = f"{cat}.{key}"
            updates[field_path] = new

        # Single call to update all changed fields safely
        if updates:
            await update_user_reminders_fields(
                bot,
                user_id,
                user.name,
                updates=updates,
            )
    except Exception as e:
        pretty_log("error", f"Failed to save reminders to DB for {user_id}: {e}", bot=bot)

    # ───────────── Build embed ─────────────
    embed = None
    try:
        LABELS = {
            "catchbot.mode": "Catchbot Remind Mode",
            "catchbot.repeating": "Catchbot Repeating Reminder",
            "catchbot.remind_next_on": "Catchbot Next Reminder",
            "relics.mode": "Relics Remind Mode",
        }
        #
        def fmt(key: str, val):
            """Format reminder values with emojis & friendly labels."""
            if key.endswith("mode"):
                if isinstance(val, str):
                    match val.lower():
                        case "dms":
                            return "📩 DMs"
                        case "channel":
                            return "📢 Channel"
                        case "off" | "":
                            return "🚫 Off"
                        case _:
                            return val.title()
            elif key.endswith("repeating"):
                if isinstance(val, int) and val > 0:
                    return f"🔁 Every {val} minutes"
                return "🚫 Off"
            elif key.endswith("remind_next_on"):
                # Only show if repeating > 0 and value exists
                if val:
                    try:
                        ts = int(val)
                        return f"<t:{ts}:f>"
                    except Exception:
                        return str(val)
                return None  # hide completely
            elif isinstance(val, bool):
                return "✅ On" if val else "🚫 Off"
            elif val is None:
                return "🚫 Off"
            return str(val)

        if changed_items:
            formatted_changes = []
            for cat, key, old, new in changed_items:
                full_key = f"{cat}.{key}"
                label = LABELS.get(full_key, f"{cat.title()}.{key.title()}")
                f_old, f_new = fmt(key, old), fmt(key, new)
                if f_new is None and f_old is None:
                    continue  # skip hidden fields like remind_next_on when off
                formatted_changes.append((label, f_old, f_new))

            embed = build_reminders_settings_embed(
                user=user,
                title=f"{category.title()} Reminder Updated",
                changes=formatted_changes,
            )
        else:
            print(f"[DEBUG] No changes detected for {user_id}")
            embed = build_reminders_settings_embed(
                user=user,
                title=f"{category.title()} Reminder Settings",
                changes=[],
                description="No changes detected.",
            )
    except Exception as e:
        pretty_log(
            "error", f"Failed to build summary embed for {user_id}: {e}", bot=bot
        )

    # ───────────── Finish loader first ─────────────
    try:
        if embed:
            await loader.stop(
                content=f"Reminders updated for {user.mention}:",
                embed=embed,
            )
        else:
            await loader.stop(content="⚠️ Something went wrong while saving reminders.")
    except Exception as e:
        pretty_log("error", f"Failed to stop loader for {user_id}: {e}", bot=bot)

    # ───────────── Reload cache *after* response ─────────────
    bot.loop.create_task(load_user_reminders_cache(bot=bot))

    return embed


# ─────────────────────────────
# Category Dropdown
# ─────────────────────────────
class ReminderCategorySelect(ui.Select):
    def __init__(self, parent_view, categories: list[str]):
        options = [
            discord.SelectOption(label=cat.title(), value=cat) for cat in categories
        ]
        super().__init__(placeholder="Select a reminder category...", options=options)
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        if not self.values:
            return
        category = self.values[0]
        buttons_view = ReminderButtonsView(
            bot=self.parent_view.bot,
            user_id=self.parent_view.user_id,
            category=category,
            selection_changed=self.parent_view.selection_changed,
        )
        await interaction.response.send_message(
            f"⚡ Configure settings for **{category.title()}**:",
            view=buttons_view,
            ephemeral=True,
        )


# ─────────────────────────────
# Main Select View
# ─────────────────────────────
class ReminderSelectView(ui.View):
    def __init__(self, bot, user_id: int, user_reminders: dict[str, dict]):
        super().__init__(timeout=300)
        self.bot = bot
        self.user_id = user_id
        self.selection_changed = {k: v.copy() for k, v in user_reminders.items()}

        # Dropdown
        categories = list(user_reminders.keys())
        if categories:
            self.add_item(ReminderCategorySelect(self, categories))


# ─────────────────────────────
# Slash Command Handler
# ─────────────────────────────
async def toggle_reminders_func(bot: commands.Bot, interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    user_id = interaction.user.id

    from group_func.toggle.reminders.user_reminders_db_func import (
        fetch_user_row,
        upsert_user_reminders,
    )
    from utils.cache.reminders_cache import load_user_reminders_cache

    # 🔹 Check if the user already has a row
    user_row = await fetch_user_row(bot, user_id)

    if user_row and user_row.get("reminders"):
        # ✅ Row exists → use existing reminders
        merged_reminders = user_row["reminders"]
    else:
        # ❌ Row doesn't exist → try creating it in DB
        defaults = {
            "relics": {"mode": "off"},
            "catchbot": {"mode": "off"},
        }
        try:
            merged_reminders = await upsert_user_reminders(
                bot,
                user_id,
                interaction.user.name,
                defaults,
            )
            if not merged_reminders:
                await interaction.edit_original_response(
                    content="⚠️ Failed to initialize reminders. Please try again later.",
                    view=None,
                )
                return
        except Exception as e:
            await interaction.edit_original_response(
                content=f"⚠️ Error creating reminders row: {e}",
                view=None,
            )
            return

        # 🔄 Refresh cache after insert
        bot.loop.create_task(load_user_reminders_cache(bot=bot))

    # Pass merged reminders directly to the view
    view = ReminderSelectView(bot, user_id, merged_reminders)
    await interaction.edit_original_response(
        content="Select a category to modify its settings.",
        view=view,
    )
