import asyncio
import re
from datetime import datetime, timedelta

import discord
from discord.ext import commands

from config.aesthetic import *
from config.aesthetic import Emojis
from config.current_setup import MINCCINO_COLOR, POKEMEOW_APPLICATION_ID
from config.straymons_constants import STRAYMONS__ROLES
from utils.database.fl_cd_db_func import upsert_feeling_lucky_cd
from utils.database.fl_reminders_db_func import *
from utils.essentials.pokemeow_helpers import get_pokemeow_reply_member
from utils.loggers.pretty_logs import pretty_log


# 🍀────────────────────────────────────────────
#   Function: feeling_lucky_cd
#   Handles Pokémon find cooldowns per user
# 🍀────────────────────────────────────────────
async def feeling_lucky_cd(bot: commands.Bot, message: discord.Message):
    try:
        if message.author.id != POKEMEOW_APPLICATION_ID:
            return

        # 🚫 Skip if it's a captcha (content, embed title, or embed description)
        if "captcha" in message.content.lower():
            pretty_log(
                "info",
                f"Skipped cooldown — captcha detected in message content",
                label="🍀 FEELING LUCKY CD",
                bot=bot,
            )
            return

        if message.embeds:
            embed = message.embeds[0]
            if (embed.title and "captcha" in embed.title.lower()) or (
                embed.description and "captcha" in embed.description.lower()
            ):
                pretty_log(
                    "info",
                    f"Skipped cooldown — captcha detected in embed",
                    label="🍀 FEELING LUCKY CD",
                    bot=bot,
                )
                return

        # ✅ Normal handling continues here
        match = re.search(r"\*\*(.+?)\*\* found a wild", message.content)
        if not match:
            return

        guild = message.guild

        member = await get_pokemeow_reply_member(message=message)
        if not member:
            return

        await upsert_feeling_lucky_cd(
            bot=bot, user_id=member.id, user_name=member.display_name
        )

        fl_reminder_info = await fetch_fl_reminder_db(bot=bot, user_id=member.id)
        if not fl_reminder_info:
            await upsert_fl_reminder_db(
                bot=bot, user_id=member.id, user_name=member.name
            )

        fl_cd_role = guild.get_role(STRAYMONS__ROLES.fl_cd)
        if fl_cd_role:
            await member.add_roles(fl_cd_role)

        cooldown_time = datetime.now() + timedelta(hours=6)
        desc = (
            f"{Emojis.lucky_cheese} {member.mention}, you can use ;find here again "
            f"<t:{int(cooldown_time.timestamp())}:R>.\n"
            "Type /cooldowns to check your cooldowns."
        )
        embed = discord.Embed(description=desc, color=MINCCINO_COLOR)
        await message.channel.send(embed=embed)

        pretty_log(
            "info",
            f"Sent feeling lucky cooldown notification to {member.display_name}",
            label="🍀 FEELING LUCKY CD",
            bot=bot,
        )

    except Exception as e:
        pretty_log(
            tag="critical",
            message=f"Unhandled exception in feeling_lucky_cd: {e}",
            label="🍀 FEELING LUCKY CD",
            bot=bot,
        )
