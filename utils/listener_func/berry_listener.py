import re

import discord

from config.current_setup import ALLOWED_BERRY_REMINDER_USER_IDS, HANA_USER_ID
from config.straymons_constants import STRAYMONS__ROLES, STRAYMONS__TEXT_CHANNELS
from utils.database.berry_reminder import (
    fetch_user_all_berry_reminder,
    remove_berry_reminder,
    upsert_berry_reminder,
    update_moisture_dries_on,
    update_moisture_dries_on_func,
)
from utils.database.watering_can_db import (
    check_if_bot_already_asked,
    get_watering_can,
    upsert_watering_can,
)
from utils.essentials.pokemeow_helpers import get_pokemeow_reply_member
from utils.loggers.debug_log import debug_log, enable_debug
from utils.loggers.pretty_logs import pretty_log

# enable_debug(f"{__name__}.berry_listener")


def extract_mulch_application(line: str):
    """
    Extracts the mulch emoji name, mulch label, and slot number from a mulch application line.
    Example: "### <:damp_mulch:1486261015657185281> Applied **Damp Mulch** to Slot 1 (<:sprouted:1486510462416851014> Aspear Tree)!"
    Returns a dict with keys: mulch_name, mulch_label, slot_number
    """
    pattern = re.compile(
        r"<:(\w+):\d+>\s+Applied\s+\*\*(.+?)\*\*\s+to Slot (\d+)", re.IGNORECASE
    )
    match = pattern.search(line)
    if match:
        return {
            "mulch_name": match.group(1),
            "mulch_label": match.group(2),
            "slot_number": int(match.group(3)),
        }
    return None


def extract_watering_action(line: str):
    """
    Extracts the watering can emoji name, berry name, and slot number from a watering action line.
    Example: "<:wailmer_pail:1486261601622425680> Watered **Aspear Berry** in Slot 3!"
    Returns a dict with keys: water_can_emoji, berry_name, slot_number
    """
    pattern = re.compile(
        r"<:(\w+):\d+>\s+Watered\s+\*\*(.+?)\*\*\s+in Slot (\d+)!", re.IGNORECASE
    )
    match = pattern.search(line)
    if match:
        return {
            "water_can_emoji": match.group(1),
            "berry_name": match.group(2),
            "slot_number": int(match.group(3)),
        }
    return None


