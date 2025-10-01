import discord
from discord.ext import commands

from config.aesthetic import Emojis
from config.current_setup import MINCCINO_COLOR
from utils.database.captcha_alert_db_func import *
from utils.embeds.design_embed import design_embed
from utils.essentials.loader.pretty_defer import *
from utils.loggers.pretty_logs import pretty_log
from config.aesthetic import *

# 🐾────────────────────────────────────────────
#   🛡️ Captcha Alert Settings Handler
# ─────────────────────────────────────────────
async def captcha_alert_settings_func(
    bot: commands.Bot, interaction: discord.Interaction, alert_type: str
):
    """
    Handles updating a user's captcha alert preference in the database
    and sends a confirmation embed with Minccino aesthetic.
    """

    # User Info
    user = interaction.user
    user_id = user.id
    user_name = user.name

    handler = await pretty_defer(
        interaction=interaction,
        content="Updating your captcha alert settings...",
        ephemeral=False,
    )

    # Upsert into DB
    await upsert_user_captcha_alert(bot, user_id, user_name, alert_type.lower())

    # Confirmation Embed
    embed = discord.Embed(
        title=f"{Emojis.gray_shield} Captcha Alert Settings Updated",
        description=f"**Alert Type:** {alert_type}",
        color=MINCCINO_COLOR,
    )
    embed = design_embed(
        embed=embed,
        user=user,
        thumbnail_url=MINC_Thumbnails.captcha_alert,
    )
    await handler.success(content="", embed=embed)
