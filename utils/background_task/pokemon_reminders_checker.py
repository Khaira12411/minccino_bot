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

            # --- Determine target channel ---
            try:
                channel_id = await get_registered_personal_channel(bot, user_id)
                target_channel = (
                    bot.get_channel(channel_id)
                    if channel_id
                    else user.dm_channel or await user.create_dm()
                )
                if not target_channel:
                    pretty_log("warn", f"No target channel for user {user_id}", bot=bot)
                    continue
            except Exception as e:
                pretty_log(
                    "warn", f"Failed to get target channel for {user_id}: {e}", bot=bot
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

            # --- Clear cache ---
            if user_id in user_reminders_cache:
                del user_reminders_cache[user_id]

        except Exception as e:
            pretty_log(
                "error",
                f"Error processing reminder {reminder.get('reminder_id')}: {e}",
                bot=bot,
            )
