rarity = ["common", "uncommon", "rare", "superrare", "legendary", "shiny", "golden"]


balls = [
    "pokeball",
    "greatball",
    "ultraball",
    "premierball",
    "masterball",
    "beastball",
    "diveball",
]

rarity_emojis = {
    "common": "<:common:1412000858329321482>",
    "uncommon": "<:uncommon:1412000832161054770>",
    "rare": "<:rare:1412000815882829864>",
    "superrare": "<:superrare:1412000776439595110>",
    "legendary": "<:legendary:1412000748660850779>",
    "shiny": "<:shiny:1412000714804170803>",
    "golden": "<:golden:1412000647666073670>",
}

ball_emojis = {
    "pokeball": "<:pokeball:1411999795110744145>",
    "greatball": "<:greatball:1411999846835159081>",
    "ultraball": "<:ultraball:1411999983409958972>",
    "premierball": "<:premierball:1412000053459161138>",
    "masterball": "<:masterball:1412000094223339601>",
    "beastball": "<:beastball:1412000353645236245>",
    "diveball": "<:diveball:1412001883639517275>",
}


catch_rates = {
    "non_patron_gen_1_8": {
        "common_70": {
            "pokeball": 80,
            "greatball": 95,
            "ultraball": 100,
            "premierball": 100,
            "masterball": 100,
            "beastball": 70,
        },
        "uncommon_60": {
            "pokeball": 70,
            "greatball": 85,
            "ultraball": 92,
            "premierball": 100,
            "masterball": 100,
            "beastball": 60,
        },
        "rare_37": {
            "pokeball": 47,
            "greatball": 62,
            "ultraball": 72,
            "premierball": 87,
            "masterball": 100,
            "beastball": 37,
        },
        "super_rare_20": {
            "pokeball": 30,
            "greatball": 45,
            "ultraball": 55,
            "premierball": 70,
            "masterball": 100,
            "beastball": 20,
        },
        "legendary_5": {
            "pokeball": 15,
            "greatball": 30,
            "ultraball": 40,
            "premierball": 55,
            "masterball": 100,
            "beastball": 5,
        },
        "event_shiny_0": {
            "pokeball": 0,
            "greatball": 0,
            "ultraball": 0,
            "premierball": 0,
            "masterball": 100,
            "beastball": 0,
        },
        "full_odds_shiny_64": {
            "pokeball": 74,
            "greatball": 89,
            "ultraball": 95,
            "premierball": 100,
            "masterball": 100,
            "beastball": 64,
        },
    },
    "held_item_pokemon": {
        "common_25": {
            "pokeball": 35,
            "greatball": 50,
            "ultraball": 60,
            "premierball": 75,
            "masterball": 100,
            "beastball": 25,
        },
        "uncommon_20": {
            "pokeball": 30,
            "greatball": 45,
            "ultraball": 55,
            "premierball": 70,
            "masterball": 100,
            "beastball": 20,
        },
        "rare_15": {
            "pokeball": 25,
            "greatball": 40,
            "ultraball": 50,
            "premierball": 65,
            "masterball": 100,
            "beastball": 15,
        },
        "super_rare_10": {
            "pokeball": 20,
            "greatball": 35,
            "ultraball": 45,
            "premierball": 60,
            "masterball": 100,
            "beastball": 10,
        },
        "legendary_0": {
            "pokeball": 10,
            "greatball": 25,
            "ultraball": 35,
            "premierball": 50,
            "masterball": 100,
            "beastball": 0,
        },
        "event_shiny_0": {
            "pokeball": 0,
            "greatball": 0,
            "ultraball": 0,
            "premierball": 0,
            "masterball": 100,
            "beastball": 0,
        },
        "full_odds_shiny_0": {
            "pokeball": 10,
            "greatball": 25,
            "ultraball": 35,
            "premierball": 50,
            "masterball": 100,
            "beastball": 0,
        },
    },
}
fishing_catch_rates = {
    "non_patron": {
        "common_45": {
            "pokeball": 55,
            "greatball": 70,
            "ultraball": 80,
            "premierball": 95,
            "diveball": 100,
            "masterball": 100,
            "beastball": 45,
        },
        "uncommon_35": {
            "pokeball": 45,
            "greatball": 60,
            "ultraball": 70,
            "premierball": 85,
            "diveball": 100,
            "masterball": 100,
            "beastball": 35,
        },
        "rare_25": {
            "pokeball": 35,
            "greatball": 50,
            "ultraball": 60,
            "premierball": 75,
            "diveball": 100,
            "masterball": 100,
            "beastball": 25,
        },
        "super_rare_15": {
            "pokeball": 25,
            "greatball": 40,
            "ultraball": 50,
            "premierball": 65,
            "diveball": 100,
            "masterball": 100,
            "beastball": 15,
        },
        "legendary_5": {
            "pokeball": 15,
            "greatball": 30,
            "ultraball": 40,
            "premierball": 55,
            "diveball": 90,
            "masterball": 100,
            "beastball": 5,
        },
        "shiny_0": {
            "pokeball": 10,
            "greatball": 25,
            "ultraball": 35,
            "premierball": 50,
            "diveball": 85,
            "masterball": 100,
            "beastball": 0,
        },
        "golden_0": {
            "pokeball": 10,
            "greatball": 25,
            "ultraball": 35,
            "premierball": 50,
            "diveball": 85,
            "masterball": 100,
            "beastball": 0,
        },
    },
    "states": {
        "calm": +5,
        "moderate": -5,
        "strong": -7,
        "intense": -10,
        "special": +10,
    },
}

