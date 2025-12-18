import asyncio
import re
from datetime import datetime

import discord
from discord.ext import commands

from config.aesthetic import Emojis
from config.current_setup import MINCCINO_COLOR, POKEMEOW_APPLICATION_ID
from utils.cache.cache_list import timer_cache
from utils.loggers.debug_log import debug_log, enable_debug
from utils.loggers.pretty_logs import pretty_log

# enable_debug(f"{__name__}.detect_pokemeow_battle")
# enable_debug(f"{__name__}.grab_enemy_id")
# 🗂 Track scheduled "command ready" tasks to avoid duplicates
battle_ready_tasks = {}

# BATTLE TOWER NPC IDS 400 TO 407
BATTLE_TOWER_NPC_IDS = [400, 401, 402, 403, 404, 405, 406, 407]
# MC IDS 500 to 548
MEGA_CHAMBER_NPC_IDS = [
    500,
    501,
    502,
    503,
    504,
    505,
    506,
    507,
    508,
    509,
    510,
    511,
    512,
    513,
    514,
    515,
    516,
    517,
    518,
    519,
    520,
    521,
    522,
    523,
    524,
    525,
    526,
    527,
    528,
    529,
    530,
    532,
    533,
    534,
    535,
    536,
    537,
    538,
    539,
    540,
    541,
    542,
    543,
    544,
    545,
    546,
    547,
    548,
]

MC_NPC_ENEMY_ID_MAP = {
    500: [600, 601, 602],  # Venusaur
    501: [603, 604, 605],  # MCX
    502: [606, 607, 608],  # MCY
    503: [609, 610, 611],  # Blastoise
    504: [612, 613, 614],  # Sceptile
    505: [615, 616, 617],  # Blaziken
    506: [618, 619, 620],  # Swampert
    507: [621, 622, 623],  # Gardevoir
    508: [624, 625, 626],  # Beedrill
    509: [627, 628, 629],  # Ampharos
    510: [630, 631, 632],  # Sableye
    511: [633, 634, 635],  # Garchomp
    512: [636, 637, 638],  # Pidgeot
    513: [639, 640, 641],  # Gengar
    514: [642, 643, 644],  # Steelix
    515: [645, 646, 647],  # Lopunny
    516: [648, 649, 650],  # Alakazam
    517: [651, 652, 653],  # Scizor
    518: [654, 655, 656],  # Mawile
    519: [657, 658, 659],  # Lucario
    520: [660, 661, 662],  # Slowbro
    521: [663, 664, 665],  # Heracross
    522: [666, 667, 668],  # Aggron
    523: [669, 670, 671],  # Abomasnow
    524: [672, 673, 674],  # Kangaskhan
    525: [675, 676, 677],  # Houndoom
    526: [678, 679, 680],  # Medicham
    527: [681, 682, 683],  # Gallade
    528: [684, 685, 686],  # Pinsir
    529: [687, 688, 689],  # Tyranitar
    530: [690, 691, 692],  # Manectric
    # No 531
    532: [693, 694, 695],  # Audino
    533: [696, 697, 698],  # Gyarados
    534: [699, 700, 701],  # Aerodactyl
    535: [702, 703, 704],  #  Sharpedo
    536: [705, 706, 707],  # Diancie
    537: [708, 709, 710],  # MMX
    538: [711, 712, 713],  # Camerupt
    539: [714, 715, 716],  # Altaria
    540: [717, 718, 719],  # Mray
    541: [720, 721, 722],  # MMY
    542: [723, 724, 725],  # Banette
    543: [726, 727, 728],  # Absol
    544: [729, 730, 731],  # Glalie
    545: [732, 733, 734],  # Salamence
    546: [735, 736, 737],  # Metagross
    547: [738, 739, 740],  # Latias
    548: [741, 742, 743],  # Latios
}


def find_key_by_npc_id(npc_id: int):
    for key, values in MC_NPC_ENEMY_ID_MAP.items():
        if npc_id in values:
            return key
    return None


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
                # Battle Tower NPC
                if enemy_id and int(enemy_id) in BATTLE_TOWER_NPC_IDS:
                    battle_embed.description = ";b npc bt"
                # Mega Chamber NPC
                elif 600 <= int(enemy_id) <= 743:
                    mc_npc_id = find_key_by_npc_id(int(enemy_id))
                    battle_embed.description = f";b npc {mc_npc_id}"
                # Regular NPC
                elif enemy_id:
                    battle_embed.description = f";b npc {enemy_id}"
                else:
                    battle_embed.description = "Your battle command is ready!"

                if setting == "on":
                    debug_log("Sending notification (ping)")
                    await message.channel.send(
                        content=f"{Emojis.battle_spawn} {challenger.mention}, your battle command is ready!",
                        embed=battle_embed,
                    )
                elif setting == "on w/o pings" or setting == "on_no_pings":
                    debug_log("Sending notification (no ping)")
                    await message.channel.send(
                        content=f"{Emojis.battle_spawn} **{challenger.name}**, your battle command is ready!",
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
