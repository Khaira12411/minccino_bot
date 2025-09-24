# inside get_pokemon_gif.py
from typing import Literal
from config.pokemon_gifs import *


async def get_pokemon_gif(input_name: str):
    """
    Returns the pokemon gif
    """
    original_input = input_name
    shiny = False
    golden = False
    form: Literal["regular", "mega", "gmax"] = "regular"
    region_suffix = ""

    # Normalize input
    name_parts = input_name.lower().replace("_", "-").split()

    if "golden" in name_parts:
        golden = True
        name_parts.remove("golden")
    if "shiny" in name_parts:
        shiny = True
        name_parts.remove("shiny")

    remaining_name = "-".join(name_parts)

    regions = {"alolan": "-alola", "galarian": "-galar", "hisuian": "-hisui"}
    for region_prefix, suffix in regions.items():
        if remaining_name.startswith(region_prefix + "-"):
            region_suffix = suffix
            remaining_name = remaining_name[len(region_prefix) + 1 :]
            break

    if remaining_name.startswith("mega-"):
        form = "mega"
        remaining_name = remaining_name.replace("mega-", "")
    elif remaining_name.startswith(("gigantamax-", "gmax-")):
        form = "gmax"
        remaining_name = remaining_name.replace("gigantamax-", "").replace("gmax-", "")

    # 🔹 Special gmax aliases
    gmax_aliases = {
        "urshifu-rapidstrike": "urs",
        "urshifu-singlestrike": "uss",
        "eternamax-eternatus": "eternatus",
    }
    if form == "gmax" and remaining_name in gmax_aliases:
        remaining_name = gmax_aliases[remaining_name]

    base_name = f"{remaining_name}{region_suffix}".lower()
    attr_name = remaining_name.replace("-", "_")

    gif_url = None
    gif_name = None

    if golden:
        if form == "mega":
            golden_attr_name = f"mega_{attr_name}"
            gif_url = getattr(GOLDEN_MEGA_POKEMON_URL, golden_attr_name, None)
        elif form == "gmax":
            gif_url = getattr(GOLDEN_POKEMON_URL, f"gmax_{attr_name}", None)
        else:
            gif_url = getattr(GOLDEN_POKEMON_URL, attr_name, None)

    if not gif_url:
        if form == "gmax":
            gif_url = getattr(
                SHINY_GMAX_URL if shiny else REGULAR_GMAX_URL, attr_name, None
            )
        else:
            gif_url = getattr(REGULAR_POKEMON_URL, attr_name, None)

    if not gif_url:
        shiny_prefix = "ani-shiny" if shiny else "xyani"
        suffix = "" if form == "regular" else f"-{form}"
        gif_url = f"https://play.pokemonshowdown.com/sprites/{shiny_prefix}/{base_name}{suffix}.gif?quality=lossless"

    gif_name = f"{'golden ' if golden else ''}{'shiny ' if shiny else ''}{form + ' ' if form != 'regular' else ''}{remaining_name}"

    error = None
    if not gif_url:
        error = f"Cannot find Pokémon GIF for '{original_input}'"

    return gif_url
