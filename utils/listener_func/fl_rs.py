import re

import discord
from discord.ext import commands

from config.straymons_constants import STRAYMONS__EMOJIS, STRAYMONS__TEXT_CHANNELS
from utils.essentials.pokemeow_helpers import get_pokemeow_reply_member
from utils.loggers.pretty_logs import pretty_log
from utils.embeds.design_embed import design_embed

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


# 🐾────────────────────────────────────────────
#     ✨ Feeling Lucky Rare Pokémon Checker
# 🐾────────────────────────────────────────────
async def fl_rs_checker(bot: commands.Bot, message: discord.Message):
    if not message.embeds:
        return

    embed = message.embeds[0]
    embed_color = embed.color
    if embed_color not in RARE_COLORS:
        return

    if not embed.description or "You caught a" not in embed.description:
        return

    member = await get_pokemeow_reply_member(message=message)
    if not member:
        return

    # Extract Pokémon name
    pokemon_name = None
    if embed.description:
        match = re.search(r"\*\*(.+?)\*\*", embed.description)
        if match:
            pokemon_name = match.group(1).strip().replace("*", "")
            if pokemon_name.lower().startswith("shiny "):
                pokemon_name = pokemon_name[6:].strip()
            image_url = embed.image.url if embed.image else None

    # Extract rarity
    rarity = None
    if embed.footer and embed.footer.text:
        match_rarity = re.search(r"Rarity:\s*(\w+)", embed.footer.text)
        if match_rarity:
            rarity = match_rarity.group(1).lower()
            if rarity == "super":
                rarity = "superrare"

    emoji = rarity_meta.get(rarity, rarity_meta["default"])["emoji"]
    display_pokemon_name = f"{emoji} {pokemon_name.title()}"

    desc = (
        f"Member: {member.mention}\n"
        f"Pokemon: {display_pokemon_name}\n"
        f"[Jump to Message]({message.jump_url})"
    )

    log_embed = discord.Embed(
        title="Feeling Lucky Rare Spawn", description=desc, color=embed_color
    )
    log_embed = design_embed(user=member, embed=log_embed, thumbnail_url=image_url)
    log_embed.color = embed_color

    report_channel = message.guild.get_channel(STRAYMONS__TEXT_CHANNELS.reports)
    if report_channel:
        await report_channel.send(embed=log_embed)

    pretty_log(
        tag="info",
        message=f"Detected rare Pokémon: {pokemon_name}",
        label="🍀 FL RS CHECKER",
        bot=bot,
    )
