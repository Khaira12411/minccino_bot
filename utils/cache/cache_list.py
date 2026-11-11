# 💫━━━━━━━━━━━━━━━━━━━━━━━━━
#       🌸 Processed Messages 🌸
# 💫━━━━━━━━━━━━━━━━━━━━━━━━━

processed_catchlist_sz_catches: set[tuple[int, int | None, str]] = set()
processed_spawn_messages = set()
processed_caught_catchlist_messages = set()
processed_pin_numbers_messages = set()


def clear_processed_messages_cache():
    processed_catchlist_sz_catches.clear()
    processed_spawn_messages.clear()
    processed_caught_catchlist_messages.clear()


# 🌸_________________________________________________________
# ⌚ Timer Cache (Global)
# _________________________________________________________
timer_cache: dict[int, dict[str, str]] = {}
# Structure:
# timer_cache = {
#     401435956780990484: {
#         "user_name": "Some Name",
#         "pokemon_setting": "Some Value",
#         "fish_setting": "Some Value",
#         "battle_setting": "Some Value",
#     },

probation_members_cache: dict[int, dict[str, str]] = {}
#  Structure:
# probation_members = {
#     user_id: {
#         "user_name": str,
#         "status": str,
#     }
# 💫━━━━━━━━━━━━━━━━━━━━━━━━━
#       🌸 Webhook URL Cache 🌸
# 💫━━━━━━━━━━━━━━━━━━━━━━━━━
webhook_url_cache: dict[int, dict] = {}
# Structure:
# {
#   channel_id: {
#       "channel_name": str,
#       "url": str,
#   },
#   ...

not_battle_timer_user_cache: set[str] = set()
battle_timer_users_cache: dict[str, str] = {}

# Structure:
# battle_timer_users_cache = {
#    "user_name" : str,
#    ...
# }

# 💫━━━━━━━━━━━━━━━━━━━━━━━━━
#       🌸 Catchlist Cache 🌸
# 💫━━━━━━━━━━━━━━━━━━━━━━━━━
catchlist_cache: dict[int, dict] = {}
# Structure:
# user_id -> {
#   "user_name": str,
#   "catchlist_date": str,
#   "catchlist_mons": list[dict],
#   "rank_name": str | None,
#   "total_exp": int | None,
#   "exp_needed": int | None
# }
# 💫━━━━━━━━━━━━━━━━━━━━━━━━━
#       🌸 User Alerts Cache 🌸
# 💫━━━━━━━━━━━━━━━━━━━━━━━━━
user_alerts_cache: dict[int, dict[str, dict[str, str]]] = {}
# Structure:
# {
#   user_id: {
#     alert_type: {
#       "user_name": str,
#       "notify": str
#     },
#     ...
#   },
#   ...
# }
