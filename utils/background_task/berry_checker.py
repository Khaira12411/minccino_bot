import discord
import time

from config.aesthetic import *
from config.current_setup import KHY_USER_ID, STRAYMONS_GUILD_ID
from config.straymons_constants import STRAYMONS__TEXT_CHANNELS
from utils.database.berry_reminder import (
    fetch_all_due_berry_reminders,
    remove_berry_reminder,
)
from utils.essentials.pokemeow_helpers import get_pokemeow_reply_member
from utils.loggers.debug_log import debug_log, enable_debug
from utils.loggers.pretty_logs import pretty_log

enable_debug(f"{__name__}.berry_reminder_checker")

berry_map = {
    "oran berry": Emojis.oran_berry,
    "cheri berry": Emojis.cheri_berry,
    "rawst berry": Emojis.rawst_berry,
    "pecha berry": Emojis.pecha_berry,
    "aspear berry": Emojis.aspear_berry,
    "sitrus berry": Emojis.sitrus_berry,
    "salac berry": Emojis.salac_berry,
    "chesto berry": Emojis.chesto_berry,
    "persim berry": Emojis.persim_berry,
    "pomeg berry": Emojis.pomeg_berry,
    "kelpsy berry": Emojis.kelpsy_berry,
    "qualot berry": Emojis.qualot_berry,
    "hondew berry": Emojis.hondew_berry,
    "grepa berry": Emojis.grepa_berry,
    "tamato berry": Emojis.tomato_berry,
    "lum berry": Emojis.lum_berry,
    "occa berry": Emojis.occa_berry,
    "yache berry": Emojis.yache_berry,
    "shuca berry": Emojis.shuca_berry,
}


# 🍥──────────────────────────────────────────────
#   Berry Reminder Checker Task
# 🍥──────────────────────────────────────────────
async def berry_reminder_checker(bot: discord.Client):
    """Checks for upcoming berry reminders and sends notifications."""


    due_reminders = await fetch_all_due_berry_reminders(bot)

    if not due_reminders:
        return
    guild = bot.get_guild(STRAYMONS_GUILD_ID)

    # Group reminders by user and channel ONLY
    from collections import defaultdict

    due_reminders_count = len(due_reminders)
    debug_log(f"Fetched {due_reminders_count} due berry reminders from the database.")
    user_channel_reminders = defaultdict(list)

    for reminder in due_reminders:
        # Extra debug: show remind_on vs current time
        now_epoch = int(time.time())
        debug_log(
            f"Processing reminder: {reminder} | remind_on={reminder['remind_on']} | now={now_epoch}"
        )
        key = (
            reminder["user_id"],
            reminder["user_name"],
            reminder["channel_id"],
            reminder["channel_name"],
        )
        user_channel_reminders[key].append(reminder)

    for (
        user_id,
        user_name,
        channel_id,
        channel_name,
    ), reminders in user_channel_reminders.items():
        debug_log(
            f"Handling reminders for user_id={user_id}, user_name={user_name}, "
            f"channel_id={channel_id}, channel_name={channel_name}, reminders_count={len(reminders)}"
        )

        # Sort by slot_number for consistency
        user = guild.get_member(user_id)
        debug_log(f"Fetched user: {user} for user_id={user_id}")
        mention = user.mention if user else user_name
        reminders.sort(key=lambda r: r["slot_number"])

        berry_names = []
        for reminder in reminders:
            berry_name_raw = reminder["berry_name"]
            berry_emoji = berry_map.get(berry_name_raw.lower(), "")
            berry_name = f"{berry_emoji} {berry_name_raw.title()}".strip()
            berry_names.append(berry_name)
            debug_log(f"Prepared berry name: {berry_name} (raw: {berry_name_raw})")

        # Compose message depending on how many berries are due
        if len(berry_names) == 1:
            msg = f"{Emojis.mouse_farmer} Hey {mention}! its time to check your {berry_names[0]} thru `;berry` command!"
        elif len(berry_names) == 2:
            msg = f"{Emojis.mouse_farmer} Hey {mention}! its time to check your {berry_names[0]} and {berry_names[1]} thru `;berry` command!"
        else:
            msg = f"{Emojis.mouse_farmer} Hey {mention}, its time to check your berries ({', '.join(berry_names)}) using the `;berry` command"

        debug_log(f"Composed message: {msg}")

        # Send to the correct channel in the correct guild
        for guild in bot.guilds:
            debug_log(
                f"Checking guild: {guild} (ID: {guild.id}) for channel_id={channel_id}"
            )
            channel = guild.get_channel(channel_id)
            if channel and channel.name == channel_name:
                debug_log(
                    f"Found channel: {channel} (name: {channel.name}) in guild: {guild.name}"
                )
                try:
                    await channel.send(msg)
                    pretty_log(
                        "background_task",
                        f"Sent berry reminder for {user_name} (user_id: {user_id}) for berries: {', '.join(berry_names)}",
                        bot=bot,
                    )
                    debug_log(
                        f"Sent message to channel {channel.name} (ID: {channel.id}) for user {user_name} (ID: {user_id})"
                    )

                    # Remove each berry reminder after sending — use the actual reminder slot_number
                    for reminder in reminders:
                        debug_log(
                            f"Removing berry reminder for user_id={user_id}, slot_number={reminder['slot_number']}"
                        )
                        await remove_berry_reminder(
                            bot, user_id, slot_number=reminder["slot_number"]
                        )

                except Exception as e:
                    pretty_log(
                        "error",
                        f"Failed to send berry reminder for {user_name} (user_id: {user_id}): {e}",
                        bot=bot,
                    )
                    debug_log(
                        f"Exception occurred while sending/removing berry reminder: {e}"
                    )
