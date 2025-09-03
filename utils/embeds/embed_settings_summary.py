# utils/ui/embeds/subscription_embed.py

import discord

from config.held_items import HELD_ITEM_EMOJI
from utils.listener_func.catch_rate import rarity_emojis

thumbnail_url = "https://media.discordapp.net/attachments/1394913073520967680/1412327847636500490/45e3da7b23b584e878b15a1dd13a87ab-removebg-preview.png?ex=68b7e44e&is=68b692ce&hm=f8e586d090d18fd4d1795303cdd9f739851df5a197ac0f7fc6a43e28007dc811&=&format=webp&quality=lossless&width=563&height=563"

from config.held_items import *
from utils.embeds.design_embed import design_embed
from config.aesthetic import Emojis


def build_summary_settings_embed(
    user: discord.Member,
    title: str,
    changes: list[tuple] | dict = None,
    mode: str = "rarity",
    simple: bool = False,
    description: str | None = None,
) -> discord.Embed:
    """
    Build a standardized embed for subscription updates.
    """
    desc_lines = []
    rarity_order = [
        "common",
        "uncommon",
        "rare",
        "superrare",
        "legendary",
        "shiny",
        "golden",
    ]

    if changes:
        if mode == "rarity":
            if isinstance(changes, dict):
                sub_categories = ["pokemon", "held_items", "fishing"]
                emoji_headers = {
                    "pokemon": Emojis.brown_pokeball,
                    "held_items": Emojis.backpack,
                    "fishing": Emojis.fishing_rod,
                }

                for sub in sub_categories:
                    if sub not in changes or not changes[sub]:
                        continue
                    if description or changes[sub]:
                        # 🔹 Add spacing before each category except the first
                        if desc_lines:
                            desc_lines.append("\u200b")

                        # 🔹 Rename held_items -> Pokemon w/ Held Items
                        header_name = (
                            "Pokemon w/ Held Items"
                            if sub == "held_items"
                            else sub.replace("_", " ").title()
                        )
                        desc_lines.append(f"{emoji_headers.get(sub,'')} {header_name}")

                    for r in rarity_order:
                        if r == "golden" and sub != "fishing":
                            continue
                        if r in changes[sub]:
                            enabled = changes[sub][r]
                            emoji_str = rarity_emojis.get(r, "❔")
                            desc_lines.append(
                                f"{'✅' if enabled else '❌'} {emoji_str} {r.title()}"
                            )

            else:
                grouped_changes = {r: [] for r in rarity_order}
                for rarity, enabled in changes:
                    if rarity == "golden":
                        continue
                    grouped_changes[rarity].append(enabled)

                for rarity in rarity_order:
                    if grouped_changes[rarity]:
                        emoji_str = rarity_emojis.get(rarity, "❔")
                        if description:
                            desc_lines.append(f"**{rarity.title()}**")
                        for enabled in grouped_changes[rarity]:
                            desc_lines.append(
                                f"{'✅' if enabled else '❌'} {emoji_str} {rarity.title()}"
                            )

        elif mode == "held_items":
            for r in rarity_order:
                if r == "golden":
                    continue
                relevant_items = [
                    item_tuple for item_tuple in changes if item_tuple[0] == r
                ]
                for item_tuple in relevant_items:
                    emoji_str = rarity_emojis.get(r, "❔")
                    if simple:
                        new_state = (
                            item_tuple[-1] if len(item_tuple) == 3 else item_tuple[1]
                        )
                        desc_lines.append(
                            f"{'✅' if new_state else '❌'} {emoji_str} {r.title()}"
                        )
                    else:
                        old, new = item_tuple[1], item_tuple[2]
                        status_change = "✅" if new else "❌"
                        desc_lines.append(
                            f"{status_change} {emoji_str} {r.title()}: "
                            f"{'On' if old else 'Off'} -> {'On' if new else 'Off'}"
                        )

        elif mode == "held_items_ping":
            for item_tuple in changes:
                item_name = item_tuple[0]
                old_state, new_state = item_tuple[1], item_tuple[2]

                emoji_str = HELD_ITEMS_DICT.get(item_name, {}).get("emoji", "🐭")
                status_change = "✅" if new_state else "❌"

                desc_lines.append(
                    f"{status_change} {emoji_str} {item_name.replace('_',' ').title()}: "
                    f"{'On' if old_state else 'Off'} -> {'On' if new_state else 'Off'}"
                )

    # Merge description + changes list
    full_desc = description.strip() if description else ""
    if desc_lines:
        if full_desc:
            full_desc += "\n\n" + "\n".join(desc_lines)
        else:
            full_desc = "\n".join(desc_lines)

    embed = discord.Embed(
        title=title,
        description=full_desc or "No changes detected.",
    )

    footer_text = "Your subscription settings have been updated ✨"
    embed = design_embed(
        user=user,
        embed=embed,
        thumbnail_url=thumbnail_url,
        footer_text=footer_text,
        color="brown",
    )

    return embed
