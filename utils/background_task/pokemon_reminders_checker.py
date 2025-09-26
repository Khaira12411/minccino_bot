# 🎉 loop_tasks/pokemeow_reminder_checker.py
import re
from datetime import datetime

import discord

from config.aesthetic import *
from config.current_setup import MINCCINO_COLOR, STRAYMONS_GUILD_ID
from group_func.toggle.reminders.reminders_sched_db_func import (
    delete_reminder,
    fetch_all_schedules,
    mark_reminder_sent,
    update_catchbot_reminds_next_on,
)
from utils.cache.reminders_cache import user_reminders_cache
from utils.loggers.pretty_logs import pretty_log

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


from datetime import datetime

import discord


def build_reminder_embed(
    user: discord.Member,
    reminder_type: str,
    title: str | None = None,
    description: str | None = None,
    remind_next_on: int | None = None,
) -> discord.Embed:
    """
    Generic reminder embed builder.

    Parameters:
    - user: discord.Member → who the reminder is for
    - reminder_type: str → type of reminder (catchbot, relics, etc.)
    - title: optional custom title
    - description: optional custom description (list of instructions)
    - remind_next_on: optional timestamp for repeating reminders
    """

    # Default titles & descriptions per type
    default_data = {
        "catchbot": {
            "title": f"{Emojis.robot} Your Catchbot Has Returned!",
            "description": (
                "Don't forget to do:\n"
                "- `;cb` to get the Pokémon\n"
                "- `;cb run` to run it again"
            ),
            "repeating_text": "If you don't run your catchbot, I would gladly remind you again on <t:{remind_next_on}:f> ⏰",
        },
        "relics": {
            "title": f"{Emojis.relic} Relics Exchange Effect Expired",
            "description": (
                "- Exchange 4 Relics again, for a chance to get Special Battle Items from held items mon"
            ),
        },
        # Add future reminder types here
    }

    data = default_data.get(reminder_type, {})
    embed_title = title or data.get("title", "🔔 Reminder!")
    embed_desc = description or data.get(
        "description", "- Don't forget to check this reminder!"
    )

    # Append repeating line if exists
    if remind_next_on and data.get("repeating_text"):
        embed_desc += (
            f"\n\n{data['repeating_text'].format(remind_next_on=remind_next_on)}"
        )

    embed = discord.Embed(
        title=embed_title,
        description=embed_desc,
        color=MINCCINO_COLOR,
        timestamp=datetime.now(),
    )
    guild = user.guild
    embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)
    embed.set_footer(text="Minccino Reminder System", icon_url=guild.icon.url)

    return embed


