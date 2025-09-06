# utils/cache/boosted_channels_cache.py
import copy
from utils.database.boosted_channels_db_func import fetch_all_boosted_channels
from utils.loggers.pretty_logs import pretty_log

# channel_id -> channel_name
boosted_channels_cache: dict[int, str] = {}


async def load_boosted_channels_cache(bot):
    """
    Load all boosted channels into memory.
    """
    boosted_channels_cache.clear()
    try:
        rows = await fetch_all_boosted_channels(bot)
        for row in rows:
            channel_id = row["channel_id"]
            channel_name = row["channel_name"]
            boosted_channels_cache[channel_id] = channel_name

        pretty_log(
            tag="",
            label="💒 BOOSTED CHANNELS",
            message=f"Loaded {len(boosted_channels_cache)} boosted channels into cache.",
            bot=bot,
        )
    except Exception as e:
        pretty_log("error", f"Failed to load boosted channels cache: {e}", bot=bot)

    return copy.deepcopy(boosted_channels_cache)
