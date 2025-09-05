import re

import discord

from config.fish_rarity import FISH_RARITY
from utils.listener_func.catch_rate import *
DEBUG = False
FISHING_COLOR = 0x87CEFA  # sky blue

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
        return "special"
    elif "calm" in name_lower:
        return "calm"
    elif "strong" in name_lower:
        return "strong"
    elif "moderate" in name_lower:
        return "moderate"
    elif "intense" in name_lower:
        return "intense"
    return None


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


import inspect

import discord

from config.fish_rarity import FISH_RARITY
from utils.cache.ball_reco_cache import ball_reco_cache
from utils.cache.water_state_cache import get_water_state, update_water_state
from utils.listener_func.catch_rate import ball_emojis, best_ball_fishing, rarity_emojis
from utils.loggers.debug_log import debug_log
from utils.loggers.pretty_logs import pretty_log


async def recommend_fishing_ball(message: discord.Message, bot):
    func_name = inspect.currentframe().f_code.co_name

    # --- Parse spawn info using dedicated parser ---
    spawn_info = parse_pokemeow_fishing_spawn(message)
    if not spawn_info:
        await debug_log(func_name, f"No valid spawn info in message {message.id}")
        return None

    trainer_id = spawn_info["user_id"]
    trainer_name = spawn_info["trainer_name"]
    water_state = spawn_info["water_state"]
    pokemon_name = spawn_info["pokemon"]
    form = spawn_info["form"]
    rarity = spawn_info["rarity"]
    embed_desc = message.embeds[0].description or ""

    await debug_log(func_name, f"Parsed spawn info: {spawn_info}")
    await debug_log(func_name, f"Current cache keys: {list(ball_reco_cache.keys())}")

    # --- Lookup user in cache ---
    user_settings = None

    # 1️⃣ Lookup by ID first
    if trainer_id:
        raw = ball_reco_cache.get(trainer_id)
        if isinstance(raw, dict):
            user_settings = raw
        elif isinstance(raw, str):
            user_settings = {"user_name": raw, "enabled": True, "catch_rate_bonus": 0}

    # 2️⃣ Fallback: lookup by user_name
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
    if isinstance(enabled_val, str):
        is_enabled = enabled_val.strip().lower() in ("true", "yes", "1", "on")
    else:
        is_enabled = bool(enabled_val)

    if not user_settings or not is_enabled:
        await debug_log(
            func_name,
            f"User {trainer_name or trainer_id} is_enabled: {is_enabled} | In Cache: {bool(user_settings)}",
        )
        return None

    # --- Update water state if message contains cast info ---
    if "cast a " in embed_desc:
        current_state = extract_water_state_from_author(trainer_name)
        await debug_log(func_name, f"Detected cast: {current_state}")
        if current_state and current_state.lower() != water_state.lower():
            update_water_state(new_state=current_state.lower())
            water_state = current_state.lower()
            await debug_log(func_name, f"Updated water state to: {water_state}")

    # Ignore caught messages
    if "You caught a" in embed_desc:
        await debug_log(func_name, f"Ignored caught message {message.id}")
        return None

    # --- Calculate best ball ---
    try:
        # Determine Patreon status from cache
        is_patreon = bool(user_settings.get("is_patreon", False))

        # 🌊 Print all inputs before computation
        print(f"[DEBUG] Calling best_ball_fishing with:")
        print(f"         rarity = {rarity}")
        print(f"         state = {water_state}")
        print(f"         boost = 0 (ignoring catch_rate_bonus)")
        print(f"         is_patreon = {is_patreon}")
        print(f"         form = {form.lower() if form else None}")

        ball, rate, all_rates = best_ball_fishing(
            rarity=rarity,
            state=water_state,
            is_patreon=is_patreon,
            form=form.lower() if form else None,
        )

        # 🌊 Print all computed rates
        print(f"[DEBUG] Computed rates for all balls:")
        for b, r in all_rates.items():
            print(f"         {b}: {r}%")

        # --- Build display ---
        rarity_display_map = {
            "common": "Common",
            "uncommon": "Uncommon",
            "rare": "Rare",
            "superrare": "Super Rare",
            "legendary": "Legendary",
            "full_odds_shiny_0": "Full Odds Shiny",
            "event_shiny_0": "Event Shiny",
        }
        rarity_label = rarity_display_map.get(rarity, rarity.capitalize())
        if form:
            rarity_label = f"{form.capitalize()} {rarity_label}"

        rarity_label_lower = rarity_label.lower()
        rarity_emoji = rarity_emojis.get(rarity_label_lower, "")
        ball_emoji = ball_emojis.get(ball, "")

        msg = f"{user_settings['user_name']} 🎣 {rarity_emoji} → {ball_emoji} ({rate}%)"
        await message.channel.send(msg)
        await debug_log(func_name, f"Sent recommendation: {msg}")

        return {
            "user_name": user_settings["user_name"],
            "rarity": rarity,
            "form": form,
            "spawn_type": "fishing",
            "ball": ball,
            "rate": rate,
            "water_state": water_state,
            "is_patreon": is_patreon,
        }

    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to recommend fishing ball for user {trainer_name}: {e}",
            label="STRAYMONS",
            bot=bot,
        )
        await debug_log(func_name, f"Exception occurred: {e}")
        return None