async def berry_listener(
    bot: discord.Client, before_message: discord.Message, message: discord.Message
):
    """Listens for berry reminders from pokemeow and stores them in the database."""
    embed = message.embeds[0] if message.embeds else None
    if not embed:
        return

    member = await get_pokemeow_reply_member(before_message)
    if not member:
        debug_log("No member found in pokemeow reply.")
        return
    user_id = member.id
    guild = message.guild
    straymon_role = guild.get_role(STRAYMONS__ROLES.straymon)
    if (
        straymon_role not in member.roles
        and user_id not in ALLOWED_BERRY_REMINDER_USER_IDS
    ):
        debug_log(
            f"Message from user_id {user_id} is not allowed in berry users. Ignoring."
        )
        return
    # Check if they have watering can
    water_can_type = await get_watering_can(bot, user_id)
    if not water_can_type:
        if await check_if_bot_already_asked(bot, user_id):
            debug_log(
                f"Bot has already asked user_id {user_id} about watering can. Not asking again."
            )
            return
        content = f"Hi {member.mention}, I noticed you have a berry reminder but no watering can information stored. Kindly do `;items` then go to __Berry Pouch__ to set up your watering can type for accurate watering reminders then do `;berry` again!"
        await message.channel.send(content)
        await upsert_watering_can(bot, user_id, member.name, None)
        return
    from utils.cache.straymon_member_cache import fetch_straymon_member_cache

    cache_info = fetch_straymon_member_cache(user_id)
    member_channel_id = (
        cache_info["channel_id"] if cache_info else STRAYMONS__TEXT_CHANNELS.kanto_park
    )
    if user_id == HANA_USER_ID:
        member_channel_id = STRAYMONS__TEXT_CHANNELS.khy
    member_channel = guild.get_channel(member_channel_id) if member_channel_id else None
    member_channel_name = member_channel.name if member_channel else None

    user_name = member.name
    embed_description = embed.description
    if "no berries planted" in embed_description.lower():
        debug_log("No berries planted. Ignoring.")
        return
    are_new_reminders = False
    # Get the old berry reminders for this user from the database
    old_reminders = await fetch_user_all_berry_reminder(bot, user_id)
    if not old_reminders:
        debug_log("No old berry reminders found for this user.")
        are_new_reminders = True

    # Extract berry reminder details from the embed description
    debug_log(
        f"Extracting berry reminder details from embed description: {embed_description}"
    )
    berry_slots = extract_berry_slots(embed_description)
    pretty_log(
        "debug",
        f"Extracted berry slots from embed description: {berry_slots}",
    )
    if not berry_slots:
        debug_log("No berry slots found in embed description.")
        return

    for slot in berry_slots:
        slot_number = slot["slot_number"]
        berry_name = slot["berry_name"]
        berry_status = slot["status"]
        growth_stage = slot["growth_stage"]
        next_stage_time = slot["next_stage_time"]
        has_growth_paused = slot["has_growth_paused"]
        mulch_name = slot["mulch_name"]
        has_ready_to_harvest = slot.get("has_ready_to_harvest", False)

        # Upsert the berry reminder in the database
        if not are_new_reminders:
            # Check if this reminder already exists in the old reminders and if it needs to be updated
            matching_old_reminder = next(
                (
                    r
                    for r in old_reminders
                    if r["slot_number"] == slot_number
                    and r["berry_name"] == berry_name
                    and r["stage"] == growth_stage
                    and r["grows_on"] == next_stage_time
                    and r["mulch_type"] == mulch_name
                ),
                None,
            )
            if matching_old_reminder:
                debug_log(
                    f"Berry reminder for slot {slot_number} with berry {berry_name} and stage {growth_stage} already exists and is up to date. Skipping database update."
                )
                continue
            else:
                debug_log(
                    f"Berry reminder for slot {slot_number} with berry {berry_name} and stage {growth_stage} is new or has changed. Updating database."
                )
                if not has_ready_to_harvest:
                    await upsert_berry_reminder(
                        bot=bot,
                        user_id=user_id,
                        user_name=user_name,
                        slot_number=slot_number,
                        grows_on=next_stage_time,
                        stage=growth_stage,
                        channel_id=member_channel.id,
                        channel_name=member_channel.name,
                        berry_name=berry_name,
                        mulch_type=mulch_name,
                        water_can_type=water_can_type,
                    )
                else:
                    # Remove the reminder from the database if it's ready to harvest
                    await remove_berry_reminder(bot, user_id, slot_number)
        else:
            if not has_ready_to_harvest:
                await upsert_berry_reminder(
                    bot=bot,
                    user_id=user_id,
                    user_name=user_name,
                    slot_number=slot_number,
                    grows_on=next_stage_time,
                    stage=growth_stage,
                    channel_id=member_channel.id,
                    channel_name=member_channel.name,
                    berry_name=berry_name,
                    mulch_type=mulch_name,
                    water_can_type=water_can_type,
                )
            else:
                # Remove the reminder from the database if it's ready to harvest
                await remove_berry_reminder(bot, user_id, slot_number)
    if (
        "watered" in embed_description.lower()
        and "in slot" in embed_description.lower()
    ):
        watering_action = extract_watering_action(embed_description)
        if watering_action:
            debug_log(
                f"Extracted watering action from embed description: {watering_action}"
            )
            await update_moisture_dries_on_func(
                bot,
                user_id,
                watering_action["slot_number"],
                watering_action["berry_name"],
            )
        else:
            debug_log("Failed to extract watering action from embed description.")
    if "applied **damp mulch** to slot" in embed_description.lower():
        mulch_application = extract_mulch_application(embed_description)
        if mulch_application:
            debug_log(
                f"Extracted mulch application from embed description: {mulch_application}"
            )
            # Update the mulch type for this berry reminder in the database , no need for moisture_dries_on update
            await update_moisture_dries_on(
                bot=bot,
                user_id=user_id,
                slot_number=mulch_application["slot_number"],
                moisture_dries_on=None,
            )
        else:
            debug_log("Failed to extract mulch application from embed description.")


