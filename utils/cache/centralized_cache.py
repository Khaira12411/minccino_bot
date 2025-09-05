# 🟣────────────────────────────────────────────
#       💜 Centralized Cache Loader 💜
#       🎀 Calls all individual caches 🎀
# ─────────────────────────────────────────────

from utils.cache.timers_cache import load_timer_cache, timer_cache
from utils.cache.held_item_cache import load_held_item_cache, held_item_cache
from utils.loggers.pretty_logs import pretty_log
from utils.cache.ball_reco_cache import load_ball_reco_cache, ball_reco_cache
from utils.cache.water_state_cache import get_water_state, fetch_latest_water_state
from utils.cache.reminders_cache import *
# 🐾────────────────────────────────────────────
#     💜 Load Everything in One Go
# 🐾────────────────────────────────────────────
async def load_all_caches(bot):
    """
    Centralized function to load all caches.
    Calls each cache loader in order and logs once at the end.
    """

    # ⌚ Load Timer cache
    await load_timer_cache(bot)

    # 🍄 Held Item Users Ping cache
    await load_held_item_cache(bot)

    # 🍀 Held Item Users Ping cache
    await load_ball_reco_cache(bot)

    # ⚾ User Reminders cache
    await load_user_reminders_cache(bot)

    # 🌊 Fetch latest waterstate
    await fetch_latest_water_state(bot)

    # 🎀 Unified single-line log with all caches
    pretty_log(
        tag="",
        message=(
            f"All caches refreshed and loaded "
            f"(Waterstate: {get_water_state()}, Timers: {len(timer_cache)}, "
            f"Held Items: {len(held_item_cache)}, Ball Recon: {len(ball_reco_cache)}, "
            f"Reminders: {len(user_reminders_cache)})"
        ),
        label="🥨 CENTRAL CACHE",
        bot=bot,
    )
