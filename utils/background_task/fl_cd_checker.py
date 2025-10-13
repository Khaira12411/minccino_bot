# 🎉 loop_tasks/pokemeow_reminder_checker.py
import asyncio
from datetime import datetime
import discord

from config.aesthetic import *
from config.current_setup import MINCCINO_COLOR, STRAYMONS_GUILD_ID

from utils.loggers.pretty_logs import pretty_log
from utils.database.fl_cd_db_func import remove_feeling_lucky_cd
from utils.database.fl_reminders_db_func import fetch_fl_reminder_db
from config.straymons_constants import STRAYMONS__TEXT_CHANNELS, STRAYMONS__ROLES
# Default Feeling Lucky channel (if user has no personal channel)
FEELING_LUCKY_CHANNEL_ID = STRAYMONS__TEXT_CHANNELS.feeling_lucky  # replace with your actual channel ID


# 🐾────────────────────────────────────────────
#     ✨ Direct Feeling Lucky CD Checker
# 🐾────────────────────────────────────────────
async def fl_cd_checker(bot: discord.Client):
    from utils.cache.fl_cache import feeling_lucky_cache

    now = int(datetime.now().timestamp())  # current Unix timestamp
    expired_users = []

    for user_id, data in list(feeling_lucky_cache.items()):
        cooldown_until = data.get("cooldown_until", 0)
        if now >= cooldown_until:
            expired_users.append(
                {
                    "user_id": user_id,
                    "user_name": data.get("user_name"),
                }
            )

            # Remove from DB & cache
            try:
                await remove_feeling_lucky_cd(bot, user_id)
                user_name = data.get("user_name")
                fl_reminder_info = await fetch_fl_reminder_db(bot=bot, user_id=user_id)
                reminder_type = fl_reminder_info.get("reminder_type")
                channel_id = fl_reminder_info.get("channel_id")

                member = None
                guild = bot.get_guild(STRAYMONS_GUILD_ID)
                if guild:
                    member = guild.get_member(user_id)

                message_text = (
                    f"🍀 {user_name}, you can now use ;find again in <#{FEELING_LUCKY_CHANNEL_ID}>!"
                )
                #Remove role
                fl_cd_role = guild.get_role(STRAYMONS__ROLES.fl_cd)
                if member and fl_cd_role in member.roles:
                    await member.remove_roles(fl_cd_role, reason="Feeling Lucky cooldown expired")

                if reminder_type == "channel":
                    target_channel = bot.get_channel(
                        channel_id or FEELING_LUCKY_CHANNEL_ID
                    )
                    if target_channel:
                        await target_channel.send(message_text)
                        pretty_log(
                            "info",
                            f"Sent Feeling Lucky reminder in channel for {user_name} ({user_id})",
                            label="🍀 FL CD CHECKER",
                            bot=bot,
                        )

                elif reminder_type == "dm":
                    if member:
                        try:
                            await member.send(message_text)
                            pretty_log(
                                "info",
                                f"Sent Feeling Lucky DM reminder to {user_name} ({user_id})",
                                label="🍀 FL CD CHECKER",
                                bot=bot,
                            )
                        except Exception as e:
                            pretty_log(
                                "warn",
                                f"Failed to DM Feeling Lucky reminder to {user_name} ({user_id}): {e}",
                                label="🍀 FL CD CHECKER",
                                bot=bot,
                            )
                else:
                    # reminder_type == "off"
                    pretty_log(
                        "info",
                        f"No reminder sent for {user_name} ({user_id}) – reminder_type is off",
                        label="🍀 FL CD CHECKER",
                        bot=bot,
                    )

                # Small delay to prevent rate limits

                await asyncio.sleep(0.5)

            except Exception as e:
                pretty_log(
                    "error",
                    f"Failed to remove or notify expired Feeling Lucky CD for {user_name} ({user_id}): {e}",
                    label="🍀 FL CD CHECKER",
                    bot=bot,
                )

    """pretty_log(
        "info",
        f"Checked Feeling Lucky cooldowns: {len(expired_users)} expired and removed",
        label="🍀 FL CD CHECKER",
        bot=bot,
    )"""
