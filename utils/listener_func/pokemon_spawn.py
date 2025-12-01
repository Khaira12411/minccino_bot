import re

import discord

from config.aesthetic import Emojis_Balls
from config.fish_rarity import FISH_RARITY
from utils.cache.boosted_channels_cache import boosted_channels_cache
from utils.cache.daily_fa_ball_cache import daily_faction_ball_cache
from utils.cache.faction_ball_alert_cache import faction_ball_alert_cache
from utils.cache.straymon_member_cache import straymon_member_cache
from utils.cache.water_state_cache import get_water_state, update_water_state
from utils.essentials.pokemeow_helpers import get_pokemeow_reply_member
from utils.listener_func.catch_rate import *
from utils.loggers.debug_log import debug_log, enable_debug
from utils.loggers.pretty_logs import pretty_log

processed_pokemon_spawns = set()
FISHING_COLOR = 0x87CEFA  # sky blue
HALLOWEEN_COLOR = 0xFFA500  # orange
EVENT_EXCL_COLOR = 0xEA260B  # red
embed_rarity_color = {
    "common": 546299,
    "uncommon": 1291495,
    "rare": 16484616,
    "superrare": 16315399,
    "legendary": 10487800,
    "shiny": 16751052,
    "golden": 14940164,
}
