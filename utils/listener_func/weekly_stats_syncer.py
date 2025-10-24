import re

import discord

from utils.loggers.pretty_logs import pretty_log
from utils.essentials.pokemeow_helpers import get_pokemeow_reply_member
from config.current_setup import STRAYMONS_GUILD_ID
from utils.listener_func.pokemon_caught import weekly_goal_checker

# 🌸───────────────────────────────────────────────🌸
# 🩷 ⏰ Weekly Stats Syncer Listener               🩷
# 🌸───────────────────────────────────────────────🌸
async def weekly_stats_syncer(bot, before:discord.Message, message: discord.Message):
    from utils.cache.straymon_member_cache import fetch_straymon_member_cache_by_name, fetch_straymon_member_cache
    from utils.cache.weekly_goal_tracker_cache import (
        fetch_weekly_goal_cache_by_name,
        mark_weekly_goal_dirty,
        set_weekly_stats,
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
    # Get replied member
    replied_member = await get_pokemeow_reply_member(before)

    if not replied_member:
        return
    # Try to fetch by user ID first
    straymon_info = fetch_straymon_member_cache(replied_member.id)

    if not straymon_info:
        # Try to fetch by user name as fallback
        straymon_info = fetch_straymon_member_cache_by_name(user_name)
        if straymon_info:
            pretty_log(
                "info",
                f"Found user '{user_name}' in cache by name fallback.",
                label="💠 WEEKLY STATS DEBUG",
                bot=bot,
            )
            user_id = straymon_info.get("user_id", replied_member.id)
            user = message.guild.get_member(user_id) or replied_member
        else:
            pretty_log(
                "warning",
                f"User '{user_name}' not found in Straymon cache by ID or name.",
                label="💠 WEEKLY STATS DEBUG",
                bot=bot,
            )
            return
    else:
        user = replied_member
        user_id = user.id

    # Update weekly stats
    set_weekly_stats(
        user=user,
        pokemon_caught=pokemon_caught,
        fish_caught=fish_caught,
        battles_won=battles_won,
    )
    mark_weekly_goal_dirty(user_id)

    # Check if user is eligible for roles
    guild = bot.get_guild(STRAYMONS_GUILD_ID)
    if guild:
        await weekly_goal_checker(
            bot=bot,
            guild=guild,
            member=user,
            member_info=weekly_goal_cache.get(user_id),
            channel=message.channel,
        )