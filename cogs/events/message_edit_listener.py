# 🟣────────────────────────────────────────────
#           💜 Message Create Listener Cog 💜
# ─────────────────────────────────────────────

import asyncio

import discord
from discord.ext import commands

from config.current_setup import (
    ACTIVE_GUILD_ID,
    MINCCINO_APP_ID,
    OKA_SERVER_ID,
    POKEMEOW_APPLICATION_ID,
    STAFF_SERVER_GUILD_ID,
    STRAYMONS_GUILD_ID,
)
from config.straymons_constants import STRAYMONS__TEXT_CHANNELS
from utils.listener_func.battle_won_listener import battle_won_listener
from utils.listener_func.boosted_channel_listener import handle_boosted_channel_on_edit
from utils.listener_func.fish_reco_ping import recommend_fishing_ball
from utils.listener_func.fl_rs import fl_rs_checker
from utils.listener_func.held_item_ping import held_item_ping_handler
from utils.listener_func.pokemon_caught import pokemon_caught_listener
from utils.listener_func.pokemon_timer import detect_pokemeow_reply
from utils.loggers.pretty_logs import pretty_log
from utils.listener_func.weekly_stats_syncer import weekly_stats_syncer
from utils.listener_func.explore_caught_listener import explore_caught_listener
FISHING_COLOR = 0x87CEFA

weekly_stats_trigger = "**Clan Weekly Stats — Straymons**"
explore_trigger = ":stopwatch: Your explore session has ended!"
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
                OKA_SERVER_ID,
                1154753039685660793,
            ):
                # 🔹 Fishing reco ball
                await recommend_fishing_ball(message=after, bot=self.bot)

                # Boosted Channel Listener
                await handle_boosted_channel_on_edit(bot=self.bot, message=after)

                # Process Pokemon or fish caught for Weekly Goal Tracker
                if after.embeds:
                    embed_description = after.embeds[0].description or ""
                    if embed_description and "You caught a" in embed_description:
                        await pokemon_caught_listener(
                            bot=self.bot, before_message=before, message=after
                        )

                #Process for Clan Weekly Stats
                if after.embeds:
                    embed_title = after.embeds[0].title or ""
                    if weekly_stats_trigger in embed_title:
                        await weekly_stats_syncer(bot=self.bot, message=after)

                #Process for Explore Caught
                if after.content and explore_trigger in after.content:
                    pretty_log(
                        "info",
                        f"Detected explore caught edit by {after.author} ({after.author.id})",
                        label="💠 EXPLORE",
                        bot=self.bot,
                    )
                    await explore_caught_listener(
                        bot=self.bot, before=before, after=after
                    )

                # Process for Feeling Lucky rarespawn
                if after.channel.id == STRAYMONS__TEXT_CHANNELS.feeling_lucky:
                    await fl_rs_checker(bot=self.bot, message=after)

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