def extract_berry_slots(embed_description: str):
    """
    Extracts slot_number, berry_name, mulch_name, status, growth_stage, next_stage_time, and has_growth_paused
    for each berry slot from the embed description.
    Skips slots that are empty or locked (padlock emoji).
    """
    import re

    slot_pattern = re.compile(r"\*\*Slot (\d+)\*\* — (.+?)(?:\n|$)")
    next_stage_pattern = re.compile(r"Next stage <t:(\d+):R>")
    berry_name_pattern = re.compile(r"— <:\w+:\d+> ([A-Za-z ]+?)(?:\s*<|\s*•|$)")
    mulch_pattern = re.compile(r"<:(\w+_mulch):\d+>")
    status_pattern = re.compile(r"• 💧 \*\*(.*?)\*\*")

    # Growth stage regex: matches emoji, stage name, and [STAGE x/y] with optional backticks
    growth_stage_pattern = re.compile(
        r"<:[^:]+:\d+>\s*([^`\[]+?)\s*`?\[STAGE \d+/\d+\]`?", re.IGNORECASE
    )
    growth_paused_pattern = re.compile(r"growth paused", re.IGNORECASE)
    ready_to_harvest_pattern = re.compile(r"ready to harvest", re.IGNORECASE)
    has_ready_to_harvest = False
    results = []
    lines = embed_description.splitlines()
    for i, line in enumerate(lines):
        slot_match = slot_pattern.search(line)
        if slot_match:
            slot_number = int(slot_match.group(1))
            slot_content = slot_match.group(2).strip()

            # Skip empty or locked slots
            normalized = slot_content.lower()
            if (
                "empty" in normalized
                or "slot locked" in normalized
                or "🔒" in slot_content
            ):
                continue

            # Berry name
            berry_name_match = berry_name_pattern.search(line)
            berry_name = berry_name_match.group(1).strip() if berry_name_match else None

            # Mulch name
            mulch_name = None
            mulch_match = mulch_pattern.search(line)
            if mulch_match:
                mulch_name = mulch_match.group(1).replace("_", " ").title()

            # Next stage time
            next_stage_time = None
            for j in range(i, min(i + 2, len(lines))):
                next_stage_match = next_stage_pattern.search(lines[j])
                if next_stage_match:
                    next_stage_time = int(next_stage_match.group(1))
                    break

            # Status, growth stage, growth paused
            status = None
            growth_stage = None
            has_growth_paused = False
            for j in range(i, min(i + 3, len(lines))):
                status_match = status_pattern.search(lines[j])
                if status_match:
                    status = status_match.group(1).strip()
                growth_stage_match = growth_stage_pattern.search(lines[j])
                if growth_stage_match:
                    growth_stage = growth_stage_match.group(1).strip()
                if growth_paused_pattern.search(lines[j]):
                    has_growth_paused = True
                if ready_to_harvest_pattern.search(lines[j]):
                    has_ready_to_harvest = True

            results.append(
                {
                    "slot_number": slot_number,
                    "berry_name": berry_name,
                    "mulch_name": mulch_name,
                    "status": status,
                    "growth_stage": growth_stage,
                    "next_stage_time": next_stage_time,
                    "has_growth_paused": has_growth_paused,
                    "has_ready_to_harvest": has_ready_to_harvest,
                }
            )
    return results
