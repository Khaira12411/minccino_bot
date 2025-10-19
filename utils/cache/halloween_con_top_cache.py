from utils.database.hallowen_contest_top_db import get_halloween_con_top
from utils.loggers.pretty_logs import pretty_log

halloween_con_top_cache: dict[str, dict] = {}
# Structure:
# place -> {
#   "place": str,
#   "score": int
# }

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔍 Load halloween con top cache
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def load_halloween_con_top_cache(bot):
    """
    Load halloween top fourth place into cache
    """
    halloween_con_top_cache.clear()
    row = await get_halloween_con_top(bot, "fourth_place")
    if row:
        halloween_con_top_cache["fourth_place"] = row

    fourth_place_score = (
        (halloween_con_top_cache["fourth_place"]["score"])
        if "fourth_place" in halloween_con_top_cache
        else 0
    )
    try:
        pretty_log(
            "info",
            f"Loaded halloween con top fourth cache with score of {fourth_place_score}",
            label="🎃  Halloween Con Top CACHE",
            bot=bot,
        )
    except Exception as e:
        # fallback to console if Discord logging fails
        print(
            f"[🎃  Halloween Con Top CACHE] Loaded {len(halloween_con_top_cache)} entries (pretty_log failed: {e})"
        )

    return halloween_con_top_cache

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔍 Upsert score in cache
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def upsert_halloween_con_top_cache(place: str, score: int):
    """
    Insert or update a place's score in the halloween con top cache.
    """
    halloween_con_top_cache[place] = {
        "place": place,
        "score": score,
    }
    pretty_log(
        "db",
        f"Upserted halloween con top cache for place {place} with score {score}",
        label="🎃  Halloween Con Top CACHE",
    )

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔍 Update score in cache
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def update_halloween_con_top_cache(place: str, score: int):
    """
    Update a place's score in the halloween con top cache.
    """
    halloween_con_top_cache[place] = {
        "place": place,
        "score": score,
    }
    pretty_log(
        "db",
        f"Updated halloween con top cache for place {place} with score {score}",
        label="🎃  Halloween Con Top CACHE",
    )

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔍 Remove from cache
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def remove_halloween_con_top_cache(place: str):
    """
    Remove a place from the halloween con top cache.
    """
    if place in halloween_con_top_cache:
        del halloween_con_top_cache[place]
        pretty_log(
            "db",
            f"Removed halloween con top cache for place {place}",
            label="🎃  Halloween Con Top CACHE",
        )
