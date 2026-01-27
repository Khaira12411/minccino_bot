import re

import discord
from discord.ext import commands

from config.straymons_constants import STRAYMONS__EMOJIS, STRAYMONS__TEXT_CHANNELS
from utils.embeds.design_embed import design_embed
from utils.essentials.pokemeow_helpers import get_pokemeow_reply_member
from utils.essentials.webhook import send_webhook
from utils.loggers.debug_log import debug_log, enable_debug
from utils.loggers.pretty_logs import pretty_log

# enable_debug(f"{__name__}.fl_rs_checker")
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
NON_RARE_COLORS = {
    rarity_meta.get("common")["color"],
    rarity_meta.get("uncommon")["color"],
    rarity_meta.get("rare")["color"],
    rarity_meta.get("superrare")["color"],
}


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


def extract_member_username_from_embed(embed: discord.Embed) -> str | None:
    """
    Extracts the username from the embed author name, e.g. "Congratulations, frayl!" -> "frayl".
    Returns None if not found.
    """
    if embed.author and embed.author.name:
        # Try 'Congratulations, username!' first
        match = re.search(r"Congratulations, ([^!]+)!", embed.author.name)
        if match:
            return match.group(1).strip()
        # Fallback: 'Well done, username!'
        match = re.search(r"Well done, ([^!]+)!", embed.author.name)
        if match:
            return match.group(1).strip()
        # Fallback: 'Great work, username!'
        match = re.search(r"Great work, ([^!]+)!", embed.author.name)
        if match:
            return match.group(1).strip()
    return None


# 🐾────────────────────────────────────────────
#     ✨ Feeling Lucky Rare Pokémon Checker
# 🐾────────────────────────────────────────────
async def fl_rs_checker(bot: discord.Client, message: discord.Message):
    if not message.embeds:
        return

    embed = message.embeds[0]
    embed_color = embed.color

    # Extract Pokémon name
    pokemon_name = None
    if embed.description:
        catch_match = re.search(r"You caught a.*?\*\*([^*]+)\*\*", embed.description)
        if catch_match:
            pokemon_name = catch_match.group(1).strip()
            debug_log(f"Extracted Pokémon Name: {pokemon_name}")
        else:
            debug_log("No Pokémon name found in embed description.")
            return

    debug_log(f"Embed Color: {embed_color}")
    if (
        embed.color
        and embed.color.value not in RARE_COLORS
        and embed.color.value in NON_RARE_COLORS
    ):

        debug_log("Non-rare color detected, exiting FL RS Checker.")
        return

    rarity = "unknown"
    member = await get_pokemeow_reply_member(message=message)
    if not member:
        debug_log("No member found from PokéMeow reply.")
        # Fallback: Try to extract username from embed author
        username = extract_member_username_from_embed(embed)
        if not username:
            debug_log(
                "Failed to extract username from embed author. Exiting FL RS Checker."
            )
            return

        debug_log(f"Extracted username from embed: {username}")
        from utils.cache.straymon_member_cache import fetch_straymon_user_id_by_username

        user_id = fetch_straymon_user_id_by_username(username)
        if not user_id:
            debug_log("Failed to fetch user ID from username. Exiting FL RS Checker.")
            return
        debug_log(f"Fetched user ID from username: {user_id}")
        member = message.guild.get_member(user_id)
        if not member:
            debug_log("Failed to fetch member from username. Exiting FL RS Checker.")
            return
        debug_log(f"Fetched member from username: {username}")

    if embed.color.value == legendary_color:
        rarity = "legendary"
        pretty_log(
            tag="info",
            message="Feeling Lucky spawn is legendary.",
            label="🍀 FL RS CHECKER",
            bot=bot,
        )
    elif embed.color.value == shiny_color:
        rarity = "shiny"
        pokemon_name = pokemon_name.replace("Shiny ", "")
        pretty_log(
            tag="info",
            message="Feeling Lucky spawn is shiny.",
            label="🍀 FL RS CHECKER",
            bot=bot,
        )
    elif embed.color.value == event_exclusive_color:
        # Extract rarity from footer for event exclusive
        if embed.footer and embed.footer.text:
            rarity = extract_rarity_from_footer(embed.footer.text)
            if rarity.lower() != "shiny" and rarity.lower() != "legendary":
                return

            pretty_log(
                tag="info",
                message=f"Feeling Lucky spawn is event exclusive with rarity: {rarity}.",
                label="🍀 FL RS CHECKER",
                bot=bot,
            )
    # If unknown color, extract rarity from footer
    elif embed.color and embed.color.value not in RARE_COLORS:
        if embed.footer and embed.footer.text:
            pretty_log(
                tag="info",
                message="Feeling Lucky spawn has unknown color. Attempting to extract rarity from footer.",
                label="🍀 FL RS CHECKER",
                bot=bot,
            )
            extracted_rarity = extract_rarity_from_footer(embed.footer.text)
            if extracted_rarity:
                rarity = extracted_rarity

                if rarity.lower() != "legendary":
                    pretty_log(
                        tag="info",
                        message=f"Extracted rarity from footer: {rarity}. Exiting FL RS Checker.",
                        label="🍀 FL RS CHECKER",
                        bot=bot,
                    )
                    return
                else:
                    pretty_log(
                        tag="info",
                        message="Extracted rarity is legendary. Continuing FL RS Checker.",
                        label="🍀 FL RS CHECKER",
                        bot=bot,
                    )

    image_url = embed.image.url if embed.image else None

    emoji = rarity_meta.get(rarity, rarity_meta["default"]).get("emoji", "❓")
    display_pokemon_name = f"{emoji} {pokemon_name.title()}"

    desc = (
        f"Member: {member.mention}\n"
        f"Pokemon: {display_pokemon_name}\n\n"
        f"Don't forget to forward the rare spawn in <#1167381632429342794>!"
    )

    log_embed = discord.Embed(
        title="Feeling Lucky Rare Spawn",
        url=message.jump_url,
        description=desc,
        color=embed_color,
    )
    log_embed = design_embed(
        user=member, embed=log_embed, thumbnail_url=image_url if image_url else None
    )
    log_embed.color = message.embeds[0].color

    report_channel = message.guild.get_channel(STRAYMONS__TEXT_CHANNELS.reports)
    if report_channel:
        await send_webhook(bot, report_channel, embed=log_embed)

    pretty_log(
        tag="info",
        message=f"Detected rare Pokémon: {pokemon_name}",
        label="🍀 FL RS CHECKER",
        bot=bot,
    )
