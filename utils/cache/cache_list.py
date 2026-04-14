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
