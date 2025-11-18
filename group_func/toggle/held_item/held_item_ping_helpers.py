from datetime import datetime
from zoneinfo import ZoneInfo

from config.aesthetic import Emojis
from config.held_items import HELD_ITEMS_DICT
from utils.loggers.debug_log import debug_log, enable_debug

enable_debug(f"{__name__}.held_item_message")
# ─────────────────────────────
#  💎 Pretty names for items
# ─────────────────────────────
PRETTY_ITEM_NAMES = {
    "assaultvest": "Assault Vest",
    "blackbelt": "Black Belt",
    "blackglasses": "Black Glasses",
    "charcoal": "Charcoal",
    "dragonfang": "Dragon Fang",
    "electrizer": "Electrizer",
    "magmarizer": "Magmarizer",
    "kingsrock": "King's Rock",
    "dragonscale": "Dragon Scale",
    "fairyfeather": "Fairy Feather",
    "focusband": "Focus Band",
    "luckyegg": "Lucky Egg",
    "magnet": "Magnet",
    "hardstone": "Hard Stone",
    "metalcoat": "Metal Coat",
    "miracleseed": "Miracle Seed",
    "mysticwater": "Mystic Water",
    "nevermeltice": "Nevermeltice",
    "poisonbarb": "Poison Barb",
    "razorclaw": "Razor Claw",
    "razorfang": "Razor Fang",
    "sharpbeak": "Sharp Beak",
    "silkscarf": "Silk Scarf",
    "silverpowder": "Silver Powder",
    "softsand": "Soft Sand",
    "spelltag": "Spell Tag",
    "twistedspoon": "Twisted Spoon",
}


def pretty_item_name(item: str) -> str:
    """Return the properly formatted item name."""
    return PRETTY_ITEM_NAMES.get(item.lower(), item.title())


def is_midnight_est():
    """
    Returns True if the current time in America/New_York is between 12:00 AM and 12:59 AM.
    """
    nyc = ZoneInfo("America/New_York")
    now_nyc = datetime.now(nyc)
    return now_nyc.hour == 0


def is_nighttime_est():
    """
    Returns True if the current time in America/New_York is between 7:00 PM and 6:59 AM.
    """
    nyc = ZoneInfo("America/New_York")
    now_nyc = datetime.now(nyc)
    return now_nyc.hour >= 19 or now_nyc.hour < 7


# ─────────────────────────────
#  💎 Held Item Message
# ─────────────────────────────
def held_item_message(pokemon_name: str, user_sub: dict) -> str | None:
    """
    Generate a compact message for a Pokemon with held items.

    user_sub example:
        {
            "all_held_items": True,
            "subscribed_items": {"hardstone", "assaultvest", ...},
            "moonball": True,
            "duskball": True
        }
    """
    debug_log(f"held_item_message called for {pokemon_name} with user_sub: {user_sub}")
    subscribed_items = user_sub.get("subscribed_items", set())
    all_items_flag = user_sub.get("all_held_items", False)
    moonball_subbed = "moonball" in subscribed_items
    debug_log(f"User Moonball subscribed: {moonball_subbed}")
    duskball_subbed = "duskball" in subscribed_items
    debug_log(f"User Duskball subscribed: {duskball_subbed}")
    nyc = ZoneInfo("America/New_York")
    now_nyc = datetime.now(nyc)
    debug_log(f"Current time in EST: {now_nyc.strftime('%Y-%m-%d %H:%M:%S')} ")

    held_item_phrase = f"{Emojis.held_item} item! "

    items_for_pokemon = [
        item
        for item, data in HELD_ITEMS_DICT.items()
        if pokemon_name.lower() in data["pokemon"]
    ]
    proper_pokemon_name = pokemon_name.title()

    # Special balls to show
    special_balls = []
    if is_midnight_est() and moonball_subbed:
        debug_log(f"Midnight EST detected for {proper_pokemon_name}")
        special_balls.append(f"{Emojis.moonball} **__Moonball__**")
        debug_log(f"Added Moonball for {proper_pokemon_name}")
        if duskball_subbed:
            special_balls.append(f"{Emojis.duskball} **__Duskball__**")
            debug_log(f"Added Duskball for {proper_pokemon_name}")
    elif is_nighttime_est() and duskball_subbed:
        debug_log(f"Nighttime EST detected for {proper_pokemon_name}")
        special_balls.append(f"{Emojis.duskball} **__Duskball__**")
        debug_log(f"Added Duskball for {proper_pokemon_name}")
    else:
        debug_log(f"No special balls added for {proper_pokemon_name}")

    # No held items
    if not items_for_pokemon:
        debug_log(f"No held items for {proper_pokemon_name}")
        if special_balls:
            balls_str = " ".join(special_balls)
            debug_log(f"Special balls for {proper_pokemon_name}: {balls_str}")
            return f"{proper_pokemon_name} is holding an {held_item_phrase} (Special Item Chance: {balls_str})"
        else:
            debug_log(f"No special balls for {proper_pokemon_name}")
            return f"{proper_pokemon_name} is holding an {held_item_phrase}"

    # Held items
    items_to_show = []
    for item in items_for_pokemon:
        if all_items_flag or item in subscribed_items:
            emoji = HELD_ITEMS_DICT[item]["emoji"]
            items_to_show.append(f"{emoji} **__{pretty_item_name(item)}__**")
    items_to_show.extend(special_balls)

    if not items_to_show:
        debug_log(f"No subscribed held items for {proper_pokemon_name}")
        return None

    if len(items_to_show) == 1:
        debug_log(f"One held item for {proper_pokemon_name}: {items_to_show[0]}")
        return f"{proper_pokemon_name} is holding an {held_item_phrase} (Special Item Chance: {items_to_show[0]})"
    else:
        items_str = " or ".join(items_to_show)
        debug_log(f"Multiple held items for {proper_pokemon_name}: {items_str}")
        return f"{proper_pokemon_name} is holding an {held_item_phrase} (Special Item Chance: {items_str})"
