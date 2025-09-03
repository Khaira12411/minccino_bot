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
    OKA_SERVER_ID
)
from utils.listener_func.fish_reco_ping import recommend_fishing_ball
from utils.listener_func.held_item_ping import held_item_ping_handler
from utils.listener_func.pokemon_timer import detect_pokemeow_reply
from utils.loggers.pretty_logs import pretty_log

FISHING_COLOR = 0x87CEFA


class MessageEditListener(commands.Cog):
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
    #           👂 Message Edit Listener Event
    # 💜────────────────────────────────────────────
    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        try:
            # 🚫 Ignore bots except PokeMeow, but allow webhooks
            if (
                after.author.bot
                and after.author.id != POKEMEOW_APPLICATION_ID
                and not after.webhook_id
            ):
                return
            # if after.guild and after.guild.id == ACTIVE_GUILD_ID:

            # --- Weakness chart processing (Active + Staff Guilds) ---
            if after.guild and after.guild.id in (
                ACTIVE_GUILD_ID,
                STAFF_SERVER_GUILD_ID,
                STRAYMONS_GUILD_ID,
                OKA_SERVER_ID

            ):
                # 🔹 Call recommend_ball directly
                await recommend_fishing_ball(message=after, bot=self.bot)

        except Exception as e:
            pretty_log(
                tag="critical",
                message=f"Unhandled exception in on_message_edit: {e}",
            )


# 💜────────────────────────────────────────────
#        🛠️ Setup function to add cog to bot
# 💜────────────────────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(MessageEditListener(bot))
    # espeon_log("ready", "MessageCreateListener cog loaded successfully!")
