# 🟣────────────────────────────────────────────
#        💜 FL settings function 💜
# ─────────────────────────────────────────────
from datetime import datetime

import discord
from discord.ext import commands

from config.aesthetic import Emojis
from config.current_setup import MINCCINO_COLOR
from utils.database.fl_reminders_db_func import *
from utils.embeds.design_embed import design_embed
from utils.essentials.loader.pretty_defer import *
from utils.loggers.pretty_logs import pretty_log

thumbnail_url = "https://media.discordapp.net/attachments/1411503395310669885/1411503494149570672/chronometer_1.png?ex=68b4e491&is=68b39311&hm=8751fcc4bc4f0f1bce8090b48d5301e3ffdac147285baa0959e96b4b0b77d85c&=&format=webp&quality=lossless&width=576&height=576"


async def feeling_lucky_reminder_update_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
    type: str,
):
    # 🌸 Banner log
    pretty_log(
        tag="info",
        message=f"💜 User {interaction.user} ({interaction.user.id}) is updating FL reminder type to '{type}'",
        label="🍀 FL REMINDER",
        bot=bot,
    )

    handler = await pretty_defer(
        interaction=interaction,
        content=f"Updating your Feeling Lucky reminder type....",
    )

    # 🐾 Grab the user info
    user = interaction.user
    user_id = user.id
    user_name = user.name

    try:
        # 🔹 Update DB
        await update_fl_reminder_type(
            bot=bot, user_id=user_id, reminder_type=type.lower()
        )

        # 🌸 Confirmation embed
        embed = discord.Embed(
            title=f"{Emojis.timer} Feeling Lucky Reminder Setting Updated",
            description=f"**Type:** {type}",
            color=MINCCINO_COLOR,
        )
        embed = design_embed(embed=embed, user=user, thumbnail_url=thumbnail_url)

        await handler.success(content="", embed=embed)

        # ✅ Pretty log success
        pretty_log(
            tag="success",
            message=f"💚 Successfully updated FL reminder for {user} ({user_id}) to '{type}'",
            label="🍀 FL REMINDER",
            bot=bot,
        )

    except Exception as e:
        # ❌ Pretty log error
        pretty_log(
            tag="error",
            message=f"❌ Failed to update FL reminder for {user} ({user_id}): {e}",
            label="🍀 FL REMINDER",
            bot=bot,
            include_trace=True,
        )
        await handler.error(content=f"Failed to update reminder. Please try again.")