WS_MAP = {
    -10: "intense",
    -7: "strong",
    -5: "moderate",
    0: None,
    5: "calm",
    10: "special",
}
from config.aesthetic import *
# Map ball names to unlocked emojis
UNLOCKED_BALL_EMOJIS = {
    "pokeball": Emojis.pokeball_unlocked,
    "greatball": Emojis.greatball_unlocked,
    "ultraball": Emojis.ultraball_unlocked,
    "premierball": Emojis.premierball_unlocked,
    "masterball": Emojis.masterball_unlocked,
    "beastball": Emojis.beastball_unlocked,
    "diveball": Emojis.diveball_unlocked,
}

def compute_fishing_rate(
    rarity, ball, state=None, is_patreon=False, channel_boost=False
):
    """
    Compute fishing catch rate with optional Patreon and channel boost.
    """
    base_rate = fishing_catch_rates["non_patron"][rarity][ball]

    if state:
        state = state.lower()
        if state in fishing_catch_rates["states"]:
            state_mod = fishing_catch_rates["states"][state]
            if ball in ["diveball", "masterball"] and base_rate >= 100:
                state_mod = max(0, state_mod)
            base_rate += state_mod

    # Bonuses
    patron_bonus = 5 if is_patreon else 0
    channel_bonus = 5 if channel_boost else 0
    total_rate = base_rate + patron_bonus + channel_bonus

    """print(
        f"[DEBUG] compute_fishing_rate: {ball=} base={base_rate}% "
        f"(patron={patron_bonus}, channel_boost={channel_bonus}) total={total_rate}%"
    )"""

    return max(0, min(100, total_rate))


def best_ball_fishing(
    rarity,
    state=None,
    is_patreon=False,
    channel_boost=False,
    form=None,
    display_all: bool = False,
):
    from utils.cache.water_state_cache import get_water_state

    if state is None:
        state = get_water_state()
    state = state.lower()

    key = rarity
    if form == "shiny":
        key = "shiny_0"
    elif form == "golden":
        key = "golden_0"
    else:
        rarity_map = {
            "common": "common_45",
            "uncommon": "uncommon_35",
            "rare": "rare_25",
            "superrare": "super_rare_15",
            "legendary": "legendary_5",
        }
        key = rarity_map.get(rarity, rarity)

    ball_priority = [
        "pokeball",
        "greatball",
        "ultraball",
        "premierball",
        "beastball",
        "diveball",
        "masterball",
    ]

    actual_results = {}
    for ball in ball_priority:
        actual_results[ball] = compute_fishing_rate(
            key, ball, state=state, is_patreon=is_patreon, channel_boost=channel_boost
        )

    superrare_and_below = {"common", "uncommon", "rare", "superrare"}
    filtered_results = {
        b: r
        for b, r in actual_results.items()
        if not (
            rarity in superrare_and_below
            and b in {"premierball", "diveball", "masterball"}
        )
    }

    max_rate = max(filtered_results.values())
    for ball in ball_priority:
        if ball in filtered_results and filtered_results[ball] == max_rate:
            best = ball
            break

    # Display string using unlocked emojis
    all_balls_str = " | ".join(
        f"{UNLOCKED_BALL_EMOJIS[b]} ({actual_results[b]}%)" for b in ball_priority
    )

    return (
        best,
        filtered_results[best],
        actual_results,
        all_balls_str if display_all else None,
    )


def compute_catch_rate(
    category,
    rarity,
    ball,
    boost=0,
    is_patreon=False,
    channel_boost=False,
    ultra_beast=False,
):
    """
    Compute final catch rate.
    - category: "non_patron_gen_1_8" or "held_item_pokemon"
    - rarity: e.g. "uncommon_60"
    - ball: e.g. "greatball"
    - boost: flat % boost (default 0)
    - is_patreon: True/False → adds +5% if True
    - channel_boost: True/False → adds +5% if True
    - ultra_beast: True/False → Beast Ball auto 80% if True
    """
    base_rate = catch_rates[category][rarity][ball]

    # Ultra Beast special rule
    if ball == "beastball" and ultra_beast:
        base_rate = 80

    # Apply boosts
    """if is_patreon:
        base_rate += 5"""
    if channel_boost:
        base_rate += 5
    base_rate += boost

    # Cap at 100%
    return min(100, base_rate)


def best_ball(
    category,
    rarity,
    boost=0,
    is_patreon=False,
    channel_boost=False,
    ultra_beast=False,
    display_all: bool = False,
):
    ball_priority = [
        "pokeball",
        "greatball",
        "ultraball",
        "premierball",
        "beastball",
        "masterball",
    ]
    results = {}

    for ball in ball_priority:
        results[ball] = compute_catch_rate(
            category,
            rarity,
            ball,
            boost=boost,
            is_patreon=is_patreon,
            channel_boost=channel_boost,
            ultra_beast=ultra_beast,
        )

    # Determine allowed balls
    allowed_balls = ball_priority.copy()
    if rarity not in ["full_odds_shiny_64", "event_shiny_0"]:
        allowed_balls = [b for b in allowed_balls if b != "masterball"]
    if rarity not in [
        "full_odds_shiny_64",
        "event_shiny_0",
        "legendary_5",
        "legendary_0",
    ]:
        allowed_balls = [b for b in allowed_balls if b != "premierball"]

    max_rate = max(results[ball] for ball in allowed_balls)
    for ball in allowed_balls:
        if results[ball] == max_rate:
            best = ball
            break

    # Display string using unlocked emojis
    all_balls_str = " | ".join(
        f"{UNLOCKED_BALL_EMOJIS[b]} ({results[b]}%)" for b in ball_priority
    )

    return best, results[best], results, all_balls_str if display_all else None
