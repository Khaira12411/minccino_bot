import asyncio
import re
from datetime import datetime, timedelta

import discord
from discord.ext import commands

from config.aesthetic import *
from config.aesthetic import Emojis
from config.current_setup import MINCCINO_COLOR, POKEMEOW_APPLICATION_ID
from config.straymons_constants import STRAYMONS__ROLES
from utils.essentials.pokemeow_helpers import get_pokemeow_reply_member
from utils.loggers.pretty_logs import pretty_log

CAPTCHA_HELPER_MENTION = f"<@&{STRAYMONS__ROLES.captcha_helper}>"


# 🛡️────────────────────────────────────────────
#   Captcha Alert Handler
# 🛡️────────────────────────────────────────────
async def captcha_alert_handler(bot: commands.Bot, message: discord.Message):
    """
    Handles messages from PokeMeow bot and alerts users/helpers
    based on their captcha alert settings.
    """

    try:
        if message.author.id != POKEMEOW_APPLICATION_ID:
            return

        # 🚫 Skip if it's not a captcha (content, embed title, or embed description)
        if message.embeds:
            embed = message.embeds[0]
            if not (
                (embed.title and "captcha" in embed.title.lower())
                or (embed.description and "captcha" in embed.description.lower())
            ):
                return

        guild = message.guild
        #
        member = await get_pokemeow_reply_member(message=message)
        if not member:
            return

        # Check cache for users with captcha alert enabled
        from utils.cache.user_captcha_alert_cache import fetch_user_captcha_alert_cache

        member_id = member.id

        captcha_alert_info = fetch_user_captcha_alert_cache(user_id=member_id)
        if not captcha_alert_info:
            pretty_log(
                "info",
                f"Skipping ...  {member.display_name} not in captcha alert cache",
                label="🛡️ Captcha Alert",
            )
            return

        notify = (captcha_alert_info.get("notify") or "off").lower()
        content = ""
        if notify == "off":
            pretty_log(
                "info",
                f"Skipping ...  {member.display_name} has turned off captcha alerts",
                label="🛡️ Captcha Alert",
            )
            return

        elif notify == "on":
            content = f"{member.mention} a CAPTCHA has appeared! Please solve it to avoid getting banned!"

        else:
            content = f"{CAPTCHA_HELPER_MENTION}! {member.mention} has a spawned a CAPTCHA! Please assist them in solving it!"

        await message.channel.send(content=content)

        pretty_log(
            "success",
            f" Sent captcha alert for {member.display_name}",
            label="🛡️ Captcha Alert",
        )

    except Exception as e:
        pretty_log(
            tag="critical",
            message=f"Unhandled exception in captcha_alert_handler: {e}",
            label="🛡️ Captcha Alert",
            bot=bot,
        )
