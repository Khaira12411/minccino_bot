import re

import discord

from config.aesthetic import *
from config.straymons_constants import STRAYMONS__ROLES, STRAYMONS__TEXT_CHANNELS
from utils.database.weekly_goal_tracker_db_func import upsert_weekly_goal
from utils.essentials.pokemeow_helpers import get_pokemeow_reply_member
from utils.loggers.pretty_logs import pretty_log

# 💠────────────────────────────────────────────
#           👂 Explore Caught Listener Event
# 💠────────────────────────────────────────────
async def explore_caught_listener(
    bot: discord.Client, before: discord.Message, after: discord.Message
):
    from utils.cache.straymon_member_cache import fetch_straymon_member_cache
    from utils.cache.weekly_goal_tracker_cache import (
        increment_fish_caught,
        mark_weekly_goal_dirty,
        set_pokemon_caught,
        update_weekly_angler_mark,
        update_weekly_grinder_mark,
        update_weekly_requirement_mark,
        weekly_goal_cache,
    )

    member = await get_pokemeow_reply_member(before)
    if not member:
        return

    member_id = member.id
    member_name = member.name

    # Add member to Weekly Goal Tracker if not in cache
    if member_id not in weekly_goal_cache:
        straymon_info = fetch_straymon_member_cache(member_id)
        if not straymon_info:
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
        pretty_log(
            "info",
            f"Added {member_name} ({member_id}) to Weekly Goal Tracker db and cache",
            label="💠 WEEKLY GOAL",
            bot=bot,
        )

    # Process message embeds
    if not after.embeds:
        return

    embed = after.embeds[0]
    embed_description = embed.description or ""

    # Match the number inside "Pokémon caught (...)"
    match = re.search(r"Pokémon caught \((\d+)\)", embed_description)
    if not match:
        return

    caught_count = int(match.group(1))
    pretty_log(
        "info",
        f"Explore Caught detected for {member_name}: Pokémon Caught {caught_count}",
        label="💠 EXPLORE CAUGHT",
        bot=bot,
    )

    # Update Weekly Goal Tracker cache/db
    new_caught = weekly_goal_cache[member_id].get("pokemon_caught", 0) + caught_count
    set_pokemon_caught(user=member, pokemon_caught=new_caught)
    mark_weekly_goal_dirty(member_id)

    total_caught = weekly_goal_cache[member_id].get("pokemon_caught", 0)

    # Announce Grinder milestone if reached
    if total_caught >= 175 and not weekly_goal_cache[member_id].get(
        "weekly_requirement_mark"
    ):
        update_weekly_requirement_mark(member.id)
        await after.channel.send(
            f"Congratulations {member.display_name}! You've reached the weekly requirement goal of catching 175 Pokémon! 🎉"
        )
        goal_tracker_channel = after.guild.get_channel(
            STRAYMONS__TEXT_CHANNELS.goal_tracker
        )
        if goal_tracker_channel:
            await goal_tracker_channel.send(
                f"{Emojis.gray_star} {member.display_name} has reached the Weekly requirement catch goal of 175!"
            )
    if total_caught >= 2000 and not weekly_goal_cache[member_id].get(
        "weekly_grinder_mark"
    ):
        update_weekly_grinder_mark(member.id)
        await after.channel.send(
            f"Wow {member.display_name}! You've caught over 2000 Pokémon this week! Incredible dedication! 🎉 "
            "We are also giving you the role of Weekly Grinder! Don't forget to do /active-giveaways to check for any active Weekly Grinder Giveaways"
        )
        weekly_grinder_role = after.guild.get_role(STRAYMONS__ROLES.weekly_grinder)
        if weekly_grinder_role and weekly_grinder_role not in member.roles:
            await member.add_roles(
                weekly_grinder_role, reason="Reached 2000 Pokémon caught in Weekly Goal"
            )
            pretty_log(
                "info",
                f"Assigned Weekly Grinder role to {member_name} ({member_id})",
                label="💠 WEEKLY GOAL",
                bot=bot,
            )
        goal_tracker_channel = after.guild.get_channel(
            STRAYMONS__TEXT_CHANNELS.goal_tracker
        )
        if goal_tracker_channel:
            await goal_tracker_channel.send(
                f"{Emojis.medal} {member.display_name} has reached the Weekly Grinder goal of catching 2000 Pokémon! {Emojis.celebrate}"
            )
