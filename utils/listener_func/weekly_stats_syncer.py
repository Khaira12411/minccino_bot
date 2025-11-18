import re

import discord

from config.current_setup import STRAYMONS_GUILD_ID
from utils.database.weekly_goal_tracker_db_func import upsert_weekly_goal
from utils.essentials.pokemeow_helpers import get_pokemeow_reply_member
from utils.listener_func.pokemon_caught import (
    is_saturday_1155pm_est,
    weekly_goal_checker,
)
from utils.loggers.pretty_logs import pretty_log

processed_weekly_stats_messages = set()


def extract_current_page_number(footer_text: str) -> int | None:
    """
    Extracts the current page number from a PokéMeow stats embed footer.
    Returns the page number as an int, or None if not found.
    Example footer: "Page 1/5 • Stat categories: ;clan stats daily/weekly/monthly/yearly"
    """
    match = re.search(r"Page (\d+)", footer_text)
    if match:
        return int(match.group(1))
    return None

# 🌸───────────────────────────────────────────────🌸
# 🩷 ⏰ Weekly Stats Syncer Listener               🩷
# 🌸───────────────────────────────────────────────🌸
async def weekly_stats_syncer(bot, before: discord.Message, message: discord.Message):
    from utils.cache.straymon_member_cache import (
        fetch_straymon_member_cache,
        fetch_straymon_member_cache_by_name,
    )
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
    embed_footer = embed.footer.text or ""

    if is_saturday_1155pm_est():
        pretty_log(
            "info",
            f"Skipping weekly goal check as it's Saturday 11:55 PM EST or later.",
            label="💠 WEEKLY GOAL",
            bot=bot,
        )
        return

    # Get replied member
    replied_member = await get_pokemeow_reply_member(before)

    if not replied_member:
        return
    # Try to fetch by user ID first
    straymon_info = fetch_straymon_member_cache(replied_member.id)
    user_name = replied_member.name

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

    if message.id in processed_weekly_stats_messages:
        pretty_log(
            "info",
            f"Message ID {message.id} already processed for weekly stats. Skipping.",
            label="💠 WEEKLY STATS",
            bot=bot,
        )
        return
    # Extract page number from footer
    current_page = None
    if embed.footer and embed.footer.text:
        current_page = extract_current_page_number(embed.footer.text)
    # Check if they are in the Weekly Goal Cache
    weekly_goal_info = weekly_goal_cache.get(user_id)
    if not weekly_goal_info:
        # Upsert in db
        channel_id = straymon_info.get("channel_id")
        await upsert_weekly_goal(
            bot=bot,
            user=user,
            pokemon_caught=0,
            fish_caught=0,
            battles_won=0,
            channel_id=channel_id,
        )
        pretty_log(
            "info",
            f"Added {user_name} ({user_id}) to Weekly Goal Tracker db and cache",
            label="💠 WEEKLY GOAL",
        )

    # Initialize stats variables
    pokemon_caught = 0
    fish_caught = 0
    battles_won = 0
    rank = 0
    top_line_catches = 0

    # Get top line catches
    user_top_line_match = re.search(
        r"You're Rank \d+ in your clan's weekly stats — with ([\d,]+) catches!",
        embed_description,
    )
    top_line_catches = 0
    if user_top_line_match:
        top_line_catches = int(user_top_line_match.group(1).replace(",", ""))
        pretty_log(
            "info",
            f"Top line catches for {user_name}: {top_line_catches}",
            label="💠 WEEKLY STATS DEBUG",
            bot=bot,
        )

    # Updated regex to handle the actual bolded format
    # Format: **1** **empyyy_ (newline) stats line ending with **
    bolded_pattern = re.compile(
        r"\*\*(\d+)\*\* \*\*(.+?)\n<:dexcaught:[^>]+> (\d+(?:,\d+)*) • <:oldrod:[^>]+> (\d+(?:,\d+)*) • <:poke_egg:[^>]+> \d+ • :tickets: \d+ • :robot: \d+ • :crossed_swords: (\d+(?:,\d+)*)\*\*"
    )

    match = bolded_pattern.search(embed_description)
    if match:
        pretty_log(
            "info",
            f"Weekly Stats regex matched for user {user_name}.",
            label="💠 WEEKLY STATS DEBUG",
            bot=bot,
        )
        processed_weekly_stats_messages.add(message.id)
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
    elif not match and top_line_catches >= 175 and (current_page and current_page == 1):
        pretty_log(
            "info",
            f"Weekly Stats regex did not match, but top line catches {top_line_catches} >= 175 for user {user_name}.",
            label="💠 WEEKLY STATS DEBUG",
        )
        # Check if user is eligible for roles based on top line catches
        guild = bot.get_guild(STRAYMONS_GUILD_ID)
        if guild:
            await weekly_goal_checker(
                bot=bot,
                guild=guild,
                member=user,
                member_info=weekly_goal_cache.get(user_id),
                channel=message.channel,
            )
            mark_weekly_goal_dirty(user_id)
