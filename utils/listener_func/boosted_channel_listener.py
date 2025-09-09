import re
import discord

from config.current_setup import POKEMEOW_APPLICATION_ID
from utils.database.boosted_channels_db_func import (
    delete_boosted_channel,
    insert_boosted_channel,
)
from utils.loggers.pretty_logs import pretty_log
from utils.loggers.debug_log import debug_log
from discord.ext import commands

BOOST_FOOTER_PATTERN = re.compile(r"\(\+(\d+)% ;channel boost\)")


async def handle_boosted_channel_on_edit(bot: commands.Bot, message: discord.Message):
    """
    Detect if a PokéMeow message contains a channel boost. Update cache & DB accordingly.
    Includes detailed debug logs.
    Skips processing if the boosted_channels_cache is empty.
    """
    from utils.cache.boosted_channels_cache import boosted_channels_cache

    # --- Skip entirely if cache is empty ---
    if not boosted_channels_cache:
        debug_log("Boosted channels cache is empty, skipping processing")
        return

    debug_log(f"Processing message {message.id} in channel {message.channel.id}")

    # ✅ Must be from PokéMeow bot
    if message.author.id != POKEMEOW_APPLICATION_ID:
        debug_log(f"Ignored message: author {message.author.id} is not PokéMeow")
        return

    # ✅ Must have at least one embed
    if not message.embeds:
        debug_log("Ignored message: no embeds found")
        return

    embed = message.embeds[0]

    # ✅ Must have description and "You caught a"
    if not embed.description or "You caught a" not in embed.description:
        debug_log("Ignored message: missing description or 'You caught a'")
        return

    # ✅ Must have footer with channel boost
    footer_text = embed.footer.text if embed.footer else ""
    boost_match = BOOST_FOOTER_PATTERN.search(footer_text)

    channel_id = message.channel.id
    channel_name = message.channel.name

    # If boost exists and not in cache → insert
    if boost_match:
        boost_value = int(boost_match.group(1))
        debug_log(f"Found channel boost: +{boost_value}% in footer")

        if channel_id not in boosted_channels_cache:
            boosted_channels_cache[channel_id] = channel_name
            debug_log(f"Inserting channel {channel_name} ({channel_id}) into DB")
            try:
                await insert_boosted_channel(bot, channel_id, channel_name)
            except Exception as e:
                pretty_log(
                    "error",
                    f"Failed to insert boosted channel {channel_name}: {e}",
                    bot=bot,
                )
            else:
                pretty_log(
                    "",
                    f"Detected boosted channel: {channel_name} ({channel_id}), +{boost_value}% boost, added to cache & DB",
                    bot=bot,
                )
        else:
            debug_log(f"Channel {channel_name} ({channel_id}) already in cache")
    else:
        # No boost in footer but channel is in cache → remove
        if channel_id in boosted_channels_cache:
            debug_log(
                f"Channel {channel_name} ({channel_id}) no longer boosted, removing"
            )
            boosted_channels_cache.pop(channel_id, None)
            try:
                await delete_boosted_channel(bot, channel_id)
            except Exception as e:
                pretty_log(
                    "error",
                    f"Failed to delete boosted channel {channel_name}: {e}",
                    bot=bot,
                )
            else:
                pretty_log(
                    "warn",
                    f"Channel {channel_name} ({channel_id}) no longer boosted, removed from cache & DB",
                    bot=bot,
                )
        else:
            debug_log(
                f"No boost found and channel {channel_name} not in cache, nothing to do"
            )
