# utils/ui/embeds/user_settings_embed.py

import discord

from config.aesthetic import *
from config.held_items import HELD_ITEM_EMOJI
from utils.embeds.design_embed import design_embed
from utils.listener_func.catch_rate import rarity_emojis


# Rarity order
RARITY_ORDER = [
    "common",
    "uncommon",
    "rare",
    "superrare",
    "legendary",
    "shiny",
    "golden",
]
REMINDER_MODE_EMOJIS = {
    "dms": "📩",
    "channel": "📢",
    "off": "🚫",
}
REMINDER_EMOJIS = {
    "relics": Emojis.relic,  # relic emoji
    "catchbot": Emojis.robot,  # catchbot emoji
}
# Per-category embed configuration
EMBED_CONFIG = {
    "timer": {
        "title": f"{Emojis.brown_clock} Timer Settings",
        "footer_text": "⏰ Ticking away, one Pokémon at a time!",
        "color": "brown",
        "thumbnail_url": MINC_Thumbnails.brown_clock,
        "image_url": None,
    },
    "ball_reco": {
        "title": f"{Emojis.brown_pokeball} Ball Recommendation Settings",
        "footer_text": "🎯 Pick the perfect ball and catch ’em all!",
        "color": "brown",
        "thumbnail_url": MINC_Thumbnails.pink_coffee,
        "image_url": None,
    },
    "held_items": {
        "title": f"{Emojis.brown_ribbon} Held Item Pings",
        "footer_text": "👜 Completing your set, one treasure at a time!",
        "color": "brown",
        "thumbnail_url": MINC_Thumbnails.brown_backpack,
        "image_url": None,
    },
    "reminders": {
        "title": f"{Emojis.notifs} Reminder Settings",
        "footer_text": "🔔 Stay on top of your relics and catchbot reminders!",
        "color": "brown",
        "thumbnail_url": MINC_Thumbnails.bell,
        "image_url": None,
    },
}
EMBED_CONFIG["wb_pings"] = {
    "title": f"{Emojis.boss} World Boss Pings",
    "footer_text": "⚔️ Track your world boss alerts here!",
    "color": "brown",
    "thumbnail_url": MINC_Thumbnails.boss,
    "image_url": None,
}

# Category header emojis
CATEGORY_HEADER_EMOJIS = {
    "pokemon": Emojis.brown_pokeball,
    "held_items": Emojis.backpack,
    "fishing": Emojis.fishing_rod,
}

def build_user_settings_embed(
    user: discord.Member, category: str, data: dict
) -> discord.Embed:

    config = EMBED_CONFIG.get(
        category,
        {
            "title": "⚠️ Unknown Category",
            "footer_text": "No data available.",
            "color": discord.Color.light_grey(),
            "thumbnail_url": None,
            "image_url": None,
        },
    )

    desc_lines = []

    # 💖────────────────────────💖
    # Pokémon Timer ⏰✨
    # 💖────────────────────────💖
    if category == "timer":
        desc_lines = [
            f"{Emojis.timer} Pokémon Timer: {data.get('pokemon_setting','Not Set')}",
            # f"🎣 Fishing Timer: {data.get('fish_setting','Not Set')}",
            # f"⚔️ Battle Timer: {data.get('battle_setting','Not Set')}",
        ]

    # 🎯────────────────────────🎀
    # Ball Recommendation 🎈🐾
    # 🎯────────────────────────🎀
    elif category == "ball_reco":
        sub_categories = ["pokemon", "held_items", "fishing"]
        for sub in sub_categories:
            sub_data = data.get(sub, {})
            if sub == "held_items" and isinstance(sub_data, set):
                sub_data = {key: True for key in sub_data}
            if not sub_data:
                continue

            lines = []

            # ✅ Add Display Mode if available
            display_mode = sub_data.get("display_mode")
            if isinstance(display_mode, str):
                display_mode = display_mode.strip().title()
                if display_mode not in ("Best Ball", "All"):
                    display_mode = "Best Ball"
                lines.append(f"🎛️ **Display Mode:** {display_mode}")

            # Rarities
            rarities_to_show = (
                RARITY_ORDER if sub != "held_items" else RARITY_ORDER[:-1]
            )
            if sub == "fishing":
                rarities_to_show = RARITY_ORDER

            for rarity in rarities_to_show:
                if rarity in sub_data:
                    val = sub_data[rarity]
                    emoji = rarity_emojis.get(rarity, "")
                    status = "✅" if val else "❌"
                    lines.append(f"{status} {emoji} {rarity.title()}")

            if lines:
                header_emoji = CATEGORY_HEADER_EMOJIS.get(sub, "")
                desc_lines.append(
                    f"{header_emoji} **{sub.title()}**\n" + "\n".join(lines)
                )

    # 👜────────────────────────💜
    # Held Item Pings 🎒✨
    # 👜────────────────────────💜
    elif category == "held_items":
        subscribed_items = data.get("subscribed_items", set())
        all_flag = data.get("all_held_items", False)
        if subscribed_items or all_flag:
            lines = []
            for item in sorted(subscribed_items):
                emoji = getattr(HELD_ITEM_EMOJI, item, "🐭")
                lines.append(f"✅ {emoji} {item.replace('_',' ').title()}")
            desc_lines.append("\n".join(lines))
        else:
            desc_lines.append("No held item subscriptions.")

    # 🔔────────────────────────🌸
    #   Reminder Settings 📩💖
    # 🔔────────────────────────🌸
    elif category == "reminders":
        if not data:  # no reminders set
            desc_lines.append("❌ No reminders set.")
        else:
            for cat, settings in data.items():
                emoji = REMINDER_EMOJIS.get(cat, "❔")

                # Mode
                mode = settings.get("mode", "off") or "off"
                mode_emoji = REMINDER_MODE_EMOJIS.get(mode.lower(), "❔")
                mode_display = f"{mode_emoji} {mode.title() if mode else 'Off'}"

                lines = [f"Mode: {mode_display}"]

                # Relics-specific
                if cat == "relics":
                    has_exchanged = settings.get("has_exchanged", False)
                    lines.append(f"Has Exchanged: {'✅' if has_exchanged else '🚫'}")

                    expires_on = settings.get("expires_on") or 0
                    if expires_on and has_exchanged:
                        lines.append(f"Expiration: <t:{expires_on}:f>")

                # Catchbot-specific
                if cat == "catchbot":
                    repeating = settings.get("repeating") or 0
                    returns_on = settings.get("returns_on") or 0
                    reminds_next_on = settings.get("reminds_next_on") or 0

                    if repeating > 0:
                        lines.append(f"⏱️ Repeating: Every {repeating} mins")
                        if reminds_next_on:
                            lines.append(f"Reminds Next On: <t:{reminds_next_on}:f>")

                    if mode.lower() != "off" and returns_on:
                        lines.append(f"Returns On: <t:{returns_on}:f>")

                desc_lines.append(f"{emoji} **{cat.title()}**\n" + "\n".join(lines))


    else:
        desc_lines.append("No data available.")

    embed = discord.Embed(
        title=config["title"],
        description="\n\n".join(desc_lines),
    )

    embed = design_embed(
        user=user,
        embed=embed,
        thumbnail_url=config.get("thumbnail_url"),
        footer_text=config.get("footer_text"),
        image_url=config.get("image_url"),
        color=config["color"],
    )

    return embed
