import re
from datetime import datetime

import discord
from discord.ext import commands

from config.current_setup import POKEMEOW_APPLICATION_ID
from group_func.toggle.reminders.reminders_sched_db_func import (
    delete_user_schedule,
    upsert_user_schedule,
    schedule_exists_with_same_ts
)
from group_func.toggle.reminders.user_reminders_db_func import *
from utils.cache.reminders_cache import user_reminders_cache
from utils.essentials.pokemeow_helpers import get_pokemeow_reply_member
from utils.loggers.debug_log import debug_log
from utils.loggers.pretty_logs import pretty_log

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔹 Regex Patterns
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CATCHBOT_RUN_PATTERN = re.compile(r"in \*\*(\d+)([hHmM])\*\*", re.IGNORECASE)
CATCHBOT_EMBED_PATTERN = re.compile(r"It will be back on .*?<t:(\d+):f>", re.IGNORECASE)
CHECKLIST_CB_PATTERN = re.compile(
    r"Your catch bot will be back on <t:(\d+):f>", re.IGNORECASE
)
CATCHBOT_RETURNED_PATTERN = re.compile(
    r":confetti_ball: \*\*Your catchbot returned with \d+ Pokemon!?\*\*",
    re.IGNORECASE,
)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ;cl checklist embed
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def handle_cb_checklist_message(bot: commands.Bot, message: discord.Message):
    if message.author.id != POKEMEOW_APPLICATION_ID:
        return

    embed = message.embeds[0]
    if not embed or not embed.description:
        return

    member = await get_pokemeow_reply_member(message=message)
    if not member:
        return

    # 🔹 Must have reminders row and mode != off
    reminders = user_reminders_cache.get(member.id)
    if not reminders or reminders.get("catchbot", {}).get("mode", "off") == "off":
        return None

    m = CHECKLIST_CB_PATTERN.search(embed.description)
    if not m:
        return

    timestamp = int(m.group(1))
    if not timestamp:
        return

    # 🗂️ Save schedule
    result = await extract_and_save_catchbot_schedule(
        bot=bot, user=member, timestamp=timestamp
    )

    # 📅 React only if new schedule
    if result == "added":
        try:
            await message.reference.resolved.add_reaction("📅")
        except Exception as e:
            pretty_log(
                "warn", f"[CB CHECKLIST] Failed to add 📅 reaction: {e}", bot=bot
            )

    pretty_log(
        "info",
        f"[CB CHECKLIST] Result={result} ts={timestamp} for {member.id}",
        bot=bot,
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ;cb embed
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def handle_cb_command_embed(bot: commands.Bot, message: discord.Message):
    if message.author.id != POKEMEOW_APPLICATION_ID:
        return

    embed = message.embeds[0]
    if not embed:
        return

    member = await get_pokemeow_reply_member(message=message)
    if not member:
        return

    reminders = user_reminders_cache.get(member.id)
    if not reminders or reminders.get("catchbot", {}).get("mode", "off") == "off":
        return None

    # 🔹 1. Try matching timestamp in description
    timestamp = None
    if embed.description:
        m = CATCHBOT_EMBED_PATTERN.search(embed.description)
        if m:
            timestamp = int(m.group(1))
            pretty_log(
                "embed", f"[CB EMBED] Found ts in description: {timestamp}", bot=bot
            )

    # 🔹 2. If not found, try each field value
    if not timestamp:
        for field in embed.fields:
            if not field.value:
                continue
            m = CATCHBOT_EMBED_PATTERN.search(field.value)
            if m:
                timestamp = int(m.group(1))
                pretty_log(
                    "embed",
                    f"[CB EMBED] Found ts in field '{field.name}': {timestamp}",
                    bot=bot,
                )
                break

    # 🔹 3. If still not found, stop
    if not timestamp:
        return

    # 🗂️ Save schedule
    result = await extract_and_save_catchbot_schedule(
        bot=bot, user=member, timestamp=timestamp
    )

    # 📅 React only if new schedule
    if result == "added":
        try:
            await message.reference.resolved.add_reaction("📅")
        except Exception as e:
            pretty_log("warn", f"[CB EMBED] Failed to add 📅 reaction: {e}", bot=bot)

    pretty_log(
        "info", f"[CB EMBED] Result={result} ts={timestamp} for {member.name}", bot=bot
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# ;cb run
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def handle_cb_run_message(bot, message: discord.Message):
    try:
        if message.author.id != POKEMEOW_APPLICATION_ID:
            return None

        if not message.reference or not getattr(message.reference, "resolved", None):
            return None
        user = message.reference.resolved.author
        if not user:
            return None

        reminders = user_reminders_cache.get(user.id)
        if not reminders or reminders.get("catchbot", {}).get("mode", "off") == "off":
            return None

        content = message.content or ""
        run_match = CATCHBOT_RUN_PATTERN.search(content)
        if not run_match:
            return None

        value, unit = run_match.groups()
        value = int(value)
        seconds = value * (3600 if unit.lower() == "h" else 60)
        timestamp = int(message.created_at.timestamp()) + seconds

        # 🗂️ Save schedule
        result = await extract_and_save_catchbot_schedule(bot, user, timestamp)

        # 📅 React if new schedule added
        if result == "added":
            try:
                await message.reference.resolved.add_reaction("📅")
            except Exception as e:
                pretty_log("warn", f"[CB RUN] Failed to add 📅 reaction: {e}", bot=bot)

        pretty_log(
            "info", f"[CB RUN] Result={result} ts={timestamp} for {user.name}", bot=bot
        )

    except Exception as e:
        pretty_log("error", f"[CB RUN] Failed on {message.id}: {e}", bot=bot)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# cb return
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def handle_cb_return_message(bot, message: discord.Message):
    try:
        if message.author.id != POKEMEOW_APPLICATION_ID:
            return None

        if not message.reference or not getattr(message.reference, "resolved", None):
            return None
        user = message.reference.resolved.author
        if not user:
            return None

        reminders = user_reminders_cache.get(user.id)
        if not reminders or reminders.get("catchbot", {}).get("mode", "off") == "off":
            return None

        await delete_user_schedule(bot, user.id, "catchbot")

        # 🔹 Clear catchbot expiration in cache if it exists
        reminders = user_reminders_cache.get(user.id)
        if reminders and "catchbot" in reminders:
            reminders["catchbot"]["expiration_timestamp"] = None
            pretty_log(
                "info",
                f"[CB RETURN] Cleared catchbot expiration_timestamp in cache for {user.name}",
                bot=bot,
            )

        pretty_log(
            "info",
            f"[CB RETURN] Cleared catchbot schedule for {user.name}",
            bot=bot,
        )
        return "deleted"

    except Exception as e:
        pretty_log("error", f"[CB RETURN] Failed on {message.id}: {e}", bot=bot)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Shared save logic
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def extract_and_save_catchbot_schedule(
    bot, user: discord.User | discord.Member, timestamp: int
) -> str:
    """
    Upsert user's catchbot schedule, update cache, DB table, and nested reminders JSON.
    Returns: "added", "unchanged", or "failed"
    """
    try:
        reminders = user_reminders_cache.get(user.id, {})
        cb_settings = reminders.get("catchbot", {"mode": "off"})
        cb_mode = cb_settings.get("mode", "off")
        if cb_mode == "off":
            return "failed"

        # 🔎 Skip if schedule unchanged
        current_ts = reminders.get("catchbot", {}).get("returns_on")
        if current_ts == timestamp:
            pretty_log(
                "debug",
                f"[CB SAVE] Schedule unchanged for {user.name} ({timestamp})",
                bot=bot,
            )
            return "unchanged"

        # ⏰ Calculate next reminder if repeating
        repeating = cb_settings.get("repeating")
        reminds_next_on = timestamp + int(repeating) * 60 if repeating else None

        # 💾 Write to DB
        await upsert_user_schedule(
            bot=bot,
            user_id=user.id,
            user_name=user.name,
            type_="catchbot",
            ends_on=timestamp,
            remind_next_on=reminds_next_on,
        )

        # 🗃️ Update cache
        if "catchbot" not in reminders:
            reminders["catchbot"] = {}
        reminders["catchbot"]["returns_on"] = timestamp
        if reminds_next_on:
            reminders["catchbot"]["reminds_next_on"] = reminds_next_on
        else:
            reminders["catchbot"].pop("reminds_next_on", None)

        user_reminders_cache[user.id] = reminders

        # 📝 Update reminders JSON in DB
        updates = {"catchbot.returns_on": timestamp}
        if reminds_next_on:
            updates["catchbot.reminds_next_on"] = reminds_next_on

        await update_user_reminders_fields(bot, user.id, user.name, updates=updates)

        pretty_log(
            "info", f"[CB SAVE] Stored schedule {timestamp} for {user.name}", bot=bot
        )
        return "added"

    except Exception as e:
        pretty_log("error", f"[CB SAVE] Failed for {user.name}: {e}", bot=bot)
        return "failed"
