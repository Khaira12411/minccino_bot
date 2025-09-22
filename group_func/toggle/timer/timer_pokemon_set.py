# 🟣────────────────────────────────────────────
#        💜 Timer Pokemon Function 💜
# ─────────────────────────────────────────────
from datetime import datetime

import discord
from discord.ext import commands

from config.aesthetic import Emojis
from config.current_setup import MINCCINO_COLOR
from group_func.toggle.timer.timer_db_func import fetch_timer, set_timer
from utils.embeds.design_embed import design_embed
from utils.essentials.loader.pretty_defer import *
from utils.loggers.pretty_logs import pretty_log

thumbnail_url = "https://media.discordapp.net/attachments/1411503395310669885/1411503494149570672/chronometer_1.png?ex=68b4e491&is=68b39311&hm=8751fcc4bc4f0f1bce8090b48d5301e3ffdac147285baa0959e96b4b0b77d85c&=&format=webp&quality=lossless&width=576&height=576"


async def timer_set_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
    type: str,
    mode: str,
):
    from utils.cache.timers_cache import load_timer_cache

    handler = await pretty_defer(
        interaction=interaction, content=f"Updating your {type} timer ...."
    )
    # 🐾 Grab the user info
    user = interaction.user
    user_id = user.id
    user_name = user.name

    if type == "Pokemon":
        # 💾 Update the Pokemon timer setting in DB
        await set_timer(
            bot=bot, user_id=user_id, pokemon_setting=mode, user_name=user_name
        )
        pretty_log(
            tag="db",
            message=f"Set Pokemon timer for {user} to {mode}",
        )
    elif type == "Battle":
        if mode != "React":
            # 💾 Update the Battle timer setting in DB
            await set_timer(
                bot=bot, user_id=user_id, battle_setting=mode, user_name=user_name
            )
            pretty_log(
                tag="db",
                message=f"Set Battle timer for {user} to {mode}",
            )
        else:
            await handler.error(content="You can't set the battle timer to React")

    # 🌸 Prepare confirmation embed
    embed = discord.Embed(
        title=f"{Emojis.timer} Timer Setting Updated",
        description=f"**{type.title()}:** {mode.title()}",
    )
    embed = design_embed(embed=embed, user=user, thumbnail_url=thumbnail_url)
    # ✨ Send as ephemeral interaction response
    try:
        await handler.success(content="", embed=embed)
        pretty_log(
            tag="info",
            message=f"Sent Pokemon timer confirmation to {user}",
        )
        await load_timer_cache(bot)

    except Exception as e:
        # ⚠️ Log any errors
        pretty_log(
            tag="error",
            message=f"Failed to send Pokemon timer confirmation for {user_id}: {e}",
        )
