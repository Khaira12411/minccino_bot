import re

import discord

from config.aesthetic import Emojis
from config.straymons_constants import STRAYMONS__ROLES
from utils.database.weekly_goal_tracker_db_func import upsert_weekly_goal
from utils.loggers.pretty_logs import pretty_log

OWNER_USERNAME = ["khy.09", "hana_banana._"]


async def battle_won_listener(bot: discord.Client, message: discord.Message):
    from utils.cache.straymon_member_cache import fetch_straymon_member_cache_by_name
    from utils.cache.weekly_goal_tracker_cache import (
        fetch_weekly_goal_cache_by_name,
        increment_battles_won,
        mark_weekly_goal_dirty,
        update_weekly_guardian_mark,
        weekly_goal_cache,
    )

    # Extract username from battle won message
    emoji_pattern = r"<:[^:]+:\d+>"
    username_match = re.search(
        rf"{emoji_pattern} \*\*(.+?)\*\* won the battle!", message.content
    )
    if not username_match:
        return

    user_name = username_match.group(1)
    if user_name in OWNER_USERNAME:
        pokemon_message = f"{Emojis.pokespawn} **{user_name}**, your </pokemon:1015311085441654824> command is ready!"
        fish_message = f"{Emojis.fish_spawn} **{user_name}**, your </fish spawn:1015311084812501026> command is ready!"
        await message.channel.send(pokemon_message)
        await message.channel.send(fish_message)

    # Check cache first
    weekly_goal_info = fetch_weekly_goal_cache_by_name(user_name)

    if not weekly_goal_info:
        # Not in cache, check Straymon membership
        straymon_info = fetch_straymon_member_cache_by_name(user_name)
        if not straymon_info:
            return

        user_id = straymon_info.get("user_id")
        channel_id = straymon_info.get("channel_id")

        # Fetch member from guild
        user = message.guild.get_member(user_id)
        if not user:
            return

        # Add to Weekly Goal Tracker DB/cache
        await upsert_weekly_goal(
            bot,
            user=user,
            pokemon_caught=0,
            fish_caught=0,
            battles_won=0,
            channel_id=channel_id,
        )
        pretty_log(
            "info",
            f"Added {user.display_name} ({user_id}) to Weekly Goal Tracker db and cache",
            label="💠 WEEKLY GOAL",
            bot=bot,
        )
    else:
        user_id = weekly_goal_info["user_id"]
        user = message.guild.get_member(user_id)
        if not user:
            return

    # Increment battles won
    increment_battles_won(user.display_name, user_id)
    mark_weekly_goal_dirty(user_id)
    new_battles_won = weekly_goal_cache[user_id].get("battles_won", 0)

    if new_battles_won >= 300 and not weekly_goal_cache[user_id].get(
        "weekly_guardian_mark", False
    ):
        content = (
            f"🏆 **{user.display_name}** has reached **300 Battles Won** this week "
            f"and earned the **Weekly Guardian** role!"
        )
        update_weekly_guardian_mark(user_id)
        await message.channel.send(content)

        weekly_guardian_role = message.guild.get_role(STRAYMONS__ROLES.weekly_guardian)
        if weekly_guardian_role and weekly_guardian_role not in user.roles:
            try:
                await user.add_roles(
                    weekly_guardian_role,
                    reason="Reached 300 battles won in Weekly Goal",
                )
            except discord.Forbidden:
                pretty_log(
                    "warn",
                    f"Failed to assign Weekly Guardian role to {user.display_name} ({user_id}) due to missing permissions",
                    label="💠 WEEKLY GOAL",
                    bot=bot,
                )
            else:
                pretty_log(
                    "info",
                    f"Assigned Weekly Guardian role to {user.display_name} ({user_id})",
                    label="💠 WEEKLY GOAL",
                    bot=bot,
                )
