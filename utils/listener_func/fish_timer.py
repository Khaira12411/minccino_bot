import asyncio
import re
from datetime import datetime

import discord
from discord.ext import commands

from config.aesthetic import Emojis
from config.current_setup import POKEMEOW_APPLICATION_ID
from utils.essentials.pokemeow_helpers import get_pokemeow_reply_member
from utils.loggers.pretty_logs import pretty_log

FISH_TIMER = 25

# 🗂 Track scheduled "command ready" tasks to avoid duplicates
fish_ready_tasks = {}


def extract_fishing_trainer_name(description: str) -> str | None:
    """
    Extracts the trainer name (e.g. 'khy.09') from a PokéMeow fishing embed description.
    Example: '<:irida:...> **khy.09** cast a ...'
    """
    match = re.search(r"\*\*(.+?)\*\* cast a", description)
    if match:
        return match.group(1).strip()
    return None


# 💜────────────────────────────────────────────
#   Function: detect_pokemeow_reply
#   Handles Pokemon timer notifications per user settings
# 💜────────────────────────────────────────────
async def fish_timer_handler(message: discord.Message):
    """
    Triggered on any message.
    Handles Fish ready notifications depending on user's timer cache settings:
      - off → ignore
      - on → ping them in channel
      - on w/o pings → send message w/o mention
    """
    try:
        if message.author.id != POKEMEOW_APPLICATION_ID:
            return

        embed = message.embeds[0]
        embed_description = embed.description or ""
        guild = message.guild

        member = await get_pokemeow_reply_member(message)
        if not member:
            # Fall back to username extraction if needed
            user_name = extract_fishing_trainer_name(embed_description)
            if not user_name:
                return
            from utils.cache.timers_cache import fetch_id_by_user_name

            user_id = fetch_id_by_user_name(user_name)
            if not user_id:
                return
            member = guild.get_member(user_id)
            if not member:
                return

        # -------------------------------
        # 💜 Check timer_cache settings
        # -------------------------------
        from utils.cache.timers_cache import timer_cache

        user_settings = timer_cache.get(member.id)
        if not user_settings:
            return

        setting = (user_settings.get("fish_setting") or "off").lower()
        if setting == "off":
            return

        # Cancel previous ready task if any
        if member.id in fish_ready_tasks and not fish_ready_tasks[member.id].done():
            fish_ready_tasks[member.id].cancel()

        # Schedule behavior depending on setting
        async def notify_ready():
            # 💜────────────────────────────────────────────
            #   Fish Timer Notification Task
            # 💜────────────────────────────────────────────
            try:
                await asyncio.sleep(FISH_TIMER)

                if setting == "on":
                    await message.channel.send(
                        f"{Emojis.fish_spawn} {member.mention}, your </fish spawn:1015311084812501026> command is ready! "
                    )  
                elif setting == "on_no_pings":
                    await message.channel.send(
                        f"{Emojis.fish_spawn} **{member.name}**, your </fish spawn:1015311084812501026> command is ready!"
                    )

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

        fish_ready_tasks[member.id] = asyncio.create_task(notify_ready())

    except Exception as e:
        pretty_log(
            tag="critical",
            message=f"Unhandled exception in detect_pokemeow_reply: {e}",
        )
