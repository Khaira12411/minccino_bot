import re

import discord

from config.aesthetic import Emojis_Balls
from config.fish_rarity import FISH_RARITY
from utils.cache.boosted_channels_cache import boosted_channels_cache
from utils.cache.daily_fa_ball_cache import daily_faction_ball_cache
from utils.cache.faction_ball_alert_cache import faction_ball_alert_cache
from utils.cache.straymon_member_cache import straymon_member_cache
from utils.cache.water_state_cache import get_water_state, update_water_state
from utils.essentials.pokemeow_helpers import get_pokemeow_reply_member
from utils.listener_func.catch_rate import *
from utils.loggers.debug_log import debug_log, enable_debug
from utils.loggers.pretty_logs import pretty_log

# -------------------- Regex + constants --------------------
HELD_ITEM_PATTERN = re.compile(
    r"(?:<:[^:]+:\d+>\s*)?"  # optional NPC emoji
    r"\*\*.+?\*\*\s*found a wild\s*"
    r"(?P<held><:held_item:\d+>)?\s*"  # optional held item emoji
    r"(?:<:[^:]+:\d+>\s*)+"  # Pokemon emoji (+ optional dexCaught)
    r"\*\*(?P<pokemon>[A-Za-z_]+)\*\*"
)
# enable_debug(f"{__name__}.extract_water_state_from_author")
# enable_debug(f"{__name__}.parse_pokemeow_spawn")
FISHING_COLOR = 0x87CEFA  # sky blue
HALLOWEEN_COLOR = 0xFFA500  # orange
EVENT_EXCL_COLOR = 0xEA260B  # red
embed_rarity_color = {
    "common": 546299,
    "uncommon": 1291495,
    "rare": 16484616,
    "superrare": 16315399,
    "legendary": 10487800,
    "shiny": 16751052,
    "golden": 14940164,
}


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

        # -------------------- CHECKING WATER STATE --------------------
        water_state = None
        if embed.color and embed.color.value == FISHING_COLOR:
            if "cast a " in description_text.lower():
                author_text = embed.author.name if embed.author else ""
                debug_log(f"Author text for cast detection: '{author_text}'")

                current_state = extract_water_state_from_author(author_text)
                debug_log(f"Detected cast: {current_state}")

                if current_state:
                    water_state = current_state.lower()

                    # ✅ Only update if different from cached state
                    cached_state = get_water_state()
                    if cached_state != water_state:
                        update_water_state(new_state=water_state)
                        debug_log(
                            f"Water state successfully updated to: {water_state}",
                            highlight=True,
                        )
                    else:
                        debug_log(
                            f"Water state unchanged ({water_state}), no update performed"
                        )
                else:
                    debug_log(
                        "No valid water state detected from author text, update skipped",
                        highlight=True,
                    )
            else:
                debug_log(
                    "No 'cast a ' found in embed description, skipping water state update"
                )
            return

        # -------------------- MUST BE A SPAWN --------------------
        if description_text and "found a wild" not in description_text.lower():
            return None

        # --- Ignore Research Lab messages ---
        if embed.author and getattr(embed.author, "name", None):
            if "pokemeow research lab" in embed.author.name.lower():
                return None

        footer_text = embed.footer.text if embed.footer else None

        # -------------------- Rarity by color --------------------
        rarity = None
        if embed.color and embed.color.value != HALLOWEEN_COLOR:
            # pretty_log("debug", f"Embed color value: {embed.color.value}")
            for r, c in embed_rarity_color.items():
                if embed.color.value == c:
                    rarity = r
                    break

        # --- Fallback: parse rarity from footer if color not recognized ---
        elif (
            not rarity
            and footer_text
            or (embed.color and embed.color.value == HALLOWEEN_COLOR)
            or (embed.color and embed.color.value == EVENT_EXCL_COLOR)
        ):
            pretty_log(
                "debug",
                f"Using footer text for rarity parsing, embed color: {embed.color.value if embed.color else 'None'}, footer_text: {footer_text!r}",
            )
            match = re.match(r"([A-Za-z ]+)", footer_text)
            if match:
                rarity = match.group(1).strip().lower().replace(" ", "")
                pretty_log("debug", f"Parsed rarity from footer: {rarity}")
            else:
                pretty_log(
                    "debug",
                    f"Rarity regex did not match. Footer text: {footer_text!r}"
                )

        # Special case: Shiny embeds
        if rarity == "shiny" and footer_text:
            footer_lower = footer_text.lower()
            if "full-odds" in footer_lower:
                rarity = "full_odds"
            elif "event" in footer_lower:
                rarity = "shiny"
            pretty_log("debug", f"Refined shiny rarity to: {rarity}")

        # --- get trainer id from reply ---
        trainer_id = None
        if message.reference and getattr(message.reference, "resolved", None):
            trainer_obj = getattr(message.reference.resolved, "author", None)
            trainer_id = trainer_obj.id if trainer_obj else None

        # --- Spawn type ---
        spawn_type = (
            "fishing"
            if embed.color and embed.color.value == FISHING_COLOR
            else "pokemon"
        )

        # --- Held item ---
        # --- Held item ---
        held_pokemon = None
        if description_text:
            # Simple check: if held item emoji is in description, it's a held item spawn
            if "<:held_item:" in description_text:
                spawn_type = "held_item"
                # You can still extract the pokemon name if needed with a simpler regex
                pokemon_match = re.search(r"\*\*([A-Za-z_]+)\*\*", description_text)
                if pokemon_match:
                    held_pokemon = pokemon_match.group(1)

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
        embed = message.embeds[0]
        embed_footer_text = embed.footer.text if embed.footer else ""
        if "PokeMeow | Egg Hatch" in embed_footer_text:
            return None  # 🚪 early exit for egg hatches

        user_id = None
        member = await get_pokemeow_reply_member(message)
        if member:
            user_id = member.id
            if user_id not in ball_reco_cache:
                return  # Exit Early if not in cache

        spawn_info = parse_pokemeow_spawn(message)
        if not spawn_info:
            return None

        user_id = spawn_info["user_id"]

        display_pokemon = (
            spawn_info.get("pokemon").title()
            if spawn_info.get("pokemon")
            else "This Pokemon"
        )

        # --- EARLY EXIT: user not in cache or disabled ---
        if not user_id or user_id not in ball_reco_cache:
            return None

        user_settings = ball_reco_cache[user_id]
        user_name = user_settings.get("user_name")
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

        spawn_info = parse_pokemeow_spawn(message)
        if not spawn_info:
            return None

        if spawn_info.get("type") == "fishing":
            return None  # 🚪 hard exit for fishing spawns

        # --- Determine category and rarity key map ---
        if spawn_type == "pokemon":
            enabled = user_settings["pokemon"].get(rarity, False) if rarity else False
            category = "non_patron_gen_1_8"
            rarity_key_map = {
                "common": "common_70",
                "uncommon": "uncommon_60",
                "rare": "rare_37",
                "superrare": "super_rare_20",
                "legendary": "legendary_5",
                "shiny": "event_shiny_0",
                "full_odds": "full_odds_shiny_64",
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
                "shiny": "event_shiny_0",
                "full_odds": "full_odds_shiny_0",
            }
        else:
            return None

        if not enabled or not rarity or rarity not in rarity_key_map:
            return None

        # --- Determine if channel has boost ---
        channel_boost = False
        if message.channel.id in boosted_channels_cache:
            channel_boost = True  # % boost from PokéMeow

        rarity_key = rarity_key_map[rarity]
        boost = int(user_settings.get("catch_rate_bonus", 0))
        is_patreon = user_settings.get("is_patreon", False)

        # --- Get display mode based on spawn type ---
        if spawn_type == "pokemon":
            display_mode = user_settings.get("pokemon", {}).get(
                "display_mode", "Best Ball"
            )
        elif spawn_type == "held_item":
            display_mode = user_settings.get("held_items", {}).get(
                "display_mode", "Best Ball"
            )
        else:
            display_mode = "Best Ball"

        # ✅ Normalize to allowed values only
        if isinstance(display_mode, str):
            display_mode = display_mode.strip().title()
        else:
            display_mode = "Best Ball"

        if display_mode not in ("Best Ball", "All Balls"):
            display_mode = "Best Ball"

        display_all = display_mode == "All Balls"

        ball, rate, all_rates, all_balls_str = best_ball(
            category,
            rarity_key,
            boost=boost,
            is_patreon=is_patreon,
            channel_boost=channel_boost,
            display_all=display_all,  # <-- pass display preference
        )

        # --- Build recommendation message ---
        rarity_emoji = rarity_emojis.get(rarity.lower(), "") if rarity else ""
        ball_emoji = ball_emojis.get(ball.lower(), "") if ball else ""
        user_name = user_settings["user_name"]
        # {Emojis.held_item}
        if spawn_type == "held_item":
            if display_all and all_balls_str:
                msg = f"{user_name} {Emojis.held_item} {Emojis_Balls.small_pokeball} {rarity_emoji} → {all_balls_str}"
            else:
                msg = f"{user_name} {Emojis.held_item} {Emojis_Balls.small_pokeball} {rarity_emoji} → {ball_emoji} ({rate}%)"
        else:
            if display_all and all_balls_str:
                msg = f"{user_name} {Emojis_Balls.small_pokeball} {rarity_emoji} → {all_balls_str}"
            else:
                msg = f"{user_name} {Emojis_Balls.small_pokeball} {rarity_emoji} → {ball_emoji} ({rate}%)"

        await message.channel.send(msg)

        return {
            "user_id": user_id,
            "user_name": user_name,
            "rarity": rarity,
            "spawn_type": spawn_type,
            "ball": ball,
            "rate": rate,
            "display_mode": display_mode,
        }

    except Exception as e:
        pretty_log("error", f"Error in recommend_ball: {e}")
        return None
