import asyncio
import re
from datetime import datetime

import discord
from discord.ext import commands

from config.aesthetic import Emojis
from config.current_setup import POKEMEOW_APPLICATION_ID
from utils.cache.timers_cache import timer_cache  # 💜 import your cache
from utils.loggers.pretty_logs import pretty_log

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
        if message.author.id != POKEMEOW_APPLICATION_ID:
            return

        match = re.search(r"\*\*(.+?)\*\* found a wild", message.content)
        if not match:
            return

        username = match.group(1).strip()
        guild = message.guild

        # Match member case-insensitive
        member = discord.utils.find(
            lambda m: m.name.lower() == username.lower()
            or m.display_name.lower() == username.lower(),
            guild.members,
        )
        if not member:
            return

        # -------------------------------
        # 💜 Check timer_cache settings
        # -------------------------------
        user_settings = timer_cache.get(member.id)
        if not user_settings:
            return

        setting = (user_settings.get("pokemon_setting") or "off").lower()
        if setting == "off":
            return

        # Cancel previous ready task if any
        if member.id in ready_tasks and not ready_tasks[member.id].done():
            ready_tasks[member.id].cancel()

        # Schedule behavior depending on setting
        async def notify_ready():
            # 💜────────────────────────────────────────────
            #   Pokemon Timer Notification Task
            # 💜────────────────────────────────────────────
            try:
                await asyncio.sleep(11)

                if setting == "on":
                    await message.channel.send(
                        f"{Emojis.brown_bear_two} {member.mention}, your Pokemon command is ready! {Emojis.Minccino_Hug}"
                    )
                elif setting == "on w/o pings":
                    await message.channel.send(
                        f"{Emojis.brown_bear_two} {member.display_name}, your Pokemon command is ready! {Emojis.Minccino_Hug}"
                    )
                elif setting == "react":
                    await message.add_reaction(Emojis.brown_check)

            except asyncio.CancelledError:
                # 💙 [CANCELLED] Scheduled ready notification cancelled
                pretty_log(
                    tag="info",
                    message=f"Cancelled scheduled ready notification for {member}",
                )
            except Exception as e:
                # 💜 [MISSED] Timer ran correctly but message failed
                # Trackable: include member ID and username
                pretty_log(
                    tag="error",
                    message=(
                        f"Missed Pokemon timer notification for {member} "
                        f"(ID: {member.id}). Timer ran correctly but message failed: {e}"
                    ),
                )

        ready_tasks[member.id] = asyncio.create_task(notify_ready())

    except Exception as e:
        pretty_log(
            tag="critical",
            message=f"Unhandled exception in detect_pokemeow_reply: {e}",
        )
