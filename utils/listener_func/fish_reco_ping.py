import re
import discord

from config.fish_rarity import FISH_RARITY
from utils.listener_func.catch_rate import *

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


async def recommend_fishing_ball(message: discord.Message, bot):
    from utils.cache.ball_reco_cache import ball_reco_cache
    from utils.cache.water_state_cache import get_water_state, update_water_state
    from utils.loggers.pretty_logs import pretty_log

    if not message.embeds:
        return None

    embed = message.embeds[0]
    embed_desc = embed.description or ""

    if not embed.color or embed.color.value != FISHING_COLOR:
        return None

    water_state = get_water_state()
    if "cast a " in embed_desc:
        current_state = extract_water_state_from_author(embed.author.name)
        if current_state:
            current_state = current_state.lower()
            if current_state != water_state.lower():
                update_water_state(new_state=current_state)
                water_state = current_state

    if "You caught a" in embed_desc:
        return None

    match = WILD_SPAWN_PATTERN.search(embed_desc)
    if not match:
        return None

    trainer_name = match.group("trainer")
    form = match.group("form")
    pokemon_name = match.group("pokemon").lower()

    rarity = None
    valid_fish = False
    for r, pokes in FISH_RARITY.items():
        if pokemon_name in pokes:
            rarity = r
            valid_fish = True
            break
    if not valid_fish:
        return None

    user_settings = ball_reco_cache.get(
        trainer_name,
        {
            "user_name": trainer_name,
            "catch_rate_bonus": 0,
            "is_patreon": False,
            "enabled": True,
        },
    )

    if not user_settings.get("enabled", True):
        return None

    try:
        ball, rate, all_rates = best_ball_fishing(
            rarity=rarity,
            state=water_state,
            boost=int(user_settings.get("catch_rate_bonus", 0)),
            is_patreon=user_settings.get("is_patreon", False),
            form=form.lower() if form else None,
        )

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

        return {
            "user_name": user_settings["user_name"],
            "rarity": rarity,
            "form": form,
            "spawn_type": "fishing",
            "ball": ball,
            "rate": rate,
            "water_state": water_state,
        }

    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to recommend fishing ball for user {trainer_name}: {e}",
            label="STRAYMONS",
            bot=bot,
        )
        return None
