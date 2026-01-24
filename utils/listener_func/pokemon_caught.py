import re
from datetime import datetime
from zoneinfo import ZoneInfo

import discord

from config.aesthetic import *
from config.current_setup import STRAYMONS_GUILD_ID
from config.straymons_constants import STRAYMONS__ROLES, STRAYMONS__TEXT_CHANNELS
from utils.cache.cache_list import probation_members_cache
from utils.database.probation_members_db import (
    update_probation_member_status,
    upsert_probation_member,
)
from utils.database.weekly_goal_tracker_db_func import upsert_weekly_goal
from utils.essentials.pokemeow_helpers import get_pokemeow_reply_member
from utils.loggers.pretty_logs import pretty_log

FISHING_COLOR = 0x87CEFA
processed_caught_messages = set()


def is_saturday_1155pm_est():
    """
    Returns True if the current time in America/New_York is Saturday at 11:55 PM or later (before midnight).
    """
    nyc = ZoneInfo("America/New_York")
    now_nyc = datetime.now(nyc)
    return now_nyc.weekday() == 5 and now_nyc.hour == 23 and now_nyc.minute >= 55


async def weekly_goal_checker(
    bot: discord.Client,
    member: discord.Member,
    member_info: dict,
    channel: discord.TextChannel,
    guild: discord.Guild,
    top_line_catches: int = None,
):
    from utils.cache.weekly_goal_tracker_cache import (
        update_weekly_angler_mark,
        update_weekly_grinder_mark,
        update_weekly_guardian_mark,
        update_weekly_requirement_mark,
    )

    if is_saturday_1155pm_est():
        pretty_log(
            "info",
            f"Skipping weekly goal check for {member.name} ({member.id}) as it's Saturday 11:55 PM EST or later.",
            label="💠 WEEKLY GOAL",
            bot=bot,
        )
        return

    pokemon_caught = member_info.get("pokemon_caught", 0)
    fish_caught = member_info.get("fish_caught", 0)
    battles_won = member_info.get("battles_won", 0)
    total_caught = pokemon_caught + fish_caught
    weekly_angler_mark = member_info.get("weekly_angler_mark", False)
    weekly_requirement_mark = member_info.get("weekly_requirement_mark", False)
    weekly_grinder_mark = member_info.get("weekly_grinder_mark", False)
    weekly_guardian_mark = member_info.get("weekly_guardian_mark", False)

    goal_tracker_channel = guild.get_channel(STRAYMONS__TEXT_CHANNELS.goal_tracker)

    # Early exit for those with probation role
    probation_role = guild.get_role(STRAYMONS__ROLES.probation)
    if probation_role and probation_role in member.roles:
        # Check their status
        probation_data = probation_members_cache.get(member.id)
        if not probation_data:
            # Upsert in DB and cache
            await upsert_probation_member(
                bot,
                member.id,
                member.name,
            )
            probation_data = probation_members_cache.get(member.id)

        status = probation_data.get("status", "")
        if status == "Passed" or status == "passed":
            return  # They have passed probation

        elif status == "Pending" or status == "pending":
            if total_caught >= 300:
                # Update status to Passed
                await update_probation_member_status(bot, member.id, "Passed")
                pretty_log(
                    "info",
                    f"Probation status updated to 'Passed' for {member.name} ({member.id}) after catching {total_caught} Pokémon.",
                    label="💠 Weekly Goal Tracker",
                )
        return  # Exit early if on probation

    # Check for Weekly Angler role
    if fish_caught >= 500 and not weekly_angler_mark:
        weekly_angler_role = member.guild.get_role(STRAYMONS__ROLES.weekly_angler)
        update_weekly_angler_mark(member.id, True)
        if weekly_angler_role and weekly_angler_role not in member.roles:

            if weekly_angler_role and weekly_angler_role not in member.roles:
                await member.add_roles(
                    weekly_angler_role, reason="Reached 500 fish caught in Weekly Goal"
                )
            await channel.send(
                f"Congratulations {member.display_name}! You've reached the weekly angler goal of catching 500 fish! 🎉 We are also giving you the role of Weekly Angler"
            )
            pretty_log(
                "info",
                f"Assigned Weekly Angler role to {member.name} ({member.id})",
                label="💠 WEEKLY GOAL",
                bot=bot,
            )
    # Check if they have reached Weekly Requirement
    if not weekly_requirement_mark:
        if (pokemon_caught >= 175 or total_caught >= 175) or (
            top_line_catches and top_line_catches >= 175
        ):
            update_weekly_requirement_mark(member.id, True)
            await channel.send(
                f"Congratulations {member.display_name}! You've reached the weekly requirement goal of catching 175 Pokémon! 🎉\nDouble-check your stats by running `;clan stats w` and finding your name."
            )
            if goal_tracker_channel:
                await goal_tracker_channel.send(
                    f"{Emojis.gray_star} {member.display_name} has reached the Weekly requirement catch goal of 175!"
                )
            pretty_log(
                "info",
                f"{member.name} ({member.id}) has reached the Weekly Requirement goal | Pokémon Caught: {pokemon_caught}, Total Caught: {total_caught}",
                label="💠 WEEKLY GOAL",
            )

    # Check if they have reached Weekly Grinder
    if not weekly_grinder_mark:
        if (pokemon_caught >= 2000 or total_caught >= 2000) or (
            top_line_catches and top_line_catches >= 2000
        ):
            update_weekly_grinder_mark(member.id, True)
            weekly_grinder_role = member.guild.get_role(STRAYMONS__ROLES.weekly_grinder)
            if weekly_grinder_role and weekly_grinder_role not in member.roles:
                await member.add_roles(
                    weekly_grinder_role,
                    reason="Reached 2000 Pokémon caught in Weekly Goal",
                )
            await channel.send(
                f"🎉 Wow {member.display_name}! You've caught over 2000 Pokémon this week and earned the **Weekly Grinder** role!\n\nCheck /active-giveaways for any current Weekly Grinder giveaways."
            )
            pretty_log(
                "info",
                f"Assigned Weekly Grinder role to {member.name} ({member.id})",
                label="💠 WEEKLY GOAL",
                bot=bot,
            )
            if goal_tracker_channel:
                await goal_tracker_channel.send(
                    f"{Emojis.medal} {member.display_name} has reached the Weekly Grinder goal of catching 2000 Pokémon! {Emojis.celebrate}"
                )
            pretty_log(
                "info",
                f"{member.name} ({member.id}) has reached the Weekly Grinder goal | Pokémon Caught: {pokemon_caught}, Total Caught: {total_caught}",
                label="💠 WEEKLY GOAL",
            )

    # Check if they have reached Weekly Guardian
    if battles_won >= 300 and not weekly_guardian_mark:
        update_weekly_guardian_mark(member.id, True)
        await channel.send(
            f"🏆 **{member.display_name}** has reached **300 Battles Won** this week, You have earned the **Weekly Guardian** role!"
        )
        weekly_guardian_role = guild.get_role(STRAYMONS__ROLES.weekly_guardian)
        if weekly_guardian_role and weekly_guardian_role not in member.roles:
            await member.add_roles(
                weekly_guardian_role, reason="Reached 300 battles won in Weekly Goal"
            )
        pretty_log(
            "info",
            f"Assigned Weekly Guardian role to {member.name} ({member.id})",
            label="💠 WEEKLY GOAL",
        ),


