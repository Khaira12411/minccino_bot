from datetime import datetime
from zoneinfo import ZoneInfo

from config.aesthetic import Emojis
from config.held_items import HELD_ITEMS_DICT

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
    subscribed_items = user_sub.get("subscribed_items", set())
    all_items_flag = user_sub.get("all_held_items", False)
    moonball_subbed = user_sub.get("moonball", False)
    duskball_subbed = user_sub.get("duskball", False)

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
        special_balls.append(f"{Emojis.moonball} **__Moonball__**")
        if duskball_subbed:
            special_balls.append(f"{Emojis.duskball} **__Duskball__**")
    elif is_nighttime_est() and duskball_subbed:
        special_balls.append(f"{Emojis.duskball} **__Duskball__**")

    # No held items
    if not items_for_pokemon:
        if special_balls:
            balls_str = " ".join(special_balls)
            return f"{proper_pokemon_name} is holding an {held_item_phrase} (Special Item Chance: {balls_str})"
        else:
            return f"{proper_pokemon_name} is holding an {held_item_phrase}"

    # Held items
    items_to_show = []
    for item in items_for_pokemon:
        if all_items_flag or item in subscribed_items:
            emoji = HELD_ITEMS_DICT[item]["emoji"]
            items_to_show.append(f"{emoji} **__{pretty_item_name(item)}__**")
    items_to_show.extend(special_balls)

    if not items_to_show:
        return None

    if len(items_to_show) == 1:
        return f"{proper_pokemon_name} is holding an {held_item_phrase} (Special Item Chance: {items_to_show[0]})"
    else:
        items_str = " or ".join(items_to_show)
        return f"{proper_pokemon_name} is holding an {held_item_phrase} (Special Item Chance: {items_str})"
