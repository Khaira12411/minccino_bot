import inspect
import re

import discord

from config.current_setup import POKEMEOW_APPLICATION_ID
from group_func.toggle.reminders.reminders_sched_db_func import upsert_user_schedule
from utils.loggers.debug_log import debug_log  # centralized debug logger
from utils.loggers.pretty_logs import pretty_log
from group_func.toggle.reminders.user_reminders_db_func import *

# Patterns to extract relic expiration timestamps
RELICS_EMBED_PATTERN = re.compile(
    r"can only exchange them after <t:(\d+):f>", re.IGNORECASE
)
RELICS_SUCCESS_PATTERN = re.compile(
    r"will be able to exchange relics again on <t:(\d+):f>", re.IGNORECASE
)


async def extract_and_save_relics_schedule(
    bot,
    user: discord.User | discord.Member,
    timestamp: int,
    message: discord.Message | None = None,
):
    """
    Upsert user's relics schedule, update cache, DB table, and store in reminders JSON.
    Uses 'expires_on' as the persistent key and reacts with 📅 if message is provided.
    """
    from utils.cache.reminders_cache import user_reminders_cache

    func_name = inspect.currentframe().f_code.co_name

    try:
        reminders = user_reminders_cache.get(user.id, {})
        relics_mode = reminders.get("relics", {}).get("mode", "off")
        if relics_mode == "off":
            return None

        current_ts = reminders.get("relics", {}).get("expiration_timestamp")
        if current_ts == timestamp:
            await debug_log(
                func_name, f"User {user.id} schedule unchanged ({timestamp}). Skipping."
            )
            return None

        # Upsert schedule table
        await upsert_user_schedule(
            bot=bot,
            user_id=user.id,
            user_name=user.name,
            type_="relics",
            ends_on=timestamp,
            remind_next_on=None,
        )

        # Update cache
        if "relics" not in reminders:
            reminders["relics"] = {}
        reminders["relics"]["has_exchanged"] = True
        reminders["relics"]["expires_on"] = timestamp
        user_reminders_cache[user.id] = reminders

        # ✅ Persist in reminders JSON in DB (multi-field, safe)
        await update_user_reminders_fields(
            bot,
            user.id,
            user.name,
            updates={
                "relics.expires_on": timestamp,
                "relics.has_exchanged": True,
            }
        )

        await debug_log(
            func_name,
            f"Updated cache & DB for user {user.id} with expires_on {timestamp}.",
        )

        # React to message if provided
        if message:
            try:
                await message.reference.resolved.add_reaction("📅")
            except Exception as e:
                await debug_log(func_name, f"Failed to add reaction: {e}")

        pretty_log(
            "info",
            f"Saved relics schedule {timestamp} for user {user.id}",
            bot=bot,
        )
        return timestamp

    except Exception as e:
        pretty_log(
            "error",
            f"Failed to save relics schedule for user {user.id}: {e}",
            bot=bot,
        )
        return None


async def handle_relics_message(bot, message: discord.Message):
    """
    Central handler for any relics-related messages.
    Processes messages for users whose relics.mode != 'off'.
    Reacts with a calendar emoji if a timestamp is found.
    """
    func_name = inspect.currentframe().f_code.co_name

    try:
        if message.author.id != POKEMEOW_APPLICATION_ID:
            return None

        if not message.reference or not getattr(message.reference, "resolved", None):
            return None
        replied_user = message.reference.resolved.author
        if not replied_user:
            return None

        from utils.cache.reminders_cache import user_reminders_cache

        reminders = user_reminders_cache.get(replied_user.id, {})
        relics_mode = reminders.get("relics", {}).get("mode", "off")
        if relics_mode == "off":
            return None
        await debug_log(
            func_name, f"Processing message {message.id} for user {replied_user.name}"
        )

        # 1️⃣ Check embed
        if message.embeds:
            embed = message.embeds[0]
            author_name = (
                getattr(embed.author, "name", "").lower() if embed.author else ""
            )
            if author_name.startswith("pokemeow research lab"):
                desc_text = embed.description or ""
                match = RELICS_EMBED_PATTERN.search(desc_text)
                if match:
                    ts = int(match.group(1))
                    await debug_log(
                        func_name, f"Found relics expiration in embed: {ts}"
                    )
                    return await extract_and_save_relics_schedule(
                        bot, replied_user, ts, message
                    )

        # 2️⃣ Check content
        content = message.content or ""
        match = RELICS_SUCCESS_PATTERN.search(content)
        if match:
            ts = int(match.group(1))
            await debug_log(func_name, f"Found relics expiration in content: {ts}")
            return await extract_and_save_relics_schedule(
                bot, replied_user, ts, message
            )

    except Exception as e:
        pretty_log(
            "error", f"Failed to handle relics message {message.id}: {e}", bot=bot
        )

    return None
