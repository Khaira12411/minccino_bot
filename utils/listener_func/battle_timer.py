import asyncio
import re
from typing import Optional

import discord
from discord.ext import commands

from config.aesthetic import Emojis
from config.current_setup import MINCCINO_COLOR, POKEMEOW_APPLICATION_ID
from utils.cache.cache_list import timer_cache
from utils.loggers.debug_log import debug_log, enable_debug
from utils.loggers.pretty_logs import pretty_log

battle_ready_tasks = {}
enable_debug(f"{__name__}._wait_for_enemy_id")
enable_debug(f"{__name__}._send_battle_ready_notification")
enable_debug(f"{__name__}._cancel_existing_timer_task")
enable_debug(f"{__name__}.detect_pokemeow_battle")
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


IGNORE_BATTLE_FOLLOWUP_LIST = [
    "Battle Pyramid",
    "Battle Pike",
    "Battle Arena",
    "Battle Factory",
    "Battle Dome",
    "Battle Palace",
    "Battle Tower",
    "Mega Chamber",
]


CHALLENGE_REGEX = re.compile(
    r"(?:<a?:\w+:\d+>\s*)?\*{0,2}(.+?)\*{0,2}\s+challenged\s+(?:<a?:\w+:\d+>\s*)?\*{0,2}(.+?)\*{0,2}(?:\s+to a battle!?)?",
    re.IGNORECASE,
)


def _is_battle_challenge_embed(embed: discord.Embed) -> bool:
    return bool(
        embed.author and embed.author.name and "PokeMeow Battles" in embed.author.name
    )


def _normalize_challenge_name(raw_name: str) -> str:
    name = raw_name.strip().strip("*")
    name = re.sub(r"^(?:<a?:\w+:\d+>\s*)+", "", name)
    name = re.sub(r"^[^\w]+", "", name)
    return name.strip()


def _parse_challenge_names(description: str) -> Optional[tuple[str, str]]:
    match = CHALLENGE_REGEX.search(description)
    if not match:
        return None

    challenger = _normalize_challenge_name(match.group(1))
    opponent = _normalize_challenge_name(match.group(2))

    if not challenger or not opponent:
        return None

    return challenger, opponent


def _find_member_by_name(
    guild: discord.Guild, member_name: str
) -> Optional[discord.Member]:
    target = member_name.lower()
    return discord.utils.find(
        lambda m: m.name.lower() == target or m.display_name.lower() == target,
        guild.members,
    )


def _is_ignored_battle_followup(footer_text: str) -> bool:
    return any(keyword in footer_text for keyword in IGNORE_BATTLE_FOLLOWUP_LIST)


def _is_relevant_enemy_followup(embed: discord.Embed, opponent_name: str) -> bool:
    footer_text = embed.footer.text if embed.footer else ""
    description = embed.description or ""
    same_opponent = opponent_name in description
    if not same_opponent:
        return False

    # Treat ignored follow-ups as relevant so we can actively block timer creation.
    if _is_ignored_battle_followup(footer_text):
        return True

    return "Enemy ID:" in footer_text or (
        "Battle Pike Round" in footer_text and "Moves taken" in footer_text
    )


def _extract_enemy_id(footer_text: str) -> Optional[str]:
    enemy_match = re.search(r"Enemy ID:\s*(\d+)", footer_text)
    if enemy_match:
        return enemy_match.group(1)
    if "Battle Pike Round" in footer_text and "Moves taken" in footer_text:
        return "bf"
    return None


async def _wait_for_enemy_id(
    bot: commands.Bot, opponent_name: str
) -> tuple[Optional[str], bool]:
    def check(m: discord.Message) -> bool:
        if m.author.id != POKEMEOW_APPLICATION_ID or not m.embeds:
            return False
        return _is_relevant_enemy_followup(m.embeds[0], opponent_name)

    try:
        debug_log("Waiting for follow-up battle message")
        followup: discord.Message = await bot.wait_for(
            "message", timeout=10, check=check
        )
        followup_embed = followup.embeds[0]
        footer_text = followup_embed.footer.text if followup_embed.footer else ""

        if _is_ignored_battle_followup(footer_text):
            debug_log(
                "Ignored follow-up footer detected; blocking battle-ready timer creation"
            )
            return None, True

        enemy_id = _extract_enemy_id(footer_text)
        debug_log(f"Enemy ID lookup result: {enemy_id}")
        return enemy_id, False
    except asyncio.TimeoutError:
        debug_log("Timeout while waiting for enemy follow-up")
        return None, False
    except Exception as e:
        debug_log(f"Exception while waiting for enemy follow-up: {e}")
        return None, False


def _build_battle_command(enemy_id: Optional[str]) -> str:
    if not enemy_id:
        return "Your </battle:1015311084422434819> command is ready!"

    if enemy_id == "bf":
        return ";b npc bf"

    if enemy_id.isdigit():
        numeric_enemy_id = int(enemy_id)

        if numeric_enemy_id in BATTLE_TOWER_NPC_IDS:
            return ";b npc bt"

        if 600 <= numeric_enemy_id <= 743:
            mc_npc_id = find_key_by_npc_id(numeric_enemy_id)
            if mc_npc_id is not None:
                return f";b npc {mc_npc_id}"

        # Keep legacy behavior where long IDs are interpreted as user battle IDs.
        if len(enemy_id) >= 15 or numeric_enemy_id == 15:
            return f";b user {enemy_id}"

    return f";b npc {enemy_id}"


