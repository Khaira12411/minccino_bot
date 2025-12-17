import inspect
import re

import discord

from config.fish_rarity import FISH_RARITY
from utils.cache.ball_reco_cache import ball_reco_cache
from utils.cache.boosted_channels_cache import boosted_channels_cache
from utils.cache.daily_fa_ball_cache import daily_faction_ball_cache
from utils.cache.faction_ball_alert_cache import faction_ball_alert_cache
from utils.cache.straymon_member_cache import straymon_member_cache
from utils.cache.water_state_cache import get_water_state, update_water_state
from utils.listener_func.catch_rate import *
from utils.listener_func.catch_rate import ball_emojis, best_ball_fishing, rarity_emojis
from utils.loggers.debug_log import debug_log, enable_debug
from utils.loggers.pretty_logs import pretty_log

# enable_debug(f"{__name__}.recommend_fishing_ball")
# enable_debug(f"{__name__}.extract_water_state_from_author")


DEBUG = False
FISHING_COLOR = 0x87CEFA  # sky blue
processed_fishing_messages = set()
NAME_PATTERN = re.compile(r"\*\*(?:(Shiny|Golden)\s+)?([A-Za-z_]+)\*\*", re.IGNORECASE)

WILD_SPAWN_PATTERN = re.compile(
    r"\*\*(?P<trainer>.+?)\*\*\s+fished a wild\s+"
    r"(?:<:[^>]+>)*\s*"
    r"(?:(?P<form>Shiny|Golden)\s+)?"
    r"(?:<:[^>]+>)*\s*"
    r"\*\*(?P<pokemon>[A-Za-z_]+)\*\*!",
    re.IGNORECASE,
)


def extract_water_state_from_author(author_name: str) -> str:

    name_lower = author_name.lower()
    if "gold" in name_lower:
        state = "special"
    elif "calm" in name_lower:
        state = "calm"
    elif "strong" in name_lower:
        state = "strong"
    elif "moderate" in name_lower:
        state = "moderate"
    elif "intense" in name_lower:
        state = "intense"
    else:
        state = None

    debug_log(f"extract_water_state_from_author('{author_name}') → {state}")
    return state


def parse_pokemeow_fishing_spawn(message: discord.Message):
    from utils.cache.water_state_cache import get_water_state

    if not message.embeds:
        return None

    embed = message.embeds[0]

    if not embed.color or embed.color.value != FISHING_COLOR:
        return None

    trainer_id = None
    trainer_name = None
    if message.reference and getattr(message.reference, "resolved", None):
        resolved_author = getattr(message.reference.resolved, "author", None)
        trainer_id = resolved_author.id if resolved_author else None

    if not trainer_id and embed.description:
        name_match = re.search(r"\*\*(.+?)\*\*", embed.description)
        if name_match:
            trainer_name = name_match.group(1)

    if not trainer_id and not trainer_name:
        return None

    water_state = get_water_state()

    pokemon_name = None
    form = None
    rarity = None
    valid_fish = False

    if embed.description:
        for match in NAME_PATTERN.finditer(embed.description):
            candidate_form_raw = match.group(1)
            candidate_name = match.group(2).lower()
            candidate_form = candidate_form_raw.lower() if candidate_form_raw else None

            for r, pokes in FISH_RARITY.items():
                if candidate_name in pokes:
                    pokemon_name = candidate_name
                    form = candidate_form
                    rarity = r
                    valid_fish = True
                    break
            if valid_fish:
                break

    if not valid_fish:
        return None
    debug_log(
        f"Parsed fishing spawn: Trainer ID={trainer_id}, Trainer Name={trainer_name}, Pokemon={pokemon_name}, Form={form}, Rarity={rarity}, Water State={water_state}",
    )
    return {
        "type": "fishing",
        "pokemon": pokemon_name,
        "form": form,
        "rarity": rarity,
        "valid_fish": valid_fish,
        "water_state": water_state,
        "user_id": trainer_id,
        "trainer_name": trainer_name,
        "raw_footer": embed.footer.text if embed.footer else "",
    }


