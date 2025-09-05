import re

import discord

from config.aesthetic import Emojis_Balls
from config.fish_rarity import FISH_RARITY
from utils.listener_func.catch_rate import *
from utils.loggers.pretty_logs import pretty_log

# -------------------- Regex + constants --------------------
HELD_ITEM_PATTERN = re.compile(
    r"(?:<:[^:]+:\d+>\s*)?"  # optional NPC emoji
    r"\*\*.+?\*\*\s*found a wild\s*"
    r"(?P<held><:held_item:\d+>)?\s*"  # optional held item emoji
    r"(?:<:[^:]+:\d+>\s*)+"  # Pokemon emoji (+ optional dexCaught)
    r"\*\*(?P<pokemon>[A-Za-z_]+)\*\*"
)

FISHING_COLOR = 0x87CEFA  # sky blue

embed_rarity_color = {
    "common": 546299,
    "uncommon": 1291495,
    "rare": 16484616,
    "superrare": 16315399,
    "legendary": 10487800,
    "shiny": 16751052,
    "golden": 14940164,
}


# -------------------- Parser --------------------
def parse_pokemeow_spawn(message: discord.Message):
    """Parses a PokeMeow spawn embed and returns dict with rarity/type, trainer_id, and water_state for fishing."""

    try:
        # --- Ignore "robot return" messages by content ---
        if (
            message.content
            and "i have returned with some pokemon for you!" in message.content.lower()
        ):
            return None

        if not message.embeds:
            return None
        embed = message.embeds[0]

        # --- Ignore captcha messages ---
        title_text = embed.title or ""
        description_text = embed.description or ""
        if "captcha" in title_text.lower() or "captcha" in description_text.lower():
            return None

        # --- Ignore Research Lab messages ---
        if embed.author and getattr(embed.author, "name", None):
            if "pokemeow research lab" in embed.author.name.lower():
                return None

        footer_text = embed.footer.text if embed.footer else None

        # -------------------- Rarity by color --------------------
        rarity = None
        if embed.color:
            for r, c in embed_rarity_color.items():
                if embed.color.value == c:
                    rarity = r
                    break

        # Special case: Shiny embeds
        if rarity == "shiny" and footer_text:
            footer_lower = footer_text.lower()
            if "full-odds" in footer_lower:
                rarity = "full_odds_shiny_0"
            elif "event" in footer_lower:
                rarity = "event_shiny_0"

        # --- get trainer id from reply ---
        trainer_id = None
        if message.reference and getattr(message.reference, "resolved", None):
            trainer_obj = getattr(message.reference.resolved, "author", None)
            trainer_id = trainer_obj.id if trainer_obj else None

        # --- Fishing ---
        water_state = None
        if embed.color and embed.color.value == FISHING_COLOR:
            state_match = re.search(r"Water state:\s*([-\d]+)", footer_text or "")
            if state_match:
                water_state = int(state_match.group(1))
            spawn_type = "fishing"
        else:
            spawn_type = "pokemon"

        # --- Held item ---
        held_pokemon = None
        if embed.description:
            held_match = HELD_ITEM_PATTERN.search(embed.description)
            if held_match and held_match.group("held"):
                held_pokemon = held_match.group("pokemon")
                spawn_type = "held_item"

        return {
            "type": spawn_type,
            "pokemon": held_pokemon,
            "rarity": rarity,
            "raw_footer": footer_text,
            "user_id": trainer_id,
            "water_state": water_state,
        }
    except Exception as e:
        pretty_log("error", f"Failed to parse spawn: {e}")
        return None


# -------------------- Recommender --------------------
async def recommend_ball(message: discord.Message, bot):
    from utils.cache.ball_reco_cache import ball_reco_cache

    try:
        if not message.embeds:
            return None

        spawn_info = parse_pokemeow_spawn(message)
        if not spawn_info:
            return None

        user_id = spawn_info["user_id"]

        # --- EARLY EXIT: user not in cache or disabled ---
        if not user_id or user_id not in ball_reco_cache:
            return None

        user_settings = ball_reco_cache[user_id]
        enabled_val = user_settings.get("enabled", False)

        if isinstance(enabled_val, str):
            is_enabled = enabled_val.strip().lower() in ("true", "yes", "1", "on")
        else:
            is_enabled = bool(enabled_val)

        if not is_enabled:
            return None

        # --- Masterball bypass ---
        embed = message.embeds[0]
        if embed.color and embed.color.value == 15345163:
            user_name = user_settings.get("user_name")
            rarity = spawn_info.get("rarity")  # can be None

            ball = "masterball"
            rate = 100

            # ✅ Safely get emojis
            rarity_emoji = rarity_emojis.get(rarity.lower(), "") if rarity else ""
            ball_emoji = ball_emojis.get("masterball")

            msg = f"{user_name} {Emojis_Balls.small_pokeball} {rarity_emoji} __Event Exclusive__ → {ball_emoji} ({rate}%)"
            await message.channel.send(msg)

            return {
                "user_id": user_id,
                "user_name": user_name,
                "rarity": rarity,
                "spawn_type": "special_masterball",
                "ball": ball,
                "rate": rate,
            }

        spawn_type = spawn_info.get("type")
        rarity = spawn_info.get("rarity")  # can be None

        # --- Determine category and rarity key map ---
        if spawn_type == "pokemon":
            enabled = user_settings["pokemon"].get(rarity, False) if rarity else False
            category = (
                "patron_gen_1_8"
                if user_settings.get("is_patreon", False)
                else "non_patron_gen_1_8"
            )
            rarity_key_map = {
                "common": "common_70",
                "uncommon": "uncommon_60",
                "rare": "rare_37",
                "superrare": "super_rare_20",
                "legendary": "legendary_5",
                "shiny": "full_odds_shiny_64",
                "golden": "event_shiny_0",
            }
        elif spawn_type == "held_item":
            enabled = (
                user_settings["held_items"].get(rarity, False) if rarity else False
            )
            category = "held_item_pokemon"
            rarity_key_map = {
                "common": "common_25",
                "uncommon": "uncommon_20",
                "rare": "rare_15",
                "superrare": "super_rare_10",
                "legendary": "legendary_0",
                "shiny": "full_odds_shiny_0",
                "golden": "event_shiny_0",
            }
        else:
            return None

        if not enabled or not rarity or rarity not in rarity_key_map:
            return None

        rarity_key = rarity_key_map[rarity]
        boost = int(user_settings.get("catch_rate_bonus", 0))
        is_patreon = user_settings.get("is_patreon", False)

        ball, rate, all_rates = best_ball(
            category, rarity_key, boost=boost, is_patreon=False
        )

        # --- Build recommendation message ---
        rarity_emoji = rarity_emojis.get(rarity.lower(), "") if rarity else ""
        ball_emoji = ball_emojis.get(ball.lower(), "") if ball else ""
        user_name = user_settings["user_name"]

        msg = f"{user_name} {Emojis_Balls.small_pokeball} {rarity_emoji} → {ball_emoji} ({rate}%)"
        await message.channel.send(msg)

        return {
            "user_id": user_id,
            "user_name": user_name,
            "rarity": rarity,
            "spawn_type": spawn_type,
            "ball": ball,
            "rate": rate,
        }

    except Exception as e:
        pretty_log("error", f"Error in recommend_ball: {e}")
        return None
