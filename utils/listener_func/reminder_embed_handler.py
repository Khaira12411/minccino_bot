import re
from datetime import datetime

import discord

from group_func.toggle.reminders.reminders_sched_db_func import (
    mark_reminder_sent,
    update_catchbot_reminds_next_on,
)
from utils.cache.reminders_cache import user_reminders_cache
from utils.loggers.pretty_logs import pretty_log

CC_BOT_LOG_ID = 1413576563559239931
WOOPER_ID = 1388515441592504483
TIMESTAMP_REGEX = re.compile(r"<t:(\d+):f>")


# 🍭 Get a registered personal channel
async def get_registered_personal_channel(
    bot: discord.Client, user_id: int
) -> int | None:
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT channel_id FROM personal_channels WHERE user_id = $1", user_id
            )
            return row["channel_id"] if row else None
    except Exception as e:
        pretty_log("warn", f"Failed to fetch personal channel for user {user_id}: {e}")
        return None


async def handle_reminder_embed(bot: discord.Client, message: discord.Message):
    """
    Reads embeds sent by Wooper in CC_BOT_LOG_ID,
    parses the fields, and sends notifications to the user.
    Logs every reason a message/embed is skipped.
    """

    # --- Skip if not in CC log channel ---
    if message.channel.id != CC_BOT_LOG_ID:
        pretty_log(
            "debug",
            f"Skipping message {message.id}: not in CC_BOT_LOG_ID ({message.channel.id})",
        )
        return

    # --- Skip if no embeds ---
    if not message.embeds:
        pretty_log("debug", f"Skipping message {message.id}: no embeds found")
        return

    for idx, embed in enumerate(message.embeds, start=1):
        # --- Debug: log full embed contents ---
        try:
            fields_preview = (
                {field.name: field.value for field in embed.fields}
                if embed.fields
                else {}
            )

            pretty_log(
                "debug",
                f"[Embed #{idx} in message {message.id}] "
                f"title='{embed.title}', "
                f"description='{embed.description}', "
                f"fields={fields_preview}",
            )
        except Exception as e:
            pretty_log(
                "warn", f"Failed to log embed preview in message {message.id}: {e}"
            )

        # --- Parse embed fields ---
        try:
            embed_fields = {field.name: field.value for field in embed.fields}

            reminder_type = embed_fields.get("Reminder Type", "").lower()
            user_mention = embed.description or ""
            user_id_str = re.sub(r"\D", "", user_mention)
            if not user_id_str:
                pretty_log(
                    "warn",
                    f"Skipping embed {idx}: could not extract user ID from description '{user_mention}'",
                )
                continue
            user_id = int(user_id_str)

            ends_on_field = embed_fields.get("Ends on")
            next_on_field = embed_fields.get("Next catchbot check")
            reminder_id_raw = embed_fields.get("Reminder ID")
            if reminder_id_raw is None:
                pretty_log(
                    "warn",
                    f"Skipping embed {idx}: missing Reminder ID for user {user_id}",
                )
                continue
            try:
                reminder_id = int(reminder_id_raw)
            except ValueError:
                pretty_log(
                    "warn",
                    f"Skipping embed {idx}: invalid Reminder ID '{reminder_id_raw}' for user {user_id}",
                )
                continue

            ends_on_ts = (
                int(TIMESTAMP_REGEX.search(ends_on_field).group(1))
                if ends_on_field and TIMESTAMP_REGEX.search(ends_on_field)
                else None
            )
            next_on_ts = (
                int(TIMESTAMP_REGEX.search(next_on_field).group(1))
                if next_on_field and TIMESTAMP_REGEX.search(next_on_field)
                else None
            )

        except Exception as e:
            pretty_log(
                "warn",
                f"Skipping embed {idx}: failed to parse fields in message {message.id}: {e}",
            )
            continue

        # --- Fetch user ---
        try:
            user = bot.get_user(user_id)
            if not user:
                pretty_log("warn", f"Skipping embed {idx}: user not found {user_id}")
                continue
        except Exception as e:
            pretty_log(
                "warn", f"Skipping embed {idx}: failed to fetch user {user_id}: {e}"
            )
            continue

        # --- Determine target channel ---
        try:
            channel_id = await get_registered_personal_channel(bot, user_id)
            target_channel = (
                bot.get_channel(channel_id)
                if channel_id
                else user.dm_channel or await user.create_dm()
            )
            if not target_channel:
                pretty_log(
                    "warn",
                    f"Skipping embed {idx}: no target channel for user {user_id}",
                )
                continue
        except Exception as e:
            pretty_log(
                "warn",
                f"Skipping embed {idx}: failed to get target channel for user {user_id}: {e}",
            )
            continue

        # --- Send notifications ---
        try:
            if reminder_type == "catchbot":
                if next_on_ts:
                    await target_channel.send(
                        f"{user.mention}, your catchbot needs attention! "
                        f"Next return: <t:{next_on_ts}:f>"
                    )
                    repeating = (
                        user_reminders_cache.get(user_id, {})
                        .get("catchbot", {})
                        .get("repeating", 0)
                    )
                    try:
                        await update_catchbot_reminds_next_on(
                            bot, user_id, minutes=repeating, ends_on=ends_on_ts
                        )
                    except Exception as e:
                        pretty_log(
                            "warn",
                            f"Failed to update next catchbot reminder for user {user_id}: {e}",
                        )
                else:
                    try:
                        await mark_reminder_sent(bot, reminder_id)
                    except Exception as e:
                        pretty_log(
                            "warn",
                            f"Failed to mark reminder {reminder_id} as sent for user {user_id}: {e}",
                        )

            elif reminder_type == "relics":
                await target_channel.send(
                    f"{user.mention}, your relics exchange effect has already expired."
                )
            else:
                pretty_log(
                    "debug",
                    f"Skipping embed {idx}: unknown reminder type '{reminder_type}' for user {user_id}",
                )

        except Exception as e:
            pretty_log(
                "warn",
                f"Failed to send notification for user {user_id} in message {message.id}: {e}",
            )

        # --- Clear cache ---
        try:
            if user_id in user_reminders_cache:
                del user_reminders_cache[user_id]
        except Exception as e:
            pretty_log(
                "warn",
                f"Failed to clear cache for user {user_id} in message {message.id}: {e}",
            )
