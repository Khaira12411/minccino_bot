import unicodedata

from config.aesthetic import *

BALL_EMOJIS = {
    "pokeball": Emojis_Balls.pokeball,
    "greatball": Emojis_Balls.greatball,
    "ultraball": Emojis_Balls.ultraball,
    "premierball": Emojis_Balls.premierball,
    "masterball": Emojis_Balls.masterball,
    "ancientball": Emojis_Balls.ancient_ball,
    "beastball": Emojis_Balls.beastball,
    "duskball": Emojis.duskball,
    "fastball": Emojis.fastball,
    "friendball": Emojis_Balls.friendball,
    "heavyball": Emojis.heavyball,
    "loveball": Emojis_Balls.loveball,
    "lureball": Emojis.lureball,
    "luxuryball": Emojis_Balls.luxuryball,
    "moonball": Emojis.moonball,
    "netball": Emojis.netball,
    "quickball": Emojis_Balls.quickball,
    "diveball": Emojis_Balls.diveball,
    "safariball": Emojis_Balls.safariball,
}

def normalize_ball_type(ball_type: str) -> str:
    # Strip accents so "Poké Ball" resolves to "pokeball".
    ball_type = unicodedata.normalize("NFD", ball_type)
    ball_type = "".join(c for c in ball_type if not unicodedata.combining(c))
    return ball_type.strip().lower().replace(" ", "")


def format_ball(ball_type: str) -> str:
    """Return '<emoji> **Ball Name**' for a ball key such as 'safariball'."""
    key = normalize_ball_type(ball_type)
    base = key[:-4] if key.endswith("ball") and len(key) > 4 else key
    name = f"{base.title()} Ball" if key.endswith("ball") else key.title()
    emoji = BALL_EMOJIS.get(key, "")
    return f"{emoji} **{name}**".strip()
