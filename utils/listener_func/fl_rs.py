import re

import discord
from discord.ext import commands

from config.straymons_constants import STRAYMONS__EMOJIS, STRAYMONS__TEXT_CHANNELS
from utils.embeds.design_embed import design_embed
from utils.essentials.pokemeow_helpers import get_pokemeow_reply_member
from utils.loggers.pretty_logs import pretty_log

rarity_meta = {
    "common": {"color": 810198, "emoji": STRAYMONS__EMOJIS.common},
    "uncommon": {"color": 1291495, "emoji": STRAYMONS__EMOJIS.uncommon},
    "rare": {"color": 16550924, "emoji": STRAYMONS__EMOJIS.rare},
    "superrare": {"color": 16571396, "emoji": STRAYMONS__EMOJIS.superrare},
    "legendary": {"color": 10487800, "emoji": STRAYMONS__EMOJIS.legendary},
    "shiny": {"color": 16751052, "emoji": STRAYMONS__EMOJIS.shiny},
    "golden": {"color": 14940164, "emoji": STRAYMONS__EMOJIS.golden11},
    "event_exclusive": {"color": 15345163},
    "default": {"color": 0xA0D8F0},
}

shiny_color = rarity_meta.get("shiny")["color"]
legendary_color = rarity_meta.get("legendary")["color"]
event_exclusive_color = rarity_meta.get("event_exclusive")["color"]

RARE_COLORS = {shiny_color, legendary_color, event_exclusive_color}


# ❀─────────────────────────────────────────❀
#      💖  Extract Rarity from Footer
# ❀─────────────────────────────────────────❀
def extract_rarity_from_footer(footer_text: str) -> str:
    # Extract rarity from embed footer
    rarity_match = re.search(r"Rarity:\s*([A-Za-z]+)", footer_text)
    if rarity_match:
        rarity = rarity_match.group(1).strip().lower().replace(" ", "")
        return rarity
    else:
        return None


# 🐾────────────────────────────────────────────
#     ✨ Feeling Lucky Rare Pokémon Checker
# 🐾────────────────────────────────────────────
async def fl_rs_checker(bot: discord.Client, message: discord.Message):
    if not message.embeds:
        return

    embed = message.embeds[0]
    embed_color = embed.color
    if embed.color and embed.color.value not in RARE_COLORS:
        pretty_log(
            tag="info",
            message="Feeling Lucky spawn is not rare. Exiting FL RS Checker.",
            label="🍀 FL RS CHECKER",
            bot=bot,
        )
        return

    member = await get_pokemeow_reply_member(message=message)
    if not member:
        return

    # Extract Pokémon name
    pokemon_name = None
    if embed.description:
        catch_match = re.search(r"You caught a.*?\*\*([^*]+)\*\*", embed.description)
        if catch_match:
            pokemon_name = catch_match.group(1).strip()

    if embed.color.value == legendary_color:
        rarity = "legendary"
    elif embed.color.value == shiny_color:
        rarity = "shiny"
        pokemon_name = pokemon_name.replace("Shiny ", "")
    elif embed.color.value == event_exclusive_color:
        # Extract rarity from footer for event exclusive
        if embed.footer and embed.footer.text:
            rarity = extract_rarity_from_footer(embed.footer.text)
            if rarity.lower() == "super rare":
                rarity = "superrare"
        else:
            rarity = "event_exclusive"

    image_url = embed.image.url if embed.image else None

    emoji = rarity_meta.get(rarity, rarity_meta["default"])["emoji"]
    display_pokemon_name = f"{emoji} {pokemon_name.title()}"

    desc = (
        f"[Jump to Message]({message.jump_url})"
        f"Member: {member.mention}\n"
        f"Pokemon: {display_pokemon_name}\n"
    )

    log_embed = discord.Embed(
        title="Feeling Lucky Rare Spawn", description=desc, color=embed_color
    )
    log_embed = design_embed(
        user=member, embed=log_embed, thumbnail_url=image_url if image_url else None
    )
    log_embed.color = message.embeds[0].color

    report_channel = message.guild.get_channel(STRAYMONS__TEXT_CHANNELS.reports)
    if report_channel:
        await report_channel.send(embed=log_embed)

    pretty_log(
        tag="info",
        message=f"Detected rare Pokémon: {pokemon_name}",
        label="🍀 FL RS CHECKER",
        bot=bot,
    )
