import discord

from utils.listener_func.berry_water_listener import (
    handle_berry_water_message,
    handle_mulch_message,
)
from utils.loggers.pretty_logs import pretty_log
from utils.loggers.debug_log import debug_log, enable_debug
from utils.listener_func.faction_ball_alert import faction_ball_alert

async def test_message_listener(bot: discord.Client, message: discord.Message):
    if not message.reference or not message.reference.message_id:
        return
    replied_message = await message.channel.fetch_message(message.reference.message_id)
    if not replied_message:
        debug_log(
            f"Failed to fetch replied message with ID {message.reference.message_id} in channel {message.channel.id}"
        )
        return
    replied_message_content = getattr(replied_message, "content", "")
    debug_log(f"Fetched replied message content: '{replied_message_content}'")

    # 💜────────────────────────────────────────────
    #          🧑‍🌾 Message Variables
    # 💜────────────────────────────────────────────
    content = message.content
    first_embed = replied_message.embeds[0] if replied_message.embeds else None
    first_embed_author = (
        first_embed.author.name
        if first_embed and first_embed.author
        else ""
    )
    first_embed_description = (
        first_embed.description
        if first_embed and first_embed.description
        else ""
    )
    first_embed_footer = (
        first_embed.footer.text
        if first_embed and first_embed.footer
        else ""
    )
    # 💜────────────────────────────────────────────
    #          🧑‍🌾 Berry Water Listener
    # 💜────────────────────────────────────────────
    if message.content:
        if (
            "Watered" in replied_message_content
            and "Next stage" in replied_message_content
        ):
            pretty_log(
                "info",
                "Detected Berry Water message, processing berry water reminders...",
            )
            await handle_berry_water_message(bot=bot, message=replied_message)
    # 💜────────────────────────────────────────────
    #          🧑‍🌾  Mulch Listener
    # 💜────────────────────────────────────────────
    if message.content:
        if (
            "Applied" in replied_message_content
            and "Mulch" in replied_message_content
            and "to Slot" in replied_message_content
        ):
            pretty_log(
                "info",
                "Detected Mulch message, processing growth mulch reminders...",
            )
            await handle_mulch_message(bot=bot, message=replied_message)

    # 💜────────────────────────────────────────────
    #          🧑‍🌾 Faction Ball Alert
    # 💜────────────────────────────────────────────
    # Faction Ball Alert
    if first_embed:
        if (
            first_embed.description
            and "<:team_logo:" in first_embed.description
            and "found a wild" in first_embed.description
        ):
            await faction_ball_alert(before=message, after=message)