# 🐾────────────────────────────────────────────
#     ✨ Direct Reminder Checker with Embeds
# 🐾────────────────────────────────────────────
async def pokemon_reminder_checker(bot: discord.Client):
    now = datetime.now().timestamp()

    # --- Fetch all active reminders ---
    try:
        active_reminders = await fetch_all_schedules(bot)
        if not active_reminders:
            return
    except Exception as e:
        pretty_log("error", f"Failed to fetch active reminders: {e}", bot=bot)
        return

    # --- Get guild object ---
    guild = bot.get_guild(STRAYMONS_GUILD_ID)
    if not guild:
        pretty_log("error", f"Guild {STRAYMONS_GUILD_ID} not found.", bot=bot)
        return

    # --- Process each reminder ---
    for reminder in active_reminders:
        try:
            user_id = reminder.get("user_id")
            reminder_id = reminder.get("reminder_id")
            reminder_type = reminder.get("type", "").lower()
            ends_on = reminder.get("ends_on")
            remind_next_on = reminder.get("remind_next_on")
            reminder_sent = reminder.get("reminder_sent", False)

            ends_on_ts = (
                int(ends_on.timestamp())
                if isinstance(ends_on, datetime)
                else int(ends_on or 0)
            )
            remind_next_on_ts = (
                int(remind_next_on.timestamp())
                if isinstance(remind_next_on, datetime)
                else int(remind_next_on or 0)
            )

            # --- Get user ---
            user = guild.get_member(user_id)
            if not user:
                pretty_log("warn", f"User {user_id} not found in guild.", bot=bot)
                continue

            # --- Determine target channel based on mode ---
            reminders_cache = user_reminders_cache.get(user_id, {})
            mode = reminders_cache.get(reminder_type, {}).get("mode", "channel")

            if mode == "off":
                pretty_log(
                    "skip",
                    f"[REMINDER] Skipped reminder {reminder_id} for {user_id} (mode=off)",
                    bot=bot,
                )
                continue

            target_channel = None
            mode = mode.lower()
            if mode == "channel":
                channel_id = await get_registered_personal_channel(bot, user_id)
                if channel_id:
                    target_channel = bot.get_channel(channel_id)
            elif mode == "dms":
                target_channel = user.dm_channel or await user.create_dm()

            if not target_channel:
                pretty_log(
                    "warn",
                    f"[REMINDER] No target channel for {user_id} (mode={mode})",
                    bot=bot,
                )
                continue

            # --- Handle relics & other standard reminders ---
            if reminder_type not in ["catchbot"]:
                if now >= ends_on_ts and not reminder_sent:
                    try:
                        embed = build_reminder_embed(user, reminder_type)
                        content = user.mention
                        if reminder_type == "relics":
                            content = f"{user.mention}, your Relics Exchange effect has expired"

                        await target_channel.send(embed=embed, content=content)

                        # 🔹 Delete immediately since relics never repeat
                        await delete_reminder(bot, reminder_id)
                        await clear_expired_reminder_fields(
                            bot=bot, user_id=user_id, reminder_type="relics"
                        )
                        pretty_log(
                            "info",
                            f"Sent {reminder_type} reminder {reminder_id} to {user_id}",
                        )
                    except Exception as e:
                        pretty_log(
                            "error",
                            f"Failed to send {reminder_type} reminder for {user_id}: {e}",
                            bot=bot,
                        )

            # --- Catchbot reminder ---
            elif reminder_type == "catchbot":
                try:
                    reminders_cache = user_reminders_cache.get(user_id, {}).get(
                        "catchbot", {}
                    )
                    repeating = reminders_cache.get("repeating", 0)

                    # only act if ends_on has passed
                    if now >= ends_on_ts:
                        # 🔹 First fire
                        if not reminder_sent:
                            embed = build_reminder_embed(
                                user,
                                "catchbot",
                                remind_next_on=(
                                    remind_next_on_ts if remind_next_on_ts else None
                                ),
                            )
                            content = f"{user.mention}, your catchbot has returned!"
                            await target_channel.send(embed=embed, content=content)

                            if repeating:
                                await update_catchbot_reminds_next_on(
                                    bot, user_id, minutes=repeating, ends_on=ends_on_ts
                                )
                            else:
                                await delete_reminder(bot, reminder_id)
                                await clear_expired_reminder_fields(
                                    bot=bot, user_id=user_id, reminder_type="catchbot"
                                )
                                reminders_cache = user_reminders_cache.get(user_id)

                                if reminders_cache and "catchbot" in reminders_cache:
                                    reminders_cache = reminders_cache[
                                        "catchbot"
                                    ]  # now this is a real reference
                                    reminders_cache["expiration_timestamp"] = None

                                    pretty_log(
                                        "info",
                                        f"[CB CLEANUP] Set catchbot expiration_timestamp=None for user {user_id} in cache",
                                        bot=bot,
                                    )
                                else:
                                    pretty_log(
                                        "skip",
                                        f"[CB CLEANUP] Skipped cache cleanup → no catchbot entry for user {user_id}",
                                        bot=bot,
                                    )

                            pretty_log(
                                "info",
                                f"Sent catchbot reminder {reminder_id} to {user_id}",
                            )

                        # 🔹 Repeating reminders
                        elif (
                            repeating and remind_next_on_ts and now >= remind_next_on_ts
                        ):
                            embed = build_reminder_embed(
                                user,
                                "catchbot",
                                remind_next_on=remind_next_on_ts,
                            )
                            await target_channel.send(embed=embed)

                            await update_catchbot_reminds_next_on(
                                bot, user_id, minutes=repeating, ends_on=ends_on_ts
                            )

                            pretty_log(
                                "info",
                                f"Sent repeating catchbot reminder {reminder_id} to {user_id}",
                            )

                except Exception as e:
                    pretty_log(
                        "error",
                        f"Failed to handle catchbot reminder for {user_id}: {e}",
                        bot=bot,
                    )



        except Exception as e:
            pretty_log(
                "error",
                f"Error processing reminder {reminder.get('reminder_id')}: {e}",
                bot=bot,
            )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🧹 Helper: Clear expired reminder fields by type (cache + DB)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
import json


async def clear_expired_reminder_fields(bot, user_id: int, reminder_type: str):
    """
    Safely clears expired fields in both cache and DB for a given reminder type.

    - bot: discord.Client → has pg_pool
    - user_id: int → target user
    - reminder_type: str → which reminder to clear (e.g., "relics", "catchbot")
    """
    reminders = user_reminders_cache.get(user_id)
    if not reminders or reminder_type not in reminders:
        pretty_log(
            "debug",
            f"[REMINDER] No cache found for {reminder_type} → {user_id}, skip.",
            bot=bot,
        )
        return

    entry = reminders[reminder_type]
    changed = False

    if reminder_type == "relics":
        if entry.get("expiration_timestamp") is not None:
            entry["expiration_timestamp"] = None
            changed = True
            pretty_log(
                "info",
                f"[REMINDER] Cleared relics expiration_timestamp for {user_id}",
                bot=bot,
            )

    elif reminder_type == "catchbot":
        if "returns_on" in entry:
            entry["returns_on"] = None
            changed = True
            pretty_log(
                "info",
                f"[REMINDER] Cleared catchbot returns_on for {user_id}",
                bot=bot,
            )

        if not entry.get("repeating"):
            # remove keys completely if no repeating
            entry.pop("returns_on", None)
            entry.pop("reminds_next_on", None)
            changed = True
            pretty_log(
                "info",
                f"[REMINDER] Removed catchbot schedule (no repeat) for {user_id}",
                bot=bot,
            )

    # 🔹 Push updates to DB if changes happened
    if changed:
        try:
            async with bot.pg_pool.acquire() as conn:
                await conn.execute(
                    """
                    UPDATE user_pokemeow_reminders
                    SET reminders = $2
                    WHERE user_id = $1
                    """,
                    user_id,
                    json.dumps(reminders),
                )
            pretty_log(
                "db",
                f"[REMINDER] Synced cleanup of {reminder_type} for {user_id} → DB updated",
                bot=bot,
            )
        except Exception as e:
            pretty_log(
                "error",
                f"[REMINDER] Failed DB cleanup sync for {reminder_type} → {user_id}: {e}",
                bot=bot,
            )
