import re

import discord

from config.aesthetic import *
from config.current_setup import STRAYMONS_GUILD_ID
from utils.database.weekly_goal_tracker_db_func import upsert_weekly_goal
from utils.essentials.pokemeow_helpers import get_pokemeow_reply_member
from utils.listener_func.pokemon_caught import weekly_goal_checker
from utils.loggers.debug_log import debug_log, enable_debug
from utils.loggers.pretty_logs import pretty_log

# Enable debug for this function
# enable_debug(f"{__name__}.explore_caught_listener")
processed_explore_caught_messages = set()


# 💠────────────────────────────────────────────
#           👂 Explore Caught Listener Event
# 💠────────────────────────────────────────────
async def explore_caught_listener(
    bot: discord.Client, before: discord.Message, after: discord.Message
):
    from utils.cache.straymon_member_cache import fetch_straymon_member_cache
    from utils.cache.weekly_goal_tracker_cache import (
        mark_weekly_goal_dirty,
        set_pokemon_caught,
        weekly_goal_cache,
    )

    # ✅ DEBUG: Log that function was called
    debug_log(f"Function called - Message ID: {after.id}")
    if after.id in processed_explore_caught_messages:
        debug_log(f"❌ Message {after.id} already processed - skipping")
        return
    processed_explore_caught_messages.add(after.id)

    member = await get_pokemeow_reply_member(before)
    if not member:
        debug_log(
            f"❌ No member found from get_pokemeow_reply_member - before message ID: {before.id if before else 'None'}"
        )
        return

    member_id = member.id
    member_name = member.name

    # ✅ DEBUG: Log member found
    debug_log(f"✅ Member found: {member_name} ({member_id})")

    # Add member to Weekly Goal Tracker if not in cache
    if member_id not in weekly_goal_cache:
        straymon_info = fetch_straymon_member_cache(member_id)
        if not straymon_info:
            debug_log(f"❌ Member {member_name} not in straymon cache - skipping")
            return
        channel_id = straymon_info.get("channel_id")
        await upsert_weekly_goal(
            bot,
            user=member,
            pokemon_caught=0,
            fish_caught=0,
            battles_won=0,
            channel_id=channel_id,
        )
        debug_log(
            f"➕ Added {member_name} ({member_id}) to Weekly Goal Tracker",
            highlight=True,
        )
        pretty_log(
            "info",
            f"Added {member_name} ({member_id}) to Weekly Goal Tracker db and cache",
            label="💠 WEEKLY GOAL",
            bot=bot,
        )

    # Process message content (not embeds!)
    content = after.content or ""

    # ✅ DEBUG: Log what we're searching through
    debug_log(f"🔍 Message content: {repr(content[:300])}...")

    if not content:
        debug_log(f"❌ No content found in message {after.id}")
        return

    # ✅ FIXED: Search in content only (no embeds for explore messages)
    match = re.search(r"Pokémon caught \((\d+)\):", content)
    if match:
        debug_log(f"✅ Found match in content: {match.group(0)}", highlight=True)
    else:
        debug_log("❌ No Pokémon caught pattern found in content")
        return

    caught_count = int(match.group(1))
    debug_log(
        f"🎯 Explore Caught detected for {member_name}: {caught_count} Pokémon",
        highlight=True,
    )

    # ✅ DEBUG: Log current cache state
    current_caught = weekly_goal_cache[member_id].get("pokemon_caught", 0)
    debug_log(f"📊 Current pokemon_caught for {member_name}: {current_caught}")

    pretty_log(
        "info",
        f"Explore Caught detected for {member_name}: Pokémon Caught {caught_count}",
        label="💠 EXPLORE CAUGHT",
        bot=bot,
    )

    # Update Weekly Goal Tracker cache/db
    new_caught = current_caught + caught_count

    # ✅ DEBUG: Log the update
    debug_log(
        f"📈 Updating {member_name}: {current_caught} + {caught_count} = {new_caught}"
    )

    set_pokemon_caught(user=member, amount=new_caught)
    mark_weekly_goal_dirty(member_id)

    # ✅ DEBUG: Verify the update
    updated_caught = weekly_goal_cache[member_id].get("pokemon_caught", 0)
    debug_log(
        f"✅ After update, {member_name} total pokemon_caught: {updated_caught}",
        highlight=True,
    )

    total_caught = weekly_goal_cache[member_id].get("pokemon_caught", 0)

    # Check for weekly goal milestones
    member_info = weekly_goal_cache.get(member_id)
    guild = bot.get_guild(STRAYMONS_GUILD_ID)
    if guild:
        await weekly_goal_checker(
            bot=bot,
            guild=guild,
            member=member,
            member_info=member_info,
            channel=after.channel,
        )