async def _send_battle_ready_notification(
    message: discord.Message,
    challenger: discord.Member,
    setting: str,
    battle_command: str,
) -> None:
    if setting == "react":
        debug_log("Sending battle-ready notice via reaction")
        await message.add_reaction(Emojis.gray_check)
        return

    battle_embed = discord.Embed(color=MINCCINO_COLOR)
    battle_embed.description = battle_command

    if setting == "on":
        debug_log("Sending battle-ready notice with mention")
        await message.channel.send(
            content=f"{Emojis.battle_spawn} {challenger.mention}, your </battle:1015311084422434819> command is ready!",
            embed=battle_embed,
        )
        return

    if setting in {"on w/o pings", "on_no_pings"}:
        debug_log("Sending battle-ready notice without mention")
        await message.channel.send(
            content=f"{Emojis.battle_spawn} **{challenger.name}**, your </battle:1015311084422434819> command is ready!",
            embed=battle_embed,
        )


def _cancel_existing_timer_task(challenger_id: int) -> None:
    existing_task = battle_ready_tasks.get(challenger_id)
    if existing_task and not existing_task.done():
        debug_log("Cancelling existing battle-ready timer task")
        existing_task.cancel()


async def detect_pokemeow_battle(bot: commands.Bot, message: discord.Message):
    try:
        debug_log("Entered detect_pokemeow_battle()", disabled=True)

        if message.author.id != POKEMEOW_APPLICATION_ID:
            debug_log("Message not from PokeMeow; skipping")
            return

        if not message.embeds:
            debug_log("Message has no embeds; skipping")
            return

        embed = message.embeds[0]
        if not _is_battle_challenge_embed(embed):
            debug_log("Embed is not a battle challenge; skipping", disabled=True)
            return

        description = embed.description or ""
        parsed_names = _parse_challenge_names(description)
        if not parsed_names:
            compact_description = " ".join(description.split())
            if len(compact_description) > 280:
                compact_description = compact_description[:277] + "..."

            debug_log(
                f"Could not parse challenger/opponent names | description={compact_description}"
            )
            pretty_log(
                "warning",
                "Could not parse battle challenge message for challenger/opponent names "
                f"| description={compact_description}",
            )
            return

        challenger_name, opponent_name = parsed_names
        debug_log(f"Parsed challenger={challenger_name}, opponent={opponent_name}")

        if not message.guild:
            debug_log("Message has no guild context; skipping")
            return

        challenger = _find_member_by_name(message.guild, challenger_name)
        if not challenger:
            debug_log("Could not match challenger to guild member")
            return

        user_settings = timer_cache.get(challenger.id)
        if not user_settings:
            debug_log("No timer settings found for challenger")
            return

        setting = (user_settings.get("battle_setting") or "off").lower()
        if setting == "off":
            debug_log("Battle timer is disabled for this user")
            return

        _cancel_existing_timer_task(challenger.id)

        enemy_id_holder = {"id": None}
        timer_start = asyncio.get_running_loop().time()

        async def notify_battle_ready(delay_seconds: float = 60.0) -> None:
            try:
                await asyncio.sleep(delay_seconds)
                battle_command = _build_battle_command(enemy_id_holder["id"])
                debug_log(f"Battle-ready command resolved: {battle_command}")
                await _send_battle_ready_notification(
                    message=message,
                    challenger=challenger,
                    setting=setting,
                    battle_command=battle_command,
                )
            except asyncio.CancelledError:
                debug_log("Battle-ready timer task cancelled")
            except Exception as e:
                debug_log(f"Battle-ready timer task error: {e}")

        async def prepare_and_schedule_battle_ready() -> None:
            try:
                enemy_id, block_timer = await _wait_for_enemy_id(bot, opponent_name)
                if block_timer:
                    debug_log(
                        "Blocked battle-ready timer due to ignored follow-up footer"
                    )
                    return

                enemy_id_holder["id"] = enemy_id
                elapsed = asyncio.get_running_loop().time() - timer_start
                remaining = max(0.0, 60 - elapsed)
                debug_log(
                    f"Scheduling battle-ready timer with remaining delay={remaining:.2f}s"
                )
                battle_ready_tasks[challenger.id] = bot.loop.create_task(
                    notify_battle_ready(remaining)
                )
            except asyncio.CancelledError:
                debug_log("Battle-ready precheck task cancelled")
            except Exception as e:
                debug_log(f"Battle-ready precheck error: {e}")

        battle_ready_tasks[challenger.id] = bot.loop.create_task(
            prepare_and_schedule_battle_ready()
        )
        debug_log("Scheduled battle-ready precheck", highlight=True)

    except Exception as e:
        debug_log(f"Exception in detect_pokemeow_battle: {e}")
        pretty_log("critical", f"Unhandled exception in detect_pokemeow_battle: {e}")