async def recommend_fishing_ball(message: discord.Message, bot):
    # --- Parse spawn info using dedicated parser ---
    debug_log(f"recommend_fishing_ball called for message {message.id}")

    if message.id in processed_fishing_messages:
        debug_log(f"Already processed message {message.id}, skipping.")
        return None
    processed_fishing_messages.add(message.id)

    spawn_info = parse_pokemeow_fishing_spawn(message)
    if not spawn_info:
        debug_log(f"No valid spawn info in message {message.id}")
        return None

    trainer_id = spawn_info["user_id"]
    trainer_name = spawn_info["trainer_name"]
    water_state = spawn_info["water_state"]
    pokemon_name = spawn_info["pokemon"]
    form = spawn_info["form"]
    rarity = spawn_info["rarity"]
    embed_desc = message.embeds[0].description or ""
    display_pokemon_name = pokemon_name.title()
    debug_log(f"Parsed spawn info: {spawn_info}")
    debug_log(f"Current cache keys: {list(ball_reco_cache.keys())}")

    # --- Lookup user in cache ---
    user_settings = None
    if trainer_id:
        raw = ball_reco_cache.get(trainer_id)
        if isinstance(raw, dict):
            user_settings = raw
        elif isinstance(raw, str):
            user_settings = {"user_name": raw, "enabled": True, "catch_rate_bonus": 0}

    if not user_settings and trainer_name:
        for uid, raw in ball_reco_cache.items():
            uname = raw if isinstance(raw, str) else raw.get("user_name", "")
            if uname.strip().lower() == trainer_name.strip().lower():
                user_settings = (
                    {"user_name": raw, "enabled": True, "catch_rate_bonus": 0}
                    if isinstance(raw, str)
                    else raw
                )
                trainer_id = uid
                break

    # --- Check if user is enabled ---
    enabled_val = user_settings.get("enabled", True) if user_settings else True
    is_enabled = (
        enabled_val.strip().lower() in ("true", "yes", "1", "on")
        if isinstance(enabled_val, str)
        else bool(enabled_val)
    )

    if not user_settings or not is_enabled:
        debug_log(
            f"User {trainer_name or trainer_id} is_enabled: {is_enabled} | In Cache: {bool(user_settings)}"
        )
        return None

    # Ignore caught messages
    if "You caught a" in embed_desc:
        debug_log(f"Ignored caught message {message.id}")
        return None

    # --- Determine if channel has boost ---
    channel_boost = message.channel.id in boosted_channels_cache

    # --- Update water state if message contains cast info ---
    water_state = get_water_state()
    debug_log(f"Using cached water state: {water_state}")

    # --- Calculate best ball ---
    try:
        is_patreon = bool(user_settings.get("is_patreon", False))
        display_mode = user_settings.get("fishing", {}).get("display_mode", "Best Ball")
        display_all = display_mode.strip().lower() == "all balls"

        ball, rate, all_rates, all_balls_str = best_ball_fishing(
            rarity=rarity,
            state=water_state,
            is_patreon=is_patreon,
            form=form.lower() if form else None,
            channel_boost=channel_boost,
            display_all=display_all,
        )

        # --- Build display ---
        rarity_label = (
            f"{form.capitalize()} {rarity.capitalize()}"
            if form
            else rarity.capitalize()
        )
        rarity_emoji = rarity_emojis.get(rarity_label.lower(), "")

        if display_all and all_balls_str:
            msg = (
                f"**{user_settings['user_name']}** 🎣 {rarity_emoji} → {all_balls_str}"
            )
        else:
            ball_emoji = ball_emojis.get(ball, "")
            msg = f"**{user_settings['user_name']}** 🎣 {rarity_emoji} → {ball_emoji} ({rate}%)"

        await message.channel.send(msg)
        debug_log(f"Sent recommendation: {msg}")

        return {
            "user_name": user_settings["user_name"],
            "rarity": rarity,
            "form": form,
            "spawn_type": "fishing",
            "ball": ball,
            "rate": rate,
            "water_state": water_state,
            "is_patreon": is_patreon,
            "channel_boost": channel_boost,
            "display_mode": display_mode,
        }

    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to recommend fishing ball for user {trainer_name}: {e}",
            label="STRAYMONS",
            bot=bot,
        )
        debug_log(f"Exception occurred: {e}")
        return None
