# 🟣────────────────────────────────────────────
#           💜 Message Create Listener Cog 💜
# ─────────────────────────────────────────────

import asyncio

import discord
from discord.ext import commands

from config.current_setup import (
    ACTIVE_GUILD_ID,
    MINCCINO_APP_ID,
    POKEMEOW_APPLICATION_ID,
    STAFF_SERVER_GUILD_ID,
    STRAYMONS_GUILD_ID,
    WATERSTATE_CHANNEL_ID,
)
from utils.listener_func.ball_reco_ping import recommend_ball
from utils.listener_func.held_item_ping import held_item_ping_handler
from utils.listener_func.pokemon_timer import detect_pokemeow_reply
from utils.listener_func.waterstate_listener import on_waterstate_message
from utils.loggers.pretty_logs import pretty_log


class MessageCreateListener(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # 💜 Helper: Retry Discord calls on 503
    async def retry_discord_call(self, func, *args, retries=3, delay=2, **kwargs):
        for attempt in range(1, retries + 1):
            try:
                return await func(*args, **kwargs)
            except discord.HTTPException as e:
                if e.status == 503:
                    pretty_log(
                        tag="warn",
                        message=f"HTTP 503 error on attempt {attempt}. Retrying in {delay}s...",
                    )
                    if attempt < retries:
                        await asyncio.sleep(delay)
                        continue
                    else:
                        raise
                else:
                    raise

    # 💜────────────────────────────────────────────
    #           👂 Message Listener Event
    # 💜────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        try:
            # 🚫 Ignore bots except PokeMeow, but allow webhooks
            if (
                message.author.bot
                and message.author.id != POKEMEOW_APPLICATION_ID
                and not message.webhook_id
            ):
                return
            # if message.guild and message.guild.id == ACTIVE_GUILD_ID:

            # --- Weakness chart processing (Active + Staff Guilds) ---
            if message.guild and message.guild.id in (
                ACTIVE_GUILD_ID,
                STAFF_SERVER_GUILD_ID,
                STRAYMONS_GUILD_ID,
            ):
                await detect_pokemeow_reply(message)
                await held_item_ping_handler(self.bot, message)
                # 🔹 Call recommend_ball directly
                await recommend_ball(message, self.bot)
            if message.channel.id == WATERSTATE_CHANNEL_ID:
                current_state = await on_waterstate_message(message)
        except Exception as e:
            pretty_log(
                tag="critical",
                message=f"Unhandled exception in on_message: {e}",
            )


# 💜────────────────────────────────────────────
#        🛠️ Setup function to add cog to bot
# 💜────────────────────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(MessageCreateListener(bot))
    # espeon_log("ready", "MessageCreateListener cog loaded successfully!")
