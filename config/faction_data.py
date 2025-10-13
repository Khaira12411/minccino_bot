FACTION_LOGO_EMOJIS = {
    "aqua": "<:team_logo:1276285308794835139>",
    "magma": "<:team_logo:1276300583300759623>",
    "flare": "<:team_logo:1276340625725329491>",
    "rocket": "<:team_logo:1276285077701263432>",
    "plasma": "<:team_logo:1276335185499000915>",
    "galactic": "<:team_logo:1276325626055491705>",
    "skull": "<:team_logo:1276346100848132106>",
    "yell": "<:team_logo:1276346491975372871>",
}


def get_faction_by_emoji(emoji: str) -> str | None:
    """
    Given an emoji string, return the faction key if found, else None.
    """
    for faction, emj in FACTION_LOGO_EMOJIS.items():
        if emoji == emj:
            return faction
    return None


# Example usage:
# faction = get_faction_by_emoji("<:team_logo:1276346491975372871>")
# print(faction)  # Output: "yell"
