import re
from datetime import datetime

import discord

from config.current_setup import POKEMEOW_APPLICATION_ID
from group_func.toggle.reminders.reminders_sched_db_func import (
    delete_user_schedule,
    upsert_user_schedule,
)
from group_func.toggle.reminders.user_reminders_db_func import *
from utils.cache.reminders_cache import user_reminders_cache
from utils.loggers.debug_log import debug_log, enable_debug
from utils.loggers.pretty_logs import pretty_log

#enable_debug(f"{__name__}.handle_catchbot_message")

# Patterns
CATCHBOT_RUN_PATTERN = re.compile(
    r"to run your catch bot.*?It will be back with.*?in \*\*(\d+)([hHmM])\*\*",
    re.IGNORECASE | re.DOTALL,
)

CATCHBOT_EMBED_PATTERN = re.compile(
    r"It will be back on [^<]*<t:(\d+):f>", re.IGNORECASE
)
CHECKLIST_CB_PATTERN = re.compile(
    r"Your catch bot will be back on [^<]*<t:(\d+):f>", re.IGNORECASE
)
CATCHBOT_RETURNED_PATTERN = re.compile(
    r":confetti_ball: \*\*Your catchbot returned with \d+ Pokemon!?\*\*", re.IGNORECASE
)


async def handle_catchbot_message(bot, message: discord.Message):
    """
    Central handler for CatchBot-related messages.
    Processes messages for users whose catchbot.mode != 'off'.
    """
    try:
        if message.author.id != POKEMEOW_APPLICATION_ID:
            return None

        if not message.reference or not getattr(message.reference, "resolved", None):
            return None
        user = message.reference.resolved.author
        if not user:
            return None

        reminders = user_reminders_cache.get(user.id, {})
        cb_mode = reminders.get("catchbot", {}).get("mode", "off")
        if cb_mode == "off":
            return None

        debug_log(f"Processing message {message.id} for user {user.id}")
        content = message.content or ""
        debug_log(f"Message content: {content}")

        # 1️⃣ Check CATCHBOT_RUN_PATTERN in content
        run_match = CATCHBOT_RUN_PATTERN.search(content)
        if run_match:
            debug_log(f"CATCHBOT_RUN_PATTERN matched: {run_match.groups()}")
            value, unit = run_match.groups()
            value = int(value)
            seconds = value * (3600 if unit.lower() == "h" else 60)
            timestamp = int(message.created_at.timestamp()) + seconds
            debug_log(f"Run duration {value}{unit} → timestamp {timestamp}")

            try:
                await message.reference.resolved.add_reaction("📅")
            except Exception as e:
                debug_log(f"Failed to add reaction: {e}")

            return await extract_and_save_catchbot_schedule(bot, user, timestamp)

        # 2️⃣ Combine all embed content (description + fields)
        texts_to_check = []
        if message.embeds:
            for idx, embed in enumerate(message.embeds):
                desc_text = embed.description or ""
                texts_to_check.append(desc_text)
                for field in embed.fields:
                    texts_to_check.append(f"{field.name}\n{field.value}")
                debug_log(
                    f"Embed {idx} combined text for pattern check:\n{desc_text}\n"
                    + "\n".join(f"{f.name}: {f.value}" for f in embed.fields),
                )

        combined_text = "\n".join(texts_to_check)

        # 3️⃣ Search all patterns in combined text
        embed_match = CATCHBOT_EMBED_PATTERN.search(combined_text)
        checklist_match = CHECKLIST_CB_PATTERN.search(combined_text)
        returned_match = CATCHBOT_RETURNED_PATTERN.search(combined_text)

        debug_log(
            f"Combined text matches -> EMBED:{bool(embed_match)} "
            f"CHECKLIST:{bool(checklist_match)} RETURNED:{bool(returned_match)}"
        )

        if embed_match or checklist_match:
            ts = int((embed_match or checklist_match).group(1))
            debug_log(f"Timestamp found: {ts}")
            try:
                await message.reference.resolved.add_reaction("📅")
            except Exception as e:
                debug_log(f"Failed to add reaction: {e}")
            return await extract_and_save_catchbot_schedule(bot, user, ts)

        if returned_match:
            debug_log(f"Catchbot returned found, deleting schedule for user {user.id}")
            await delete_user_schedule(bot, user.id, "catchbot")
            if "catchbot" in reminders:
                reminders["catchbot"]["expiration_timestamp"] = None
            user_reminders_cache[user.id] = reminders
            return "deleted"

    except Exception as e:
        pretty_log(
            "error", f"Failed to handle catchbot message {message.id}: {e}", bot=bot
        )

    return None


async def extract_and_save_catchbot_schedule(
    bot, user: discord.User | discord.Member, timestamp: int
):
    """
    Upsert user's catchbot schedule, update cache, DB table, and nested reminders JSON.
    """
    try:
        reminders = user_reminders_cache.get(user.id, {})
        cb_settings = reminders.get("catchbot", {"mode": "off"})
        cb_mode = cb_settings.get("mode", "off")
        if cb_mode == "off":
            return None

        debug_log(f"Processing user {user.id} with catchbot_mode={cb_mode}")

        current_ts = reminders.get("catchbot", {}).get("expiration_timestamp")
        if current_ts == timestamp:
            debug_log(f"User {user.id} schedule unchanged ({timestamp}). Skipping.")
            return None

        repeating = cb_settings.get("repeating")
        reminds_next_on = timestamp + int(repeating) * 60 if repeating else None

        await upsert_user_schedule(
            bot=bot,
            user_id=user.id,
            user_name=user.name,
            type_="catchbot",
            ends_on=timestamp,
            remind_next_on=reminds_next_on,
        )

        if "catchbot" not in reminders:
            reminders["catchbot"] = {}
        reminders["catchbot"]["returns_on"] = timestamp
        if reminds_next_on:
            reminders["catchbot"]["reminds_next_on"] = reminds_next_on

        user_reminders_cache[user.id] = reminders

        updates = {"catchbot.returns_on": timestamp}
        if reminds_next_on:
            updates["catchbot.reminds_next_on"] = reminds_next_on

        await update_user_reminders_fields(bot, user.id, user.name, updates=updates)

        debug_log(f"Updated cache & DB for user {user.id} with timestamp {timestamp}")
        pretty_log(
            "info", f"Saved catchbot schedule {timestamp} for user {user.id}", bot=bot
        )
        return timestamp

    except Exception as e:
        pretty_log(
            "error",
            f"Failed to save catchbot schedule for user {user.id}: {e}",
            bot=bot,
        )
        return None
