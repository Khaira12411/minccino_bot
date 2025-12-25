# 💧────────────────────────────────────────────
#      Water State Updater on New Messages
# ─────────────────────────────────────────────

import discord
from config.current_setup import WATERSTATE_CHANNEL_ID


async def on_waterstate_message(message: discord.Message) -> str:
    """
    Call this from your on_message event.
    Updates cache if a new 'Water State' embed appears.
    Returns the current water state.
    """
    from utils.cache.water_state_cache import update_water_state , get_water_state # import your helper

    WATER_STATE_CHANNEL_ID = WATERSTATE_CHANNEL_ID
    if message.channel.id != WATER_STATE_CHANNEL_ID or not message.embeds:
        return get_water_state()

    embed = message.embeds[0]
    if embed.title and "water state" in embed.title.lower():
        embed_description = embed.description or ""
        new_state = None
        if "calm" in embed_description.lower():
            new_state = "calm"
        elif "moderate" in embed_description.lower():
            new_state = "moderate"
        elif "intense" in embed_description.lower():
            new_state = "intense"
        elif "strong" in embed_description.lower():
            new_state = "strong"
        elif "golden" in embed_description.lower():
            new_state = "special"
        return update_water_state(new_state)

    return get_water_state()
