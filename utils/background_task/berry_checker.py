import time

import discord

from config.aesthetic import *
from config.current_setup import KHY_USER_ID, STRAYMONS_GUILD_ID
from config.straymons_constants import STRAYMONS__TEXT_CHANNELS
from utils.database.berry_reminder import (
    fetch_all_due_berry_reminders,
    remove_berry_reminder,
    update_growth_stage,
)
from utils.essentials.pokemeow_helpers import get_pokemeow_reply_member
from utils.loggers.debug_log import debug_log, enable_debug
from utils.loggers.pretty_logs import pretty_log

enable_debug(f"{__name__}.berry_reminder_checker")

berry_map = {
    "oran berry": {"emoji": Emojis.oran_berry, "growth_duration": 2},
    "cheri berry": {"emoji": Emojis.cheri_berry, "growth_duration": 2},
    "rawst berry": {"emoji": Emojis.rawst_berry, "growth_duration": 2},
    "pecha berry": {"emoji": Emojis.pecha_berry, "growth_duration": 2},
    "aspear berry": {"emoji": Emojis.aspear_berry, "growth_duration": 2},
    "sitrus berry": {"emoji": Emojis.sitrus_berry, "growth_duration": 2},
    "salac berry": {"emoji": Emojis.salac_berry, "growth_duration": 6},
    "chesto berry": {"emoji": Emojis.chesto_berry, "growth_duration": 3},
    "persim berry": {"emoji": Emojis.persim_berry, "growth_duration": 3},
    "pomeg berry": {"emoji": Emojis.pomeg_berry, "growth_duration": 4},
    "kelpsy berry": {"emoji": Emojis.kelpsy_berry, "growth_duration": 4},
    "qualot berry": {"emoji": Emojis.qualot_berry, "growth_duration": 4},
    "hondew berry": {"emoji": Emojis.hondew_berry, "growth_duration": 4},
    "grepa berry": {"emoji": Emojis.grepa_berry, "growth_duration": 4},
    "tamato berry": {"emoji": Emojis.tomato_berry, "growth_duration": 4},
    "lum berry": {"emoji": Emojis.lum_berry, "growth_duration": 5},
    "occa berry": {"emoji": Emojis.occa_berry, "growth_duration": 5},
    "yache berry": {"emoji": Emojis.yache_berry, "growth_duration": 5},
    "shuca berry": {"emoji": Emojis.shuca_berry, "growth_duration": 5},
}

next_stage_map = {
    "planted": "sprouted",
    "sprouted": "taller",
    "taller": "blooming",
    "blooming": "berry",
}


async def update_growth_stage_func(
    bot: discord.Client, user_id: int, slot_number: int, stage: str, berry_name: str
):
    """Updates the growth stage and grows_on time for a specific berry reminder."""
    try:
        growth_duration = berry_map.get(berry_name.lower(), {}).get(
            "growth_duration", 2
        )
        # Multiply by 3600 to convert hours to seconds
        grows_on = int(time.time()) + growth_duration * 3600
        await update_growth_stage(bot, user_id, slot_number, stage, grows_on)
    except Exception as e:
        pretty_log(
            "warn",
            f"Failed to update growth stage for user {user_id} in slot {slot_number}: {e}",
        )


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
        # Extra debug: show grows_on vs current time
        now_epoch = int(time.time())
        debug_log(
            f"Processing reminder: {reminder} | grows_on={reminder['grows_on']} | now={now_epoch}"
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

        to_be_watered_berry_names = []
        to_be_harvested_berry_names = []
        for reminder in reminders:
            water_can_type = reminder.get("water_can_type", "unknown")
            stage = reminder.get("stage", "unknown")
            next_stage = next_stage_map.get(reminder["stage"], "unknown")
            mulch_type = reminder.get("mulch_type", "unknown")
            slot_number = reminder["slot_number"]
            context = "watering stage"
            berry_name_raw = reminder["berry_name"]
            slot_number = reminder["slot_number"]
            berry_emoji = berry_map[berry_name_raw]["emoji"]
            if water_can_type != "unknown" and stage != "unknown":
                if water_can_type.lower() == "sprayduck":
                    if next_stage.lower() != "berry":
                        await update_growth_stage_func(
                            bot,
                            user_id,
                            slot_number,
                            next_stage,
                            reminder["berry_name"],
                        )
                        continue  # Skip sending reminder if already watered with sprayduck
                    else:
                        context = "harvest stage"

                elif water_can_type.lower() == "wailmer pail":
                    if mulch_type.lower() == "damp mulch":
                        await update_growth_stage_func(
                            bot,
                            user_id,
                            slot_number,
                            next_stage,
                            reminder["berry_name"],
                        )
                        continue  # Skip sending reminder if already watered with wailmer pail and has damp mulch
                    else:
                        if next_stage.lower() not in ["taller", "berry"]:
                            await update_growth_stage_func(
                                bot,
                                user_id,
                                slot_number,
                                next_stage,
                                reminder["berry_name"],
                            )
                            continue  # Skip sending reminder if already watered with wailmer pail and stage is not taller or berry
                        else:
                            if next_stage.lower() == "berry":
                                context = "harvest stage"
                            else:
                                context = "watering stage"
                                # Remove reminder cuz growth is paused and won't progress to next stage until watered with wailmer pail again
                                await remove_berry_reminder(
                                    bot, user_id, slot_number=slot_number
                                )

            berry_name = (
                f"{berry_emoji} {berry_name_raw.title()} (Slot {slot_number})".strip()
            )
            if context == "watering stage":
                to_be_watered_berry_names.append(berry_name)
            else:
                to_be_harvested_berry_names.append(berry_name)

            debug_log(f"Prepared berry name: {berry_name} (raw: {berry_name_raw})")

        # Compose message depending on how many berries are due
        to_be_watered_field_name = (
            "Berries to be watered. Use `;berry water` to water them:"
        )
        to_be_harvested_field_name = (
            "Berries to be harvested. Use `;berry harvest` to harvest them:"
        )
        embed = discord.Embed(color=0x66CC66)
        if to_be_watered_berry_names:
            embed.add_field(
                name=to_be_watered_field_name,
                value="\n".join(to_be_watered_berry_names),
                inline=False,
            )
        if to_be_harvested_berry_names:
            embed.add_field(
                name=to_be_harvested_field_name,
                value="\n".join(to_be_harvested_berry_names),
                inline=False,
            )
        msg = f"{Emojis.mouse_farmer} Hey {mention}, its time to check your berries!"

        debug_log(f"Composed message: {msg}")

        # Send to the correct channel using bot.get_channel
        channel = bot.get_channel(channel_id)
        if channel and channel.name == channel_name:
            debug_log(
                f"Found channel: {channel} (name: {channel.name}) in guild: {channel.guild.name}"
            )
            try:
                await channel.send(content=msg, embed=embed)
                pretty_log(
                    "background_task",
                    f"Sent berry reminder for {user_name} (user_id: {user_id}) in channel {channel.name} (ID: {channel.id})",
                    bot=bot,
                )
                debug_log(
                    f"Sent message to channel {channel.name} (ID: {channel.id}) for user {user_name} (ID: {user_id})"
                )

                # Remove each berry reminder after sending — use the actual reminder slot_number
                for reminder in reminders:
                    if (
                        next_stage_map.get(reminder["stage"], "unknown").lower()
                        == "berry"
                    ):
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
