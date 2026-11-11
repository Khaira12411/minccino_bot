# 🟣────────────────────────────────────────────
#       💜 Centralized Cache Loader 💜
#       🎀 Calls all individual caches 🎀
# ─────────────────────────────────────────────
from utils.cache.ball_reco_cache import ball_reco_cache, load_ball_reco_cache
from utils.cache.boosted_channels_cache import (
    boosted_channels_cache,
    load_boosted_channels_cache,
)
from utils.cache.cache_list import (
    probation_members_cache,
    timer_cache,
    webhook_url_cache,
)
from utils.cache.catchlist_cache import catchlist_cache, load_catchlist_cache
from utils.cache.daily_fa_ball_cache import (
    daily_faction_ball_cache,
    load_daily_faction_ball_cache,
)
from utils.cache.faction_ball_alert_cache import (
    faction_ball_alert_cache,
    load_faction_ball_alert_cache,
)
from utils.cache.fl_cache import feeling_lucky_cache, load_feeling_lucky_cache
from utils.cache.halloween_con_top_cache import (
    halloween_con_top_cache,
    load_halloween_con_top_cache,
)
from utils.cache.halloween_contest_cache import (
    halloween_contests_alert_cache,
    load_halloween_contest_alert_cache,
)
from utils.cache.held_item_cache import held_item_cache, load_held_item_cache
from utils.cache.probation_members_cache import load_probation_members_cache
from utils.cache.reminders_cache import *
from utils.cache.res_fossil_cache import (
    load_res_fossils_alert_cache,
    res_fossils_alert_cache,
)
from utils.cache.straymon_member_cache import (
    load_straymon_member_cache,
    straymon_member_cache,
)
from utils.cache.timers_cache import load_timer_cache
from utils.cache.user_alert_cache import load_user_alert_cache, user_alerts_cache
from utils.cache.user_captcha_alert_cache import (
    load_user_captcha_alert_cache,
    user_captcha_alert_cache,
)
from utils.cache.water_state_cache import fetch_latest_water_state, get_water_state
from utils.cache.wb_battle_alert_cache import (
    load_wb_battle_alert_cache,
    wb_battle_alert_cache,
)
from utils.cache.webhook_url_cache import load_webhook_url_cache
from utils.cache.weekly_goal_tracker_cache import (
    load_weekly_goal_cache,
    weekly_goal_cache,
)
from utils.loggers.pretty_logs import pretty_log


# 🐾────────────────────────────────────────────
#     💜 Load Everything in One Go
# 🐾────────────────────────────────────────────
async def load_all_caches(bot):
    """
    Centralized function to load all caches.
    Calls each cache loader in order and logs once at the end.
    """
    try:
        # ⌚ Load Timer cache
        await load_timer_cache(bot)

        # 🐥 Straymon Members cache
        await load_straymon_member_cache(bot)

        # 💠 Weekly Goal Tracker cache
        if not weekly_goal_cache:
            await load_weekly_goal_cache(bot)

        # 🍄 Held Item Users Ping cache
        await load_held_item_cache(bot)

        # 🍚 Ball Recommendation cache
        await load_ball_reco_cache(bot)

        # ⚾ User Reminders cache
        await load_user_reminders_cache(bot)

        # 💒 Boosted Channels cache
        await load_boosted_channels_cache(bot)

        # 🌊 Fetch latest waterstate
        await fetch_latest_water_state(bot)

        # 🍀 Feeling Lucky Cooldowns
        await load_feeling_lucky_cache(bot)

        # 🛡️ User Captcha Alert
        await load_user_captcha_alert_cache(bot)

        # 🦴 Research Fossils Alert
        await load_res_fossils_alert_cache(bot)

        # ⚔️ World Boss Battle Alert
        try:
            await load_wb_battle_alert_cache(bot)
        except Exception as e:
            pretty_log(
                tag="error",
                message=f"Error loading World Boss Battle Alert Cache: {e}",
                label="🥨 CENTRAL CACHE",
            )

        # 🎯 Daily Faction Ball Alert
        await load_daily_faction_ball_cache(bot)

        # 🎯 Faction Ball Alert
        await load_faction_ball_alert_cache(bot)

        # 🕒 Probation Members Cache
        await load_probation_members_cache(bot)

        # 🌐 Webhook URL Cache
        await load_webhook_url_cache(bot)

        # 🎃 Halloween Contest Alert Cache
        # await load_halloween_contest_alert_cache(bot)

        # 🎃 Halloween Con Top Cache Disabled for now
        # await load_halloween_con_top_cache(bot)

        # 🐾 Catchlist Cache
        await load_catchlist_cache(bot)

        # 🦴 User Alerts Cache
        await load_user_alert_cache(bot)

        # 🎀 Unified single-line log with all caches
        pretty_log(
            tag="",
            message=(
                f"All caches refreshed and loaded "
                f"Straymon Members: {len(straymon_member_cache)},"
                f"(Waterstate: {get_water_state()}, Timers: {len(timer_cache)}, "
                f"Weekly Goal Trackers: {len(weekly_goal_cache)}, "
                f"Held Items: {len(held_item_cache)}, Ball Recon: {len(ball_reco_cache)}, "
                f"Reminders: {len(user_reminders_cache)}, "
                f"Boosted Channels: {len(boosted_channels_cache)}, "
                f"Daily Faction Balls: {len(daily_faction_ball_cache)},"
                f"Feeling Lucky Cooldowns: {len(feeling_lucky_cache)},"
                f"Captcha Alerts: {len(user_captcha_alert_cache)},"
                f"Faction Ball Alerts: {len(faction_ball_alert_cache)},"
                f"World Boss Battle Alerts: {len(wb_battle_alert_cache)},"
                f"Res Fossils Alerts: {len(res_fossils_alert_cache)},"
                f"User Alerts: {len(user_alerts_cache)},"
                f"Probation Members: {len(probation_members_cache)},"
                f"Webhook URLs: {len(webhook_url_cache)}"
                # f"Halloween Contest Alerts: {len(halloween_contests_alert_cache)},"
                # f"Halloween Con Fourth Place Score: {halloween_con_top_cache.get('fourth_place', {}).get('score', 0)}"
            ),
            label="🥨 CENTRAL CACHE",
            bot=bot,
        )
    except Exception as e:
        pretty_log(
            tag="",
            message=f"Error loading caches: {e}",
            label="🥨 CENTRAL CACHE",
            level="error",
            bot=bot,
        )
