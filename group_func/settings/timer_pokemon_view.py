# 🟣────────────────────────────────────────────
#        Timer Pokemon View Function
# 🟣────────────────────────────────────────────

import discord
from discord.ext import commands

from config.aesthetic import Emojis
from config.current_setup import MINCCINO_COLOR
from group_func.toggle.timer.timer_db_func import fetch_timer
from utils.embeds.design_embed import design_embed
from utils.loggers.pretty_logs import pretty_log

thumbnail_url = "https://media.discordapp.net/attachments/1411503395310669885/1411503494149570672/chronometer_1.png?ex=68b4e491&is=68b39311&hm=8751fcc4bc4f0f1bce8090b48d5301e3ffdac147285baa0959e96b4b0b77d85c&=&format=webp&quality=lossless&width=576&height=576"


async def timer_pokemon_settings_func(bot: commands.Bot, interaction: discord.Interaction):
    """
    Show the user's current Pokemon timer settings in a cute embed.
    """
    user = interaction.user
    user_id = user.id

    # Fetch user's timer settings from DB
    timer_data = await fetch_timer(bot, user_id)
    if not timer_data:
        timer_data = {"pokemon_setting": "Not set yet"}

    pokemon_setting = timer_data.get("pokemon_setting", "Not set yet")
    # 🌸 Build embed
    embed = discord.Embed(
        title=f"{Emojis.timer} Timer Settings",
        description=f"> - **Pokemon:** {pokemon_setting.title()}",
        color=MINCCINO_COLOR,
    )
    embed = design_embed(embed=embed, user=user, thumbnail_url=thumbnail_url)

    # Send ephemeral interaction response
    try:
        await interaction.response.send_message(embed=embed)
        pretty_log(
            tag="info",
            message=f"Displayed Pokemon timer settings for {user.display_name}: {pokemon_setting}",
        )
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to send Pokemon timer view for user {user.display_name}: {e}",
        )
