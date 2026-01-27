import discord

from utils.cache.cache_list import webhook_url_cache
from utils.database.webhook_url_db import fetch_all_webhook_urls
from utils.loggers.pretty_logs import pretty_log


async def load_webhook_url_cache(bot: discord.Client):
    """
    Loads all webhook URLs from the database into the cache.
    """
    webhook_url_cache.clear()
    webhook_urls = await fetch_all_webhook_urls(bot)
    webhook_url_cache.update(webhook_urls)

    pretty_log(
        tag="cache",
        message=f"Loaded {len(webhook_url_cache)} webhook URLs into cache",
        label="🌐 WEBHOOK URL CACHE",

    )
    return webhook_url_cache


def upsert_webhook_url_in_cache(
    channel: discord.TextChannel,
    webhook_url: str,
):
    """
    Upserts a webhook URL into the cache.
    """
    channel_id = channel.id
    channel_name = channel.name
    webhook_url_cache[channel_id] = {
        "channel_name": channel_name,
        "url": webhook_url,
    }
    pretty_log(
        tag="cache",
        message=f"Upserted webhook URL for channel '{channel_name}' (ID: {channel_id}) into cache",
        label="🌐 WEBHOOK URL CACHE",

    )


def remove_webhook_url_from_cache(channel: discord.TextChannel):
    """
    Removes a webhook URL from the cache.
    """
    channel_id = channel.id
    channel_name = channel.name
    if channel_id in webhook_url_cache:
        del webhook_url_cache[channel_id]
        pretty_log(
            tag="cache",
            message=f"Removed webhook URL for channel '{channel_name}' (ID: {channel_id}) from cache",
            label="🌐 WEBHOOK URL CACHE",

        )
