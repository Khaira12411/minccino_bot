from datetime import datetime

import discord

from utils.cache.cache_list import webhook_url_cache
from utils.database.webhook_url_db import upsert_webhook_url
from utils.loggers.pretty_logs import pretty_log


async def create_webhook_func(
    bot, channel: discord.TextChannel, name: str
) -> str | None:
    try:

        avatar_bytes = await bot.user.avatar.read()
        webhook = await channel.create_webhook(name=name, avatar=avatar_bytes)
        pretty_log(
            "info",
            f"Webhook '{name}' created in channel '{channel.name}' (ID: {channel.id})",
        )
        # Store the webhook URL in the database
        await upsert_webhook_url(bot, channel, webhook.url)

    except Exception as e:
        pretty_log(
            "error",
            f"Failed to create webhook in channel '{channel.name}': {e}",
        )
    return webhook.url if webhook else None


async def send_webhook(
    bot: discord.Client,
    channel: discord.TextChannel,
    content: str = None,
    embed: discord.Embed = None,
):
    channel_id = channel.id
    webhook_url_row = webhook_url_cache.get(channel_id)
    if not webhook_url_row:
        channel_name = channel.name
        if "goal" in channel_name.lower():
            webhook_name = "Minccino Goal Tracker 🧀"
        elif "lucky" in channel_name.lower():
            webhook_name = "Minccino 🍀"
        elif "log" or "report" in channel_name.lower():
            webhook_name = "Minccino Logs 🐀"
        else:
            webhook_name = f"Minccino 🐭"
        webhook_url = await create_webhook_func(bot, channel, webhook_name)
        if not webhook_url:
            pretty_log(
                tag="info",
                message=f"⚠️ Falling back to direct channel send for channel '{channel.name}' (ID: {channel.id}) due to webhook creation failure",
                label="🌐 WEBHOOK SEND",
            )
            await channel.send(content=content, embed=embed)
            return
        # Update cache for immediate use
        webhook_url_cache[channel_id] = {
            "channel_name": channel_name,
            "url": webhook_url,
        }
        webhook_url_row = webhook_url_cache[channel_id]

    webhook_url = webhook_url_row["url"]
    if webhook_url:
        webhook = discord.Webhook.from_url(webhook_url, client=bot)
        await webhook.send(content=content, embed=embed, wait=True)
