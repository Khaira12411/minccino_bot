import re
from datetime import datetime

import discord

from group_func.toggle.reminders.reminders_sched_db_func import (
    mark_reminder_sent,
    update_catchbot_reminds_next_on,
)
from utils.cache.reminders_cache import user_reminders_cache
from utils.loggers.pretty_logs import pretty_log

CC_BOT_LOG_ID = 1413576563559239931
TIMESTAMP_REGEX = re.compile(r"<t:(\d+):f>")


# 🍭 Get a registered personal channel
async def get_registered_personal_channel(
    bot: discord.Client, user_id: int
) -> int | None:
    async with bot.pg_pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT channel_id FROM personal_channels WHERE user_id = $1", user_id
        )
        return row["channel_id"] if row else None


async def handle_reminder_embed(bot: discord.Client, message: discord.Message):
    """
    Hooked to on_message.
    Reads embeds sent by pokemon_reminder_checker in CC_BOT_LOG_ID,
    parses the fields, and sends notifications to the user.
    """

    # Only process embeds from the bot in the specific channel
    if (
        message.channel.id != CC_BOT_LOG_ID
        or not message.embeds
        or not message.author.bot
    ):
        return

    for embed in message.embeds:
        # Parse embed fields into a dict
        embed_fields = {field.name: field.value for field in embed.fields}

        try:
            reminder_type = embed_fields.get("Reminder Type", "").lower()
            user_mention = embed.description or ""
            user_id = int(re.sub(r"\D", "", user_mention))  # extract ID safely
            ends_on_field = embed_fields.get("Ends on")
            next_on_field = embed_fields.get("Next catchbot check")
            reminder_id = embed_fields.get("Reminder ID")

            # Extract timestamps
            ends_on_ts = (
                int(TIMESTAMP_REGEX.search(ends_on_field).group(1))
                if ends_on_field
                else None
            )
            next_on_ts = (
                int(TIMESTAMP_REGEX.search(next_on_field).group(1))
                if next_on_field
                else None
            )

        except Exception as e:
            pretty_log("warn", f"Failed to parse embed: {e}", bot=bot)
            continue

        # Fetch user object
        user = bot.get_user(user_id)
        if not user:
            continue

        # Decide target channel: try personal channel first, fallback to DM
        channel_id = await get_registered_personal_channel(bot, user_id)
        target_channel = (
            bot.get_channel(channel_id)
            if channel_id
            else user.dm_channel or await user.create_dm()
        )

        if not target_channel:
            continue

        # Send notification based on reminder type
        if reminder_type == "catchbot":
            await target_channel.send(
                f"{user.mention}, your catchbot needs attention! "
                f"Next return: <t:{next_on_ts}:f>"
                if next_on_ts
                else ""
            )

            # Repeating logic
            if next_on_ts and next_on_ts > 0:
                # Calculate repeating interval from cache if available
                repeating = (
                    user_reminders_cache.get(user_id, {})
                    .get("catchbot", {})
                    .get("repeating", 0)
                )
                await update_catchbot_reminds_next_on(
                    bot, user_id, minutes=repeating, ends_on=ends_on_ts
                )
            else:
                # Non-repeating: mark reminder sent
                await mark_reminder_sent(bot, reminder_id)

        elif reminder_type == "relics":
            await target_channel.send(
                f"{user.mention}, your relics exchange effect has already expired."
            )

        # Clear cache after sending
        if user_id in user_reminders_cache:
            del user_reminders_cache[user_id]
