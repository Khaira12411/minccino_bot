from datetime import datetime
import random
import discord


def format_bulletin_desc(*args, key_style_override: str = None) -> str:
    """
    Flexible bulletin formatter.
    - By default, keys are bold.
    - If key_style_override is provided, all keys use that style.
    - Skips any key/value pair where the value is None or empty string.
    """

    def apply_style(text: str, style: str) -> str:
        style = style.lower()
        if style == "bold":
            return f"**{text}**"
        elif style == "italic":
            return f"*{text}*"
        elif style == "underline":
            return f"__{text}__"
        elif style == "strikethrough":
            return f"~~{text}~~"
        elif style == "spoiler":
            return f"||{text}||"
        elif style == "inline_code":
            return f"`{text}`"
        elif style == "code":
            return f"```\n{text}\n```"
        elif style == "bold_upper":
            return f"**{text.upper()}**"
        else:
            return f"**{text}**"  # default bold

    key_style = key_style_override if key_style_override else "bold"

    lines = []
    i = 0
    while i < len(args):
        key = args[i]
        value = args[i + 1] if i + 1 < len(args) else None

        # 🔹 Skip if value is None or empty string
        if value is None or (isinstance(value, str) and value.strip() == ""):
            i += 2
            continue

        formatted_key = apply_style(f"{key}:", key_style)
        lines.append(f"- {formatted_key} {value}")

        i += 2

    return "\n".join(lines)


# -------------------- 🎨 Minccino Pastel Palette --------------------
MINCCINO_PALETTE = {
    "silver": ["#C0C0C0", "#D3D3D3", "#B0B0B0", "#D9D9D9", "#E0E0E0"],
    "gray": ["#A9A9A9", "#BEBEBE", "#DCDCDC", "#E8E8E8", "#F0F0F0"],
    "cream": ["#F5F5DC", "#FAF3E0", "#FFFDD0", "#FDF6EC", "#FBFBEF"],
    "brown": ["#A1887F", "#8D6E63", "#BCAAA4", "#D7CCC8", "#6D4C41"],
}


def get_random_minccino_shade(shade: str = None) -> discord.Colour:
    """
    Returns a random Minccino-themed color.
    If shade is None or invalid, picks from the whole Minccino palette.
    """
    if shade is None or shade.lower() not in MINCCINO_PALETTE:
        shade = random.choice(list(MINCCINO_PALETTE.keys()))
    colors = MINCCINO_PALETTE[shade.lower()]
    return discord.Colour(int(random.choice(colors).lstrip("#"), 16))


def get_random_minccino_color() -> discord.Colour:
    """Returns a random Minccino color from the entire palette."""
    return get_random_minccino_shade()


# -------------------- 🎀 Embed Designer --------------------
def design_embed(
    user: discord.Member,
    embed: discord.Embed,
    thumbnail_url: str = None,
    image_url: str = None,
    footer_text: str = None,
    color: str | discord.Color | None = None,  # accept string or Color object
):
    # -------------------- [🤍 COLOR SETTER] --------------------
    if isinstance(color, str):
        embed.color = get_random_minccino_shade(color)
    elif isinstance(color, discord.Color):
        embed.color = color
    else:
        embed.color = get_random_minccino_color()  # default random Minccino tone

    # -------------------- [🤍 AUTHOR & TIMESTAMP] --------------------
    embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)
    embed.timestamp = datetime.now()

    # -------------------- [🤍 THUMBNAIL] --------------------
    if thumbnail_url is None:
        thumbnail_url = user.display_avatar.url
    embed.set_thumbnail(url=thumbnail_url)

    # -------------------- [🤍 IMAGE] --------------------
    if image_url:
        embed.set_image(url=image_url)

    # -------------------- [🤍 FOOTER] --------------------
    if footer_text is None:
        footer_text = f"User ID: {user.id}"
    embed.set_footer(text=footer_text, icon_url=user.guild.icon.url)

    # -------------------- [✨ DONE] --------------------
    return embed
