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
from utils.listener_func.relics_listener import handle_relics_message
from utils.listener_func.waterstate_listener import on_waterstate_message
from utils.loggers.pretty_logs import pretty_log
from utils.listener_func.catchbot_listener import handle_catchbot_message

class MessageCreateListener(commands.Cog):
    # 💜────────────────────────────────────────────
    # [🟣 INIT] Cog Initialization
    # ─────────────────────────────────────────────
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # 💜────────────────────────────────────────────
    # [🟣 HELPER] Retry Discord calls on 503
    # ─────────────────────────────────────────────
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
    # [🟣 LISTENER] on_message Event
    # ─────────────────────────────────────────────
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

            # --- Weakness chart + general processing ---
            if message.guild and message.guild.id in (
                ACTIVE_GUILD_ID,
                STAFF_SERVER_GUILD_ID,
                STRAYMONS_GUILD_ID,
            ):
                # ⌚ detect PokéMeow replies
                await detect_pokemeow_reply(message)

                # 🐚 Held item ping
                await held_item_ping_handler(self.bot, message)

                # 🥎 Recommend ball
                await recommend_ball(message, self.bot)

                # 🧪 Debug: Relics processing
                await handle_relics_message(bot=self.bot, message=message)

                # 🧪 Debug: Catchbot processing
                await handle_catchbot_message(bot=self.bot, message=message)

            # 🌊 Waterstate channel processing ---
            if message.channel.id == WATERSTATE_CHANNEL_ID:
                await on_waterstate_message(message)

        except Exception as e:
            pretty_log(
                tag="critical",
                message=f"Unhandled exception in on_message: {e}",
            )


# 💜────────────────────────────────────────────
# [🟣 SETUP] Add Cog to Bot
# ─────────────────────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(MessageCreateListener(bot))
    # espeon_log("ready", "MessageCreateListener cog loaded successfully!")
