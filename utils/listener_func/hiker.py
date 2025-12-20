import re

import discord

from config.current_setup import MINCCINO_COLOR
from utils.essentials.pokemeow_helpers import get_pokemeow_reply_member
from utils.loggers.pretty_logs import pretty_log
thumbnail_url = "https://media.discordapp.net/attachments/1298966164072038450/1451980492730798090/image.png?ex=694825b5&is=6946d435&hm=1ec4545ed79d1abd5d7639b67c987975465b2bb86934fd42647632fb02795898&=&format=webp&quality=lossless&width=480&height=480"
DAMAGE_MAP = {
    "weak": {"pokemon": "Lvl 30 Tyrogue", "move": "High-Jump-Kick"},
    "decent": {"pokemon": "Lvl 49 Klinklang", "move": "Low-Kick"},
    "good": {"pokemon": "Lvl 45 Darmanitan", "move": "Fire-Punch"},
    "a lot": {"pokemon": "Lvl 80 Machoke", "move": "Karate-Chop"},
    "insane": {"pokemon": "Lvl 65 Machamp", "move": "Rock-Slide"},
}


def extract_snow_damage(text):
    match = re.search(
        r"<:snow:787559641663537153>[ \t]*(Weak|decent|insane|good|strong|A lot)(?!\S)",
        text,
        re.IGNORECASE,
    )
    if match:
        return match.group(1)
    return None


async def hiker_snow_damage_listener(message: discord.Message):

    member = await get_pokemeow_reply_member(message)
    if not member:
        return

    embed = message.embeds[0] if message.embeds else None
    if not embed:
        return
    description = embed.description if embed.description else ""
    damage_lvl = extract_snow_damage(description)
    if not damage_lvl:
        return
    display_damage_lvl = damage_lvl.title()
    damage_info = DAMAGE_MAP.get(damage_lvl.lower())
    if not damage_info:
        return
    pokemon = damage_info["pokemon"]
    move = damage_info["move"]
    display_move = move.replace("-", " ").title()

    embed = discord.Embed(
        title=f"{display_damage_lvl} Snow Move Suggestion",
        description=(f"{pokemon.title()} with {display_move}"),
        color=MINCCINO_COLOR,
    )
    embed.add_field(
        name="Step 1",
        value=f";bud set {pokemon}",
        inline=False,
    )
    embed.add_field(
        name="Step 2",
        value=f";hiker clear {move}",
        inline=False,
    )
    embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
    footer_text = f"Don't forget to set a different buddy after clearing the hiker!"
    embed.set_footer(
        text=footer_text,
        icon_url=(
            message.guild.icon.url if message.guild and message.guild.icon else None
        ),
    )
    embed.set_thumbnail(url=thumbnail_url)
    await message.channel.send(embed=embed)
    pretty_log(
        f"Hiker Snow Damage Listener triggered for {member.display_name} - {display_damage_lvl}"
    )
