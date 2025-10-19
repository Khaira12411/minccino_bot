import re

import discord

from utils.cache.halloween_con_top_cache import halloween_con_top_cache
from utils.cache.halloween_contest_cache import halloween_contests_alert_cache
from utils.database.hallowen_contest_top_db import upsert_halloween_con_top
from utils.essentials.pokemeow_helpers import get_pokemeow_reply_member
from utils.loggers.pretty_logs import pretty_log

processed_halloween_score_message_ids = set()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🎃 Halloween Contest Embed Listener
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def halloween_contest_embed_listener(bot, message: discord.Message):
    """
    Listen for Halloween Contest embeds and update the top scores cache and database.
    """
    try:
        if not message.embeds:
            return

        embed = message.embeds[0]
        rank4_score = None

        # Search all fields for Rank 4 score
        for field in embed.fields:
            match = re.search(r"`Rank 4`\s*([\d,]+)", field.value)
            if match:
                rank4_score = int(match.group(1).replace(",", ""))
                pretty_log("info", f"🎃 Found Rank 4 score: {rank4_score}")
                # You can now use rank4_score, e.g. update cache/db
                # await upsert_halloween_con_top(bot, "Rank 4", rank4_score)
                break

        if rank4_score is None:
            pretty_log("debug", "🎃 Rank 4 score not found in embed fields.")
            return

        # Check existing cached score
        cached_score = halloween_con_top_cache.get("fourth_place", {}).get("score", 0)
        if rank4_score != cached_score:
            # Update database and cache (cache update happens in upsert function)
            await upsert_halloween_con_top(bot, "fourth_place", rank4_score)
            pretty_log(
                "info",
                f"🎃 Updated Halloween Contest Rank 4 score from {cached_score} to {rank4_score}",
            )
        else:
            pretty_log(
                "info",
                f"🎃 Halloween Contest Rank 4 score unchanged at {rank4_score}",
            )
            return

    except Exception as e:
        pretty_log("error", f"Failed to parse Halloween Contest embed: {e}")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🎃 Halloween Contest Score Listener
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def halloween_contest_score_listener(
    bot, before_message: discord.Message, message: discord.Message
):
    """
    Listen for Halloween Contest score announcements and notify users based on their alert settings.
    """
    try:
        member = await get_pokemeow_reply_member(before_message)
        if not member:
            return

        # Early check if user is in cache or has their alert off
        user_halloween_con_alert_info = halloween_contests_alert_cache.get(member.id)
        if not user_halloween_con_alert_info:
            return
        notify_settings = user_halloween_con_alert_info.get("notify", "off")
        if notify_settings == "off":
            return

        if message.id in processed_halloween_score_message_ids:
            return
        processed_halloween_score_message_ids.add(message.id)

        # Extract score from message content
        score = None
        match = re.search(r"score of \*\*([\d,]+)\*\*", message.content)
        if match:
            score = int(match.group(1).replace(",", ""))
            pretty_log(
                "info",
                f"🎃 Halloween Contest: {member.display_name} earned a score of {score}",
            )
            # You can now use the score variable as needed (e.g., notify, update cache, etc.)
        else:
            pretty_log(
                "debug", f"🎃 No score found in message content: {message.content!r}"
            )
            return

        # Compare the fourth place score from cache with score
        fourth_place_score = halloween_con_top_cache.get("fourth_place", {}).get(
            "score", 0
        )
        if score > fourth_place_score:
            # Notify user based on their alert settings
            if notify_settings == "on":
                notification = f"🎃 Congratulations {member.mention}! Your Halloween Contest score of **{score:,}** has exceeded the current Rank 4 score of **{fourth_place_score:,}**!"
            elif notify_settings == "on_no_pings":
                notification = f"🎃 Congratulations {member.display_name}! Your Halloween Contest score of **{score:,}** has exceeded the current Rank 4 score of **{fourth_place_score:,}**!"
            else:
                pretty_log(
                    "debug",
                    f"🎃 Unknown notify setting '{notify_settings}' for user {member.display_name}",
                )
                return

            await message.channel.send(notification)
            pretty_log(
                "info",
                f"🎃 Sent Halloween Contest notification to {member.display_name}",
            )
        else:
            pretty_log(
                "info",
                f"🎃 No notification sent. User {member.display_name}'s score of {score} did not exceed Rank 4 score of {fourth_place_score}.",
            )

    except Exception as e:
        pretty_log("error", f"Failed to process Halloween Contest score message: {e}")
