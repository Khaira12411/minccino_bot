# 💧────────────────────────────────────────────
#          Water State Helper
# ─────────────────────────────────────────────

import discord

from config.current_setup import WATERSTATE_CHANNEL_ID
from utils.loggers.pretty_logs import pretty_log

# Centralized cache
waterstate_cache: dict[str, str] = {"value": "strong"}  # initial default value


def update_water_state(new_state: str):
    """
    Update the cached water state manually.
    """
    lower_state = new_state.lower()

    if "calm" in lower_state:
        new_state = "calm"
    elif "strong" in lower_state:
        new_state = "strong"
    elif "moderate" in lower_state:
        new_state = "moderate"
    elif "intense" in lower_state:
        new_state = "intense"
    elif "golden" in lower_state:
        new_state = "special"

    old_state = waterstate_cache.get("value", "strong")
    waterstate_cache["value"] = new_state
    pretty_log(
        message=f"Water State updated from '{old_state}' to '{new_state}'",
        label="💧 WATER STATE",
        bot=None,
    )
    return waterstate_cache["value"]


def get_water_state() -> str:
    """
    Returns the current cached water state.
    """
    return waterstate_cache.get("value", "strong")


async def fetch_latest_water_state(bot: discord.Client):
    """
    Fetch the most recent 'Water State' embed from a predefined channel
    and update the waterstate_cache.
    """
    channel = bot.get_channel(WATERSTATE_CHANNEL_ID)
    if not channel:
        return get_water_state()

    async for msg in channel.history(limit=50):
        if not msg.embeds:
            continue
        embed = msg.embeds[0]
        if embed.title and "water state" in embed.title.lower():
            return update_water_state(embed.description or "strong")

    # Fallback if none found
    return get_water_state()