def extract_member_username_from_embed(embed: discord.Embed) -> str | None:
    """
    Extracts the username from the embed author name, e.g. "Congratulations, frayl!" -> "frayl".
    Returns None if not found.
    """
    if embed.author and embed.author.name:
        # Try 'Congratulations, username!' first
        match = re.search(r"Congratulations, ([^!]+)!", embed.author.name)
        if match:
            return match.group(1).strip()
        # Fallback: 'Well done, username!'
        match = re.search(r"Well done, ([^!]+)!", embed.author.name)
        if match:
            return match.group(1).strip()
        # Fallback: 'Great work, username!'
        match = re.search(r"Great work, ([^!]+)!", embed.author.name)
        if match:
            return match.group(1).strip()
    return None


# 💠────────────────────────────────────────────
#           👂 Pokemon Caught Listener Event
# 💠────────────────────────────────────────────
async def pokemon_caught_listener(
    bot: discord.Client, before_message: discord.Message, message: discord.Message
):
    from utils.cache.res_fossil_cache import res_fossils_alert_cache
    from utils.cache.straymon_member_cache import (
        fetch_straymon_member_cache,
        fetch_straymon_user_id_by_username,
    )
    from utils.cache.weekly_goal_tracker_cache import (
        increment_fish_caught,
        mark_weekly_goal_dirty,
        set_pokemon_caught,
        weekly_goal_cache,
    )

    # Process message embeds
    if not message.embeds:
        return

    embed = message.embeds[0]

    member = await get_pokemeow_reply_member(before_message)
    if not member:
        # Fall back to username extraction from embed
        username = extract_member_username_from_embed(embed)
        if not username:
            pretty_log(
                "info",
                f"Could not extract username from embed or reply for message ID {message.id}",
                label="💠 POKÉMON CAUGHT LISTENER",
                bot=bot,
            )
            return
        user_id = fetch_straymon_user_id_by_username(username)
        if not user_id:
            pretty_log(
                "info",
                f"Could not find user ID for username '{username}' from embed for message ID {message.id}",
                label="💠 POKÉMON CAUGHT LISTENER",
                bot=bot,
            )
            return
        member = message.guild.get_member(user_id)
        if not member:
            pretty_log(
                "info",
                f"Could not find member in guild for user ID {user_id} (username: '{username}') for message ID {message.id}",
                label="💠 POKÉMON CAUGHT LISTENER",
                bot=bot,
            )
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

    embed_color = embed.color.value if embed.color else None
    embed_description = embed.description or ""

    # Prevent double processing
    if message.id in processed_caught_messages:
        return
    processed_caught_messages.add(message.id)

    # Fish catch
    if embed_color == FISHING_COLOR:
        increment_fish_caught(member)
        mark_weekly_goal_dirty(member.id)

    # Regular Pokémon catch
    else:
        current_caught = weekly_goal_cache[member_id].get("pokemon_caught", 0)
        new_caught = current_caught + 1
        set_pokemon_caught(member, new_caught)
        mark_weekly_goal_dirty(member.id)

    # Check Weekly Goal progress
    weekly_goal_info = weekly_goal_cache.get(member_id)
    guild = bot.get_guild(STRAYMONS_GUILD_ID)
    if guild:
        await weekly_goal_checker(
            bot=bot,
            member=member,
            member_info=weekly_goal_info,
            channel=message.channel,
            guild=guild,
        )

    # Plume fossil alert
    if ":plume_fossil" in embed_description and member_id in res_fossils_alert_cache:
        user_data = res_fossils_alert_cache[member_id]
        notify = str(user_data.get("notify", "off")).lower()  # ✅ CORRECT!

        if notify == "on":
            embed_msg = discord.Embed(description=";res ex plume_fossil")
            await message.channel.send(
                f"{member.mention} Oh a plume fossil! Don't forget to do the command",
                embed=embed_msg,
            )
            pretty_log(
                "info",
                f"Sent Plume Fossil alert to {member_name} ({member_id})",
                label="🦴 RESEARCH FOSSILS ALERT",
                bot=bot,
            )
