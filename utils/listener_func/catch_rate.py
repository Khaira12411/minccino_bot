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


def compute_fishing_rate(rarity, ball, state=None, boost=0, is_patreon=False):
    """
    Compute fishing catch rate.
    - rarity: e.g. "common_45", "rare_25", "shiny_0", "golden_0"
    - ball: e.g. "pokeball", "ultraball", "diveball", etc.
    - state: string water state ("calm", "strong", etc.) or None
    - boost: flat % boost
    - is_patreon: True/False → adds +5%
    """
    base_rate = fishing_catch_rates["non_patron"][rarity][ball]
    state = state.lower()
    if state and state in fishing_catch_rates["states"]:
        state_mod = fishing_catch_rates["states"][state]
        # Dive & Master Ball cannot drop below 100%
        if ball in ["diveball", "masterball"] and base_rate >= 100:
            state_mod = max(0, state_mod)
        base_rate += state_mod

    if is_patreon:
        base_rate += 5

    base_rate += boost
    return max(0, min(100, base_rate))


def best_ball_fishing(rarity, state=None, boost=0, is_patreon=False, form=None):
    """
    Recommend the most optimal fishing ball for a given rarity and form.
    - Uses cached water state if `state` is None.
    """
    # Use cached water state if not provided
    from utils.cache.water_state_cache import get_water_state
    if state is None:
        state = get_water_state()  # returns "strong", "calm", etc.

    state = state.lower()

    # Map form + rarity to proper key
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
    results = {}

    # Compute catch rate for each ball
    for ball in ball_priority:
        rate = compute_fishing_rate(
            key, ball, state=state, boost=boost, is_patreon=is_patreon
        )
        results[ball] = rate

    # Filter expensive balls for superrare and below
    superrare_and_below = {"common", "uncommon", "rare", "superrare"}
    form_is_special = form in {"shiny", "golden"}

    filtered_results = {}
    for ball, rate in results.items():
        if rarity in superrare_and_below and ball in {
            "premierball",
            "diveball",
            "masterball",
        }:
            continue
        if ball == "diveball" and (not form_is_special or rate < 100):
            continue
        filtered_results[ball] = rate

    # fallback for special forms
    if not filtered_results and form_is_special:
        for ball, rate in results.items():
            if ball in {"diveball", "masterball", "premierball"}:
                filtered_results[ball] = rate

    max_rate = max(filtered_results.values())
    for ball in ball_priority:
        if ball in filtered_results and filtered_results[ball] == max_rate:
            return ball, filtered_results[ball], results

    return None, 0, results


def compute_catch_rate(
    category, rarity, ball, boost=0, is_patreon=False, ultra_beast=False
):
    """
    Compute final catch rate.
    - category: "non_patron_gen_1_8" or "held_item_pokemon"
    - rarity: e.g. "uncommon_60"
    - ball: e.g. "greatball"
    - boost: flat % boost (default 0)
    - is_patreon: True/False → adds +5% if True
    - ultra_beast: True/False → Beast Ball auto 80% if True
    """
    base_rate = catch_rates[category][rarity][ball]

    # Ultra Beast special rule
    if ball == "beastball" and ultra_beast:
        base_rate = 80

    # Apply Patreon boost
    if is_patreon:
        base_rate += 5
    base_rate += boost

    # Cap at 100%
    return min(100, base_rate)


def best_ball(category, rarity, boost=0, is_patreon=False, ultra_beast=False):
    """
    Find the most optimal ball to use for a given rarity.
    Masterball → only 'shiny' or 'golden'.
    Premier Ball → only 'shiny', 'golden', or 'legendary'.
    """
    ball_priority = [
        "pokeball",
        "greatball",
        "ultraball",
        "premierball",
        "beastball",
        "masterball",
    ]
    results = {}

    # Compute catch rate for every ball
    for ball in ball_priority:
        results[ball] = compute_catch_rate(
            category,
            rarity,
            ball,
            boost=boost,
            is_patreon=is_patreon,
            ultra_beast=ultra_beast,
        )

    # Determine which balls to consider
    allowed_balls = ball_priority.copy()

    # Masterball restriction
    if rarity not in ["full_odds_shiny_64", "event_shiny_0"]:
        if "masterball" in allowed_balls:
            allowed_balls.remove("masterball")

    # Premier Ball restriction
    if rarity not in [
        "full_odds_shiny_64",
        "event_shiny_0",
        "legendary_5",
        "legendary_0",
    ]:
        if "premierball" in allowed_balls:
            allowed_balls.remove("premierball")

    # Find max rate among allowed balls
    max_rate = max(results[ball] for ball in allowed_balls)

    # Pick the cheapest (lowest priority) ball that gives max_rate
    for ball in allowed_balls:
        if results[ball] == max_rate:
            return ball, results[ball], results
