import discord

from config.current_setup import KHY_USER_ID
from utils.database.berry_reminder import (
    fetch_user_all_berry_reminder,
    upsert_berry_reminder,
)
from utils.essentials.pokemeow_helpers import get_pokemeow_reply_member
from utils.loggers.debug_log import debug_log, enable_debug
from utils.loggers.pretty_logs import pretty_log
from config.straymons_constants import STRAYMONS__TEXT_CHANNELS
# enable_debug(f"{__name__}.berry_listener")


async def berry_listener(bot: discord.Client, before_message: discord.Message, message: discord.Message):
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
    if user_id != KHY_USER_ID:
        debug_log(f"Message from user_id {user_id} is not Khy{KHY_USER_ID}. Ignoring.")
        return

    from utils.cache.straymon_member_cache import fetch_straymon_member_cache
    cache_info = fetch_straymon_member_cache(user_id)
    member_channel_id = cache_info["channel_id"] if cache_info else STRAYMONS__TEXT_CHANNELS.kanto_park
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
    berry_slots = extract_berry_slots(embed_description)
    if not berry_slots:
        debug_log("No berry slots found in embed description.")
        return

    for slot in berry_slots:
        slot_number = slot["slot_number"]
        berry_name = slot["berry_name"]
        berry_status = slot["status"]
        growth_stage = slot["growth_stage"]
        next_stage_time = slot["next_stage_time"]

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
                    and r["remind_on"] == next_stage_time
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
                await upsert_berry_reminder(
                    bot=bot,
                    user_id=user_id,
                    user_name=user_name,
                    slot_number=slot_number,
                    remind_on=next_stage_time,
                    stage=growth_stage,
                    channel_id=member_channel.id,
                    channel_name=member_channel.name,
                    berry_name=berry_name,
                )
        else:
            await upsert_berry_reminder(
                bot=bot,
                user_id=user_id,
                user_name=user_name,
                slot_number=slot_number,
                remind_on=next_stage_time,
                stage=growth_stage,
                channel_id=member_channel.id,
                channel_name=member_channel.name,
                berry_name=berry_name,
            )


def extract_berry_slots(embed_description: str):
    """
    Extracts slot_number, berry_name, status, growth_stage, and next_stage_time for each berry slot from the embed description.
    Skips slots that are empty.
    Returns a list of dicts with keys: slot_number, berry_name, status, growth_stage, next_stage_time
    """
    import re

    slot_pattern = re.compile(r"\*\*Slot (\d+)\*\* — (.+?)(?:\n|$)")
    next_stage_pattern = re.compile(r"Next stage <t:(\d+):R>")
    berry_name_pattern = re.compile(r"— <:(\w+):\d+> ([^<]+)")
    status_pattern = re.compile(r"• ([^•\n]+)• 💧 \*\*(.*?)\*\*")
    growth_stage_pattern = re.compile(r":\d+> (\w+) \(\d+/\d+\)")

    results = []
    lines = embed_description.splitlines()
    for i, line in enumerate(lines):
        slot_match = slot_pattern.search(line)
        if slot_match:
            slot_number = int(slot_match.group(1))
            slot_content = slot_match.group(2).strip()
            if slot_content.lower() == "empty":
                continue
            # Try to get berry name
            berry_name_match = berry_name_pattern.search(line)
            berry_name = berry_name_match.group(2).strip() if berry_name_match else None
            # Find next stage time in this or next lines
            next_stage_time = None
            for j in range(i, min(i + 2, len(lines))):
                next_stage_match = next_stage_pattern.search(lines[j])
                if next_stage_match:
                    next_stage_time = int(next_stage_match.group(1))
                    break
            # Find status and growth stage in this or next lines
            status = None
            growth_stage = None
            for j in range(i, min(i + 3, len(lines))):
                status_match = status_pattern.search(lines[j])
                if status_match:
                    status = status_match.group(2).strip()
                growth_stage_match = growth_stage_pattern.search(lines[j])
                if growth_stage_match:
                    growth_stage = growth_stage_match.group(1)
            results.append(
                {
                    "slot_number": slot_number,
                    "berry_name": berry_name,
                    "status": status,
                    "growth_stage": growth_stage,
                    "next_stage_time": next_stage_time,
                }
            )
    return results
