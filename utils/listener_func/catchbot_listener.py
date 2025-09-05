import re
import inspect
from datetime import datetime
import discord
from group_func.toggle.reminders.user_reminders_db_func import *

from group_func.toggle.reminders.reminders_sched_db_func import (
    upsert_user_schedule,
    delete_user_schedule,
)
from utils.loggers.debug_log import debug_log
from utils.loggers.pretty_logs import pretty_log
from utils.cache.reminders_cache import user_reminders_cache

from config.current_setup import POKEMEOW_APPLICATION_ID  # replace with actual ID

# Patterns
CATCHBOT_RUN_PATTERN = re.compile(
    r"to run your catch bot.*?It will be back with.*?in (\d+)([hHmM])", re.IGNORECASE
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
    Looks in message content, embed descriptions, and all embed fields.
    Reacts with a calendar emoji if a timestamp is found.
    """
    func_name = inspect.currentframe().f_code.co_name

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

        await debug_log(
            func_name, f"Processing message {message.id} for user {user.id}"
        )
        content = message.content or ""
        await debug_log(func_name, f"Message content: {content}")

        # 1️⃣ Check CATCHBOT_RUN_PATTERN in content
        run_match = CATCHBOT_RUN_PATTERN.search(content)
        if run_match:
            await debug_log(
                func_name, f"CATCHBOT_RUN_PATTERN matched: {run_match.groups()}"
            )
            value, unit = run_match.groups()
            value = int(value)
            seconds = value * (3600 if unit.lower() == "h" else 60)
            timestamp = int(message.created_at.timestamp()) + seconds
            await debug_log(
                func_name, f"Run duration {value}{unit} → timestamp {timestamp}"
            )

            # React to original user
            try:
                await message.reference.resolved.add_reaction("📅")
            except Exception as e:
                await debug_log(func_name, f"Failed to add reaction: {e}")

            return await extract_and_save_catchbot_schedule(bot, user, timestamp)

        # 2️⃣ Combine all embed content (description + fields) into one string
        texts_to_check = []
        if message.embeds:
            for idx, embed in enumerate(message.embeds):
                desc_text = embed.description or ""
                texts_to_check.append(desc_text)
                for field in embed.fields:
                    texts_to_check.append(f"{field.name}\n{field.value}")
                await debug_log(
                    func_name,
                    f"Embed {idx} combined text for pattern check:\n{desc_text}\n"
                    + "\n".join(f"{f.name}: {f.value}" for f in embed.fields),
                )

        combined_text = "\n".join(texts_to_check)

        # 3️⃣ Search all patterns in combined text
        embed_match = CATCHBOT_EMBED_PATTERN.search(combined_text)
        checklist_match = CHECKLIST_CB_PATTERN.search(combined_text)
        returned_match = CATCHBOT_RETURNED_PATTERN.search(combined_text)

        await debug_log(
            func_name,
            f"Combined text matches -> EMBED:{bool(embed_match)} "
            f"CHECKLIST:{bool(checklist_match)} RETURNED:{bool(returned_match)}",
        )

        if embed_match or checklist_match:
            ts = int((embed_match or checklist_match).group(1))
            await debug_log(func_name, f"Timestamp found: {ts}")
            # React to original user
            try:
                await message.reference.resolved.add_reaction("📅")
            except Exception as e:
                await debug_log(func_name, f"Failed to add reaction: {e}")
            return await extract_and_save_catchbot_schedule(bot, user, ts)

        if returned_match:
            await debug_log(
                func_name,
                f"Catchbot returned found, deleting schedule for user {user.id}",
            )
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
    Computes reminds_next_on if 'repeating' exists in settings.
    """
    func_name = inspect.currentframe().f_code.co_name

    try:
        reminders = user_reminders_cache.get(user.id, {})
        cb_settings = reminders.get("catchbot", {"mode": "off"})
        cb_mode = cb_settings.get("mode", "off")
        if cb_mode == "off":
            return None  # Skip entirely

        await debug_log(
            func_name, f"Processing user {user.id} with catchbot_mode={cb_mode}"
        )

        current_ts = reminders.get("catchbot", {}).get("expiration_timestamp")
        if current_ts == timestamp:
            await debug_log(
                func_name, f"User {user.id} schedule unchanged ({timestamp}). Skipping."
            )
            return None

        # Compute reminds_next_on if repeating exists
        repeating = cb_settings.get("repeating")
        reminds_next_on = timestamp + int(repeating) * 60 if repeating else None

        # Upsert schedule table
        await upsert_user_schedule(
            bot=bot,
            user_id=user.id,
            user_name=user.name,
            type_="catchbot",
            ends_on=timestamp,
            remind_next_on=reminds_next_on,
        )

        # Update cache
        if "catchbot" not in reminders:
            reminders["catchbot"] = {}
        reminders["catchbot"]["returns_on"] = timestamp  # rename from schedule
        if reminds_next_on:
            reminders["catchbot"]["reminds_next_on"] = reminds_next_on

        user_reminders_cache[user.id] = reminders

        # ✅ Persist updated reminders JSON to DB incrementally (multi-field)
        updates = {"catchbot.returns_on": timestamp}
        if reminds_next_on:
            updates["catchbot.reminds_next_on"] = reminds_next_on

        await update_user_reminders_fields(
            bot,
            user.id,
            user.name,
            updates=updates,
        )


        await debug_log(
            func_name,
            f"Updated cache & DB for user {user.id} with timestamp {timestamp}",
        )

        pretty_log(
            "info",
            f"Saved catchbot schedule {timestamp} for user {user.id}",
            bot=bot,
        )
        return timestamp

    except Exception as e:
        pretty_log(
            "error",
            f"Failed to save catchbot schedule for user {user.id}: {e}",
            bot=bot,
        )
        return None
