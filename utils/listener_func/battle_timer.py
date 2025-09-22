import asyncio
import re
from datetime import datetime

import discord
from discord.ext import commands

from config.aesthetic import Emojis
from config.current_setup import MINCCINO_COLOR, POKEMEOW_APPLICATION_ID
from utils.cache.timers_cache import timer_cache
from utils.loggers.debug_log import debug_log, enable_debug
from utils.loggers.pretty_logs import pretty_log

#enable_debug(f"{__name__}.detect_pokemeow_battle")
#enable_debug(f"{__name__}.grab_enemy_id")
# 🗂 Track scheduled "command ready" tasks to avoid duplicates
battle_ready_tasks = {}


# 💜────────────────────────────────────────────
#   Function: detect_pokemeow_battle (with debug)
# 💜────────────────────────────────────────────
async def detect_pokemeow_battle(bot: commands.Bot, message: discord.Message):
    try:
        debug_log("Entered detect_pokemeow_battle()", disabled=True)

        # ✅ Only PokéMeow messages
        if message.author.id != POKEMEOW_APPLICATION_ID:
            return
        if not message.embeds:
            return

        embed = message.embeds[0]

        # ✅ Step 1: detect "challenged ... to a battle!"
        if not (embed.author and "PokeMeow Battles" in embed.author.name):
            debug_log("Ignored: embed not a battle challenge", disabled=True)
            return

        description = embed.description or ""
        debug_log(f"Embed description: {description}")

        # Format: "**Alice** challenged **Bob** to a battle!"
        match = re.search(
            r"(?:<:\w+?:\d+>\s*)?\*\*(.+?)\*\* challenged (?:<:\w+?:\d+>\s*)?\*\*(.+?)\*\*",
            description,
        )
        if not match:
            debug_log("Regex failed: no challenger/opponent match")
            return

        challenger_name = match.group(1).strip()
        opponent_name = match.group(2).strip()
        debug_log(
            f"Challenger: {challenger_name}, Opponent: {opponent_name}", disabled=True
        )

        # ✅ Match challenger in guild
        guild = message.guild
        challenger = discord.utils.find(
            lambda m: m.name.lower() == challenger_name.lower()
            or m.display_name.lower() == challenger_name.lower(),
            guild.members,
        )
        if not challenger:
            debug_log("Challenger not found in guild members")
            return
        debug_log(f"Matched challenger: {challenger} ({challenger.id})", disabled=True)

        # ✅ Step 2: check user settings
        user_settings = timer_cache.get(challenger.id)
        debug_log(f"User settings: {user_settings}")
        if not user_settings:
            return
        setting = (user_settings.get("battle_setting") or "off").lower()
        debug_log(f"Battle setting: {setting}", disabled=True)
        if setting == "off":
            return

        # ✅ Cancel existing task if user already has one
        if (
            challenger.id in battle_ready_tasks
            and not battle_ready_tasks[challenger.id].done()
        ):
            debug_log("Cancelling existing timer task")
            battle_ready_tasks[challenger.id].cancel()

        # ✅ Storage for enemy_id (filled later)
        enemy_id_holder = {"id": None}

        # 💜 Step 3: background task to grab Enemy ID from follow-up
        async def grab_enemy_id():
            debug_log("Started grab_enemy_id() background task")

            def check(m: discord.Message):
                if m.author.id != POKEMEOW_APPLICATION_ID:
                    return False
                if not m.embeds:
                    return False
                emb = m.embeds[0]
                result = (
                    emb.footer
                    and "Enemy ID:" in (emb.footer.text or "")
                    and opponent_name in (emb.description or "")
                )
                debug_log(
                    f"Checking message for Enemy ID... "
                    f"footer={emb.footer.text if emb.footer else None}, "
                    f"description={emb.description}, "
                    f"match={result}"
                )
                return result

            try:
                followup: discord.Message = await bot.wait_for(
                    "message", timeout=10.0, check=check
                )
                debug_log("Follow-up embed received ✅")

                emb = followup.embeds[0]
                footer_text = emb.footer.text if emb.footer else ""
                debug_log(f"Follow-up footer text: {footer_text}")

                enemy_match = re.search(r"Enemy ID:\s*(\d+)", footer_text)
                if enemy_match:
                    enemy_id_holder["id"] = enemy_match.group(1)
                    debug_log(
                        f"Enemy ID captured: {enemy_id_holder['id']} 🎯",
                        highlight=True,
                    )
                else:
                    debug_log("Regex failed: Enemy ID not found in footer text ❌")

            except asyncio.TimeoutError:
                debug_log("Timeout: no follow-up embed with Enemy ID found ⏰")

        bot.loop.create_task(grab_enemy_id())

        # 💜 Step 4: schedule 60s notification immediately
        async def notify_battle_ready():
            try:
                debug_log("Timer started (60s)")
                await asyncio.sleep(60)
                enemy_id = enemy_id_holder["id"]

                debug_log(f"Timer finished. Enemy ID={enemy_id}")

                battle_embed = discord.Embed(color=MINCCINO_COLOR)
                if enemy_id:
                    battle_embed.description = f"`;b npc {enemy_id}`"
                else:
                    battle_embed.description = "Your battle command is ready!"

                if setting == "on":
                    debug_log("Sending notification (ping)")
                    await message.channel.send(
                        content=f"{challenger.mention}, your battle timer is ready! {Emojis.Minccino_Hug}",
                        embed=battle_embed,
                    )
                elif setting == "on w/o pings":
                    debug_log("Sending notification (no ping)")
                    await message.channel.send(
                        content=f"{challenger.display_name}, your battle timer is ready! {Emojis.Minccino_Hug}",
                        embed=battle_embed,
                    )
                elif setting == "react":
                    debug_log("Adding reaction notification")
                    await message.add_reaction(Emojis.gray_check)

            except asyncio.CancelledError:
                debug_log("Timer task cancelled")
            except Exception as e:
                debug_log(f"Timer task error: {e}")

        battle_ready_tasks[challenger.id] = bot.loop.create_task(notify_battle_ready())
        debug_log("Scheduled notify_battle_ready() task", highlight=True)

    except Exception as e:
        pretty_log("critical", f"Unhandled exception in detect_pokemeow_battle: {e}")
