import asyncio
import re
from datetime import datetime

import discord
from discord.ext import commands

from config.aesthetic import Emojis
from config.current_setup import POKEMEOW_APPLICATION_ID
from utils.cache.cache_list import timer_cache  # 💜 import your cache
from utils.loggers.debug_log import debug_log, enable_debug
from utils.loggers.pretty_logs import pretty_log

#enable_debug(f"{__name__}.detect_pokemeow_reply")
# 🗂 Track scheduled "command ready" tasks to avoid duplicates
ready_tasks = {}


# 💜────────────────────────────────────────────
#   Function: detect_pokemeow_reply
#   Handles Pokemon timer notifications per user settings
# 💜────────────────────────────────────────────
async def detect_pokemeow_reply(message: discord.Message):
    """
    Triggered on any message.
    Handles Pokemon ready notifications depending on user's timer cache settings:
      - off → ignore
      - on → ping them in channel
      - on w/o pings → send message w/o mention
      - react → ✅ react to PokeMeow's message
    """
    try:
        debug_log(f"Received message from author ID: {message.author.id}")
        if message.author.id != POKEMEOW_APPLICATION_ID:
            debug_log("Message is not from PokeMeow bot, ignoring.")
            return

        debug_log(f"Message content: {message.content[:100]}")
        match = re.search(r"\*\*(.+?)\*\* found a wild", message.content)
        if not match:
            debug_log("No username match found in message content.")
            return

        username = match.group(1).strip()
        debug_log(f"Extracted username: {username}")
        guild = message.guild

        # Match member case-insensitive
        member = discord.utils.find(
            lambda m: m.name.lower() == username.lower()
            or m.display_name.lower() == username.lower(),
            guild.members,
        )
        if not member:
            debug_log(f"No guild member found matching username: {username}")
            return

        debug_log(f"Matched member: {member} (ID: {member.id})")

        # -------------------------------
        # 💜 Check timer_cache settings
        # -------------------------------
        # show 3 timer cache
        debug_log(f"Current timer_cache keys: {list(timer_cache.keys())[:3]} (showing 3)")
        user_settings = timer_cache.get(member.id)

        debug_log(f"User settings from timer_cache: {user_settings}")
        if not user_settings:
            debug_log("No user settings found in timer_cache.")
            return

        setting = (user_settings.get("pokemon_setting") or "off").lower()
        debug_log(f"Pokemon timer setting: {setting}")
        if setting == "off":
            debug_log("Pokemon timer setting is off, not notifying.")
            return

        # Cancel previous ready task if any
        if member.id in ready_tasks and not ready_tasks[member.id].done():
            debug_log(f"Cancelling previous ready task for member {member.id}")
            ready_tasks[member.id].cancel()

        # Schedule behavior depending on setting
        async def notify_ready():
            # 💜────────────────────────────────────────────
            #   Pokemon Timer Notification Task
            # 💜────────────────────────────────────────────
            try:
                debug_log(f"notify_ready: sleeping for 11 seconds before notifying.")
                await asyncio.sleep(11)
                debug_log(
                    f"notify_ready: woke up, preparing to notify (setting: {setting})",
                    highlight=True,
                )
                """pretty_log(
                    tag="info",
                    message=f"Sending Pokemon timer ready notification to {member} (setting: {setting})",
                )"""
                if setting == "on":
                    debug_log(f"Notifying with mention for {member}")
                    await message.channel.send(
                        f"{Emojis.pokespawn} {member.mention}, your </pokemon:1015311085441654824> command is ready!"
                    )
                elif setting == "on w/o pings" or setting == "on_no_pings":
                    debug_log(f"Notifying without mention for {member}")
                    await message.channel.send(
                        f"{Emojis.pokespawn} **{member.name}**, your </pokemon:1015311085441654824> command is ready!"
                    )
                elif setting == "react":
                    debug_log(f"Adding reaction for {member}")
                    await message.add_reaction(Emojis.brown_check)

            except asyncio.CancelledError:
                debug_log(f"notify_ready: Cancelled for {member}")
                # 💙 [CANCELLED] Scheduled ready notification cancelled
                pretty_log(
                    tag="info",
                    message=f"Cancelled scheduled ready notification for {member}",
                )
            except Exception as e:
                debug_log(f"notify_ready: Exception occurred for {member}: {e}")
                # 💜 [MISSED] Timer ran correctly but message failed
                # Trackable: include member ID and username
                pretty_log(
                    tag="info",
                    message=(
                        f"Missed Pokemon timer notification for {member} "
                        f"(ID: {member.id}). Timer ran correctly but message failed: {e}"
                    ),
                )

        debug_log(f"Creating notify_ready task for member {member.id}")
        ready_tasks[member.id] = asyncio.create_task(notify_ready())

    except Exception as e:
        debug_log(f"Exception in detect_pokemeow_reply: {e}", highlight=True)
        pretty_log(
            tag="critical",
            message=f"Unhandled exception in detect_pokemeow_reply: {e}",
        )
