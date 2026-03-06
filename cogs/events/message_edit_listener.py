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
from utils.listener_func.clan_members_listener import clan_members_command_listener
from utils.listener_func.explore_caught_listener import explore_caught_listener
from utils.listener_func.faction_ball_alert import faction_ball_alert
from utils.listener_func.fish_reco_ping import recommend_fishing_ball
from utils.listener_func.fl_rs import fl_rs_checker
from utils.listener_func.halloween_contest_listener import (
    halloween_contest_score_listener,
)
from utils.listener_func.held_item_ping import held_item_ping_handler
from utils.listener_func.pokemon_caught import pokemon_caught_listener
from utils.listener_func.pokemon_timer import detect_pokemeow_reply
from utils.listener_func.wb_reg_listener import handle_wb_register_command
from utils.listener_func.weekly_stats_syncer import weekly_stats_syncer
from utils.loggers.pretty_logs import pretty_log

FISHING_COLOR = 0x87CEFA

weekly_stats_trigger = "**Clan Weekly Stats — Straymons**"
explore_trigger = ":stopwatch: Your explore session has ended!"

triggers = {
    "hiker": "I could use some help clearing the snow, I left my Sirfetchd in my PC!",
    "clan_member": "Clan Member Information - Straymons",
}


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
                embed = after.embeds[0] if after.embeds else None
                embed_description = embed.description if embed else ""

                first_embed = after.embeds[0] if after.embeds else None
                first_embed_author = (
                    first_embed.author.name
                    if first_embed and first_embed.author
                    else ""
                )
                first_embed_description = (
                    first_embed.description
                    if first_embed and first_embed.description
                    else ""
                )
                first_embed_footer = (
                    first_embed.footer.text
                    if first_embed and first_embed.footer
                    else ""
                )

                # 🔹 Fishing reco ball
                if embed_description and "fished a wild" in embed_description:
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

                # Process for Clan Weekly Stats
                if after.embeds:
                    embed_title = after.embeds[0].title or ""
                    if weekly_stats_trigger in embed_title:
                        await weekly_stats_syncer(
                            bot=self.bot,
                            before=before,
                            message=after,
                        )

                # Process for Explore Caught
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
                    if after.embeds:
                        embed_description = after.embeds[0].description or ""
                        if embed_description and "You caught a" in embed_description:
                            pretty_log(
                                "info",
                                f"Detected Feeling Lucky rare spawn",
                                label="🍀 FL RS",
                                bot=self.bot,
                            )
                            await fl_rs_checker(bot=self.bot, message=after)

                # Faction Ball Alert
                if after.embeds:
                    desc = after.embeds[0].description
                    color = after.embeds[0].color
                    if (
                        desc
                        and "<:team_logo:" in desc
                        and "fished a wild" in desc
                        and (
                            color == FISHING_COLOR
                            or getattr(color, "value", None) == FISHING_COLOR
                        )
                    ):
                        """pretty_log(
                            "info",
                            f"Detected faction ball alert in fish embed",
                            label="🛡️ FACTION BALL ALERT",
                            bot=self.bot,
                        )"""
                        await faction_ball_alert(before=before, after=after)

                # 🎃 Halloween Contest Score Listener (Disabled for now)
                """content = after.content
                if (
                    content
                    and ":jack_o_lantern: your catch earned a score of"
                    in content.lower()
                ):
                    await halloween_contest_score_listener(
                        bot=self.bot, before_message=before, message=after
                    )"""
                # 💜────────────────────────────────────────────
                #          👥 Clan Members Command Listener
                # 💜────────────────────────────────────────────
                if first_embed:
                    if (
                        first_embed_description
                        and triggers["clan_member"] in first_embed_description
                    ):
                        pretty_log(
                            "info",
                            "Detected Clan Member Information embed, processing clan members command...",
                        )
                        await clan_members_command_listener(
                            self.bot,
                            after,
                        )
                # 💜────────────────────────────────────────────
                #          👑 World Boss Battle Reminder Registration Confirmation
                # 💜────────────────────────────────────────────
                if first_embed:
                    if (
                        first_embed_description
                        and "<:checkedbox:752302633141665812> Successfully registered your"
                        in first_embed_description
                        and first_embed.title
                        and "**A World Boss has spawned! Register now!**"
                        in first_embed.title
                    ):
                        pretty_log(
                            "info",
                            f"Matched World Boss Battle Reminder Registration Confirmation | Message ID: {after.id} | Channel: {after.channel.name}",
                        )
                        await handle_wb_register_command(
                            bot=self.bot, before_message=before, message=after
                        )
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
