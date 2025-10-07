import re

import discord

from config.straymons_constants import STRAYMONS__ROLES, STRAYMONS__TEXT_CHANNELS
from utils.loggers.pretty_logs import pretty_log
from config.aesthetic import Emojis

# 🌸───────────────────────────────────────────────🌸
# 🩷 ⏰ Weekly Stats Syncer Listener               🩷
# 🌸───────────────────────────────────────────────🌸
async def weekly_stats_syncer(bot, message: discord.Message):
    from utils.cache.straymon_member_cache import fetch_straymon_member_cache_by_name
    from utils.cache.weekly_goal_tracker_cache import (
        fetch_weekly_goal_cache_by_name,
        mark_weekly_goal_dirty,
        set_weekly_stats,
        update_weekly_angler_mark,
        update_weekly_grinder_mark,
        update_weekly_requirement_mark,
        weekly_goal_cache,
    )
    pretty_log(
        "info",
        f"Weekly Stats Syncer triggered by message ID {message.id} in channel {message.channel.id}",
        label="💠 WEEKLY STATS",
        bot=bot,
    )

    embed = message.embeds[0]
    embed_description = embed.description or ""

    # Updated regex to handle the actual bolded format
    # Format: **1** **empyyy_ (newline) stats line ending with **
    bolded_pattern = re.compile(
        r"\*\*(\d+)\*\* \*\*(.+?)\n<:dexcaught:[^>]+> (\d+(?:,\d+)*) • <:oldrod:[^>]+> (\d+(?:,\d+)*) • <:poke_egg:[^>]+> \d+ • :tickets: \d+ • :robot: \d+ • :crossed_swords: (\d+(?:,\d+)*)\*\*"
    )

    match = bolded_pattern.search(embed_description)
    if not match:
        pretty_log(
            "warning",
            "No bolded weekly stats line found - this means the user's own stats are not visible in this embed.",
            label="💠 WEEKLY STATS DEBUG",
            bot=bot,
        )
        return

    rank = int(match.group(1))
    user_name = match.group(2).strip()
    pokemon_caught = int(match.group(3).replace(",", ""))
    fish_caught = int(match.group(4).replace(",", ""))
    battles_won = int(match.group(5).replace(",", ""))

    pretty_log(
        "info",
        f"Weekly Stats detected for {user_name}: Rank {rank}, Pokémon Caught {pokemon_caught}, "
        f"Fish Caught {fish_caught}, Battles Won {battles_won}",
        label="💠 WEEKLY STATS",
        bot=bot,
    )

    # Fetch member and update cache
    straymon_info = fetch_straymon_member_cache_by_name(user_name)
    if not straymon_info:
        pretty_log(
            "warning",
            f"User '{user_name}' not found in Straymon cache.",
            label="💠 WEEKLY STATS DEBUG",
            bot=bot,
        )
        return

    user_id = straymon_info.get("user_id")
    user = message.guild.get_member(user_id)
    if not user:
        pretty_log(
            "warning",
            f"User '{user_name}' not found in guild members.",
            label="💠 WEEKLY STATS DEBUG",
            bot=bot,
        )
        return

    # Update weekly stats
    set_weekly_stats(
        user=user,
        pokemon_caught=pokemon_caught,
        fish_caught=fish_caught,
        battles_won=battles_won,
    )
    mark_weekly_goal_dirty(user_id)

    # Check if user is eligible for roles
    if pokemon_caught >= 175 and not weekly_goal_cache[user_id].get(
        "weekly_requirement_mark"
    ):
        update_weekly_requirement_mark(user.id)
        await message.channel.send(
            f"Congratulations {user.display_name}! You've reached the weekly requirement goal of catching 175 Pokémon! 🎉"
        )
        goal_tracker_channel = message.guild.get_channel(
            STRAYMONS__TEXT_CHANNELS.goal_tracker
        )
        if goal_tracker_channel:
            await goal_tracker_channel.send(
                f"{Emojis.gray_star} {user.display_name} has reached the Weekly requirement catch goal of 175!"
            )
    if pokemon_caught >= 2000 and not weekly_goal_cache[user_id].get(
        "weekly_grinder_mark"
    ):
        update_weekly_grinder_mark(user.id)
        await message.channel.send(
            f"Wow {user.display_name}! You've caught over 2000 Pokémon this week! Incredible dedication! 🎉 "
            "We are also giving you the role of Weekly Grinder! Don't forget to do /active-giveaways to check for any active Weekly Grinder Giveaways"
        )
        weekly_grinder_role = message.guild.get_role(STRAYMONS__ROLES.weekly_grinder)
        if weekly_grinder_role and weekly_grinder_role not in user.roles:
            await user.add_roles(
                weekly_grinder_role, reason="Reached 2000 Pokémon caught in Weekly Goal"
            )
        goal_tracker_channel = message.guild.get_channel(
            STRAYMONS__TEXT_CHANNELS.goal_tracker
        )
        if goal_tracker_channel:
            await goal_tracker_channel.send(
                f"{Emojis.medal} {user.display_name} has reached the Weekly Grinder goal of catching 2000 Pokémon! {Emojis.celebrate}"
            )

        pretty_log(
            "info",
            f"Assigned Weekly Grinder role to {user.display_name} ({user_id})",
            label="💠 WEEKLY GOAL",
            bot=bot,
        )
    if fish_caught >= 500 and not weekly_goal_cache[user_id].get("weekly_angler_mark"):
        update_weekly_angler_mark(user.id)
        await message.channel.send(
            f"Congratulations {user.display_name}! You've reached the weekly angler goal of catching 500 fish! 🎉 We are also giving you the role of Weekly Angler"
        )
        weekly_angler_role = message.guild.get_role(STRAYMONS__ROLES.weekly_angler)
        if weekly_angler_role and weekly_angler_role not in user.roles:
            await user.add_roles(
                weekly_angler_role, reason="Reached 500 fish caught in Weekly Goal"
            )
        pretty_log(
            "info",
            f"Assigned Weekly Angler role to {user.display_name} ({user_id})",
            label="💠 WEEKLY GOAL",
            bot=bot,
        )
    if battles_won >= 300 and not weekly_goal_cache[user_id].get(
        "weekly_guardian_mark"
    ):
        await message.channel.send(
            f"🏆 **{user.display_name}** has reached **300 Battles Won** this week "
            f"and earned the **Weekly Guardian** role!"
        )
        weekly_guardian_role = message.guild.get_role(STRAYMONS__ROLES.weekly_guardian)
        if weekly_guardian_role and weekly_guardian_role not in user.roles:
            await user.add_roles(
                weekly_guardian_role, reason="Reached 300 battles won in Weekly Goal"
            )
        update_weekly_angler_mark(user.id)
        pretty_log(
            "info",
            f"Assigned Weekly Guardian role to {user.display_name} ({user_id})",
            label="💠 WEEKLY GOAL",
            bot=bot,
        )
