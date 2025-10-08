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


# ─────────────────────────────
#  💎 Held Item Message
# ─────────────────────────────
def held_item_message(pokemon_name: str, user_sub: dict) -> str | None:
    """
    Generate a compact message for a Pokemon with held items.

    user_sub example:
        {
            "all_held_items": True,
            "subscribed_items": {"hardstone", "assaultvest", ...}
        }
    """
    held_item_phrase = f"{Emojis.held_item} item! "

    items_for_pokemon = [
        item
        for item, data in HELD_ITEMS_DICT.items()
        if pokemon_name.lower() in data["pokemon"]
    ]
    proper_pokemon_name = pokemon_name.title()

    if not items_for_pokemon:
        return f"{proper_pokemon_name} is holding an {held_item_phrase}"

    subscribed_items = user_sub.get("subscribed_items", set())
    all_items_flag = user_sub.get("all_held_items", False)

    items_to_show = []
    for item in items_for_pokemon:
        if all_items_flag or item in subscribed_items:
            emoji = HELD_ITEMS_DICT[item]["emoji"]
            items_to_show.append(f"{emoji} **__{pretty_item_name(item)}__**")

    if not items_to_show:
        return None

    if len(items_to_show) == 1:
        return f"{proper_pokemon_name} is holding an {held_item_phrase} (Special Item Chance: {items_to_show[0]})"
    else:
        items_str = " or ".join(items_to_show)
        return f"{proper_pokemon_name} is holding an {held_item_phrase} (Special Item Chance: {items_str})"
