import discord

from config.aesthetic import *
from config.straymons_constants import STRAYMONS__ROLES, STRAYMONS__TEXT_CHANNELS
from utils.database.weekly_goal_tracker_db_func import upsert_weekly_goal
from utils.essentials.pokemeow_helpers import get_pokemeow_reply_member
from utils.loggers.pretty_logs import pretty_log

FISHING_COLOR = 0x87CEFA
processed_caught_messages = set()


# 💠────────────────────────────────────────────
#           👂 Pokemon Caught Listener Event
# 💠────────────────────────────────────────────
async def pokemon_caught_listener(
    bot: discord.Client, before_message: discord.Message, message: discord.Message
):
    from utils.cache.res_fossil_cache import res_fossils_alert_cache
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

    member = await get_pokemeow_reply_member(before_message)
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
    if not message.embeds:
        return

    embed = message.embeds[0]
    embed_color = embed.color.value if embed.color else None
    embed_description = embed.description or ""

    #Prevent double processing
    if message.id in processed_caught_messages:
        return
    processed_caught_messages.add(message.id)

    # Fish catch
    if embed_color == FISHING_COLOR:
        increment_fish_caught(member)
        mark_weekly_goal_dirty(member.id)
        new_fish_caught = weekly_goal_cache[member_id].get("fish_caught", 0)

        if new_fish_caught >= 500 and not weekly_goal_cache[member_id].get(
            "weekly_angler_mark", False
        ):
            update_weekly_angler_mark(member.id, True)
            await message.channel.send(
                f"Congratulations {member.display_name}! You've reached the weekly angler goal of catching 500 fish! 🎉 We are also giving you the role of Weekly Angler"
            )

            weekly_angler_role = message.guild.get_role(STRAYMONS__ROLES.weekly_angler)
            if weekly_angler_role and weekly_angler_role not in member.roles:
                await member.add_roles(
                    weekly_angler_role, reason="Reached 500 fish caught in Weekly Goal"
                )
                pretty_log(
                    "info",
                    f"Assigned Weekly Angler role to {member_name} ({member_id})",
                    label="💠 WEEKLY GOAL",
                    bot=bot,
                )

    # Regular Pokémon catch
    else:
        current_caught = weekly_goal_cache[member_id].get("pokemon_caught", 0)
        new_caught = current_caught + 1
        set_pokemon_caught(member, new_caught)
        mark_weekly_goal_dirty(member.id)

        # Weekly requirement 175 Pokémon
        if new_caught >= 175 and not weekly_goal_cache[member_id].get(
            "weekly_requirement_mark", False
        ):
            update_weekly_requirement_mark(member.id, True)
            await message.channel.send(
                f"Congratulations {member.display_name}! You've reached the weekly requirement goal of catching 175 Pokémon! 🎉"
            )

            goal_tracker_channel = message.guild.get_channel(
                STRAYMONS__TEXT_CHANNELS.goal_tracker
            )
            if goal_tracker_channel:
                await goal_tracker_channel.send(
                    f"{Emojis.gray_star} {member.display_name} has reached the Weekly requirement catch goal of 175!"
                )

        # Weekly grinder 2000 Pokémon
        if new_caught >= 2000 and not weekly_goal_cache[member_id].get(
            "weekly_grinder_mark", False
        ):
            update_weekly_grinder_mark(member.id, True)
            await message.channel.send(
                f"🎉 Wow {member.display_name}! You've caught over 2000 Pokémon this week and earned the **Weekly Grinder** role! Check /active-giveaways for any current Weekly Grinder giveaways."
            )

            weekly_grinder_role = message.guild.get_role(
                STRAYMONS__ROLES.weekly_grinder
            )
            if weekly_grinder_role and weekly_grinder_role not in member.roles:
                await member.add_roles(
                    weekly_grinder_role,
                    reason="Reached 2000 Pokémon caught in Weekly Goal",
                )
                pretty_log(
                    "info",
                    f"Assigned Weekly Grinder role to {member_name} ({member_id})",
                    label="💠 WEEKLY GOAL",
                    bot=bot,
                )

            goal_tracker_channel = message.guild.get_channel(
                STRAYMONS__TEXT_CHANNELS.goal_tracker
            )
            if goal_tracker_channel:
                await goal_tracker_channel.send(
                    f"{Emojis.medal} {member.display_name} has reached the Weekly Grinder goal of catching 2000 Pokémon! {Emojis.celebrate}"
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
