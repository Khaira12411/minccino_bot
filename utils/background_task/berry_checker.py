import time

import discord

from config.aesthetic import *
from config.current_setup import KHY_USER_ID, STRAYMONS_GUILD_ID
from config.straymons_constants import STRAYMONS__TEXT_CHANNELS
from utils.database.berry_reminder import (
    fetch_all_due_berry_reminders,
    remove_berry_reminder,
    update_growth_stage,
    berry_map,
    next_stage_map,
)
from utils.essentials.pokemeow_helpers import get_pokemeow_reply_member
from utils.loggers.debug_log import debug_log, enable_debug
from utils.loggers.pretty_logs import pretty_log

enable_debug(f"{__name__}.berry_reminder_checker")


async def update_growth_stage_func(
    bot: discord.Client, user_id: int, slot_number: int, stage: str, berry_name: str
):
    """Updates the growth stage and grows_on time for a specific berry reminder."""
    pretty_log(
        "debug",
        f"Updating growth stage for user_id {user_id} in slot {slot_number} to stage {stage} for berry {berry_name}",
    )
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

    # debug_log("Fetching all due berry reminders...")
    due_reminders = await fetch_all_due_berry_reminders(bot)

    if not due_reminders:
        # debug_log("No due berry reminders found. Exiting checker.")
        return
    debug_log(f"Found {len(due_reminders)} due reminders. Getting guild...")
    guild = bot.get_guild(STRAYMONS_GUILD_ID)

    # Group reminders by user and channel ONLY
    from collections import defaultdict

    due_reminders_count = len(due_reminders)
    debug_log(f"Fetched {due_reminders_count} due berry reminders from the database.")
    user_channel_reminders = defaultdict(list)

    for reminder in due_reminders:
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
        debug_log(f"Assigning reminder to user/channel key: {key}")
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
            debug_log(
                f"Processing reminder for slot {reminder['slot_number']}: {reminder}"
            )
            water_can_type = reminder.get("water_can_type", "unknown")
            stage = reminder.get("stage", "unknown")
            next_stage = next_stage_map.get(reminder["stage"].lower(), "unknown")
            mulch_type = reminder.get("mulch_type") or "unknown"
            if isinstance(mulch_type, str) and mulch_type != "unknown":
                mulch_type = mulch_type.lower()
            slot_number = reminder["slot_number"]
            context = "watering stage"
            berry_name_raw = (
                reminder["berry_name"].lower()
                if reminder.get("berry_name")
                else "unknown"
            )
            slot_number = reminder["slot_number"]
            berry_emoji = berry_map[berry_name_raw]["emoji"]
            debug_log(
                f"water_can_type={water_can_type}, stage={stage}, next_stage={next_stage}, mulch_type={mulch_type}, slot_number={slot_number}, berry_name_raw={berry_name_raw}"
            )
            if water_can_type != "unknown" and stage != "unknown":
                if water_can_type.lower() == "sprayduck" or water_can_type.lower() == "wailmer pail":
                    debug_log(
                        f"Sprayduck/Wailmer Pail used for slot {slot_number}. next_stage={next_stage}"
                    )
                    if next_stage.lower() != "berry":
                        debug_log(
                            f"Updating growth stage for slot {slot_number} (not berry stage)"
                        )
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

                else:
                    # Spray Lotad needs constant watering reminding
                    if next_stage.lower() == "berry":
                        context = "harvest stage"
                    else:
                        context = "watering stage"
                        debug_log(
                            f"Growth paused for slot {slot_number}, removing reminder."
                        )

            berry_name = (
                f"{berry_emoji} {berry_name_raw.title()} (Slot {slot_number})".strip()
            )
            debug_log(
                f"Prepared berry name: {berry_name} (raw: {berry_name_raw}) for context: {context}"
            )
            if context == "watering stage":
                to_be_watered_berry_names.append(berry_name)
                debug_log(
                    f"Added to watering list: {berry_name} for slot {slot_number}"
                )
            else:
                to_be_harvested_berry_names.append(berry_name)
                debug_log(
                    f"Added to harvesting list: {berry_name} for slot {slot_number}"
                )
            if not to_be_watered_berry_names and not to_be_harvested_berry_names:
                debug_log(
                    f"No berries to be watered or harvested for user_id={user_id} after processing reminders. Skipping message sending."
                )
                continue

        # Compose message depending on how many berries are due
        if not to_be_watered_berry_names and not to_be_harvested_berry_names:
            debug_log(
                f"No berries to be watered or harvested for user_id={user_id} after processing reminders. Skipping message sending."
            )
            continue

        to_be_watered_field_name = (
            "Berries to be watered. Use `;berry water` to water them:"
        )
        to_be_harvested_field_name = (
            "Berries to be harvested. Use `;berry harvest` to harvest them:"
        )
        debug_log(f"Composing embed for user {user_name} (ID: {user_id})")
        embed = discord.Embed(color=0x66CC66)
        if to_be_watered_berry_names:
            debug_log(f"Adding watered berries field: {to_be_watered_berry_names}")
            embed.add_field(
                name=to_be_watered_field_name,
                value="\n".join(to_be_watered_berry_names),
                inline=False,
            )
        if to_be_harvested_berry_names:
            debug_log(f"Adding harvested berries field: {to_be_harvested_berry_names}")
            embed.add_field(
                name=to_be_harvested_field_name,
                value="\n".join(to_be_harvested_berry_names),
                inline=False,
            )
        if not to_be_watered_berry_names and to_be_harvested_berry_names:
            msg = f"{Emojis.mouse_harvest} Hey {mention}, its time to harvest your berries!"
            thumbnail_url = MINC_Thumbnails.harvest
        elif to_be_watered_berry_names and not to_be_harvested_berry_names:
            msg = f"{Emojis.mouse_water} Hey {mention}, its time to water your berries for additional yield!"
            thumbnail_url = MINC_Thumbnails.water
        else:
            msg = f"{Emojis.mouse_farmer} Hey {mention}, its time to check your berries!"
            thumbnail_url = MINC_Thumbnails.plant
        embed.set_thumbnail(url=thumbnail_url)
        embed.set_image(url=MINC_DIVIDER.flowers)

        debug_log(f"Composed message: {msg}")

        # Send to the correct channel using bot.get_channel
        channel = bot.get_channel(channel_id)
        debug_log(
            f"Looking up channel by id: {channel_id}, expected name: {channel_name}"
        )
        if channel and channel.name == channel_name:
            debug_log(
                f"Found channel: {channel} (name: {channel.name}) in guild: {channel.guild.name}"
            )
            try:
                debug_log(
                    f"Attempting to send message to channel {channel.name} (ID: {channel.id}) for user {user_name} (ID: {user_id})"
                )
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
                        next_stage_map.get(reminder["stage"].lower(), "unknown").lower()
                        == "berry"
                    ):
                        debug_log(
                            f"Removing berry reminder for user_id={user_id}, slot_number={reminder['slot_number']}"
                        )
                        await remove_berry_reminder(
                            bot, user_id, slot_number=reminder["slot_number"]
                        )
                    else:
                        # Update growth stage to next_stage for non-berry reminders after sending reminder
                        debug_log(
                            f"Updating growth stage to next_stage for user_id={user_id}, slot_number={reminder['slot_number']}"
                        )
                        await update_growth_stage_func(
                            bot,
                            user_id,
                            reminder["slot_number"],
                            next_stage_map.get(reminder["stage"].lower(), "unknown"),
                            reminder["berry_name"],
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
