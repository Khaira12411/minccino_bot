# 🟣────────────────────────────────────────────
#           💜 Message Create Listener Cog 💜
# ─────────────────────────────────────────────

import asyncio

import discord
from discord.ext import commands

from config.current_setup import (
    ACTIVE_GUILD_ID,
    CC_GUILD_ID,
    MINCCINO_APP_ID,
    POKEMEOW_APPLICATION_ID,
    STAFF_SERVER_GUILD_ID,
    STRAYMONS_GUILD_ID,
    WATERSTATE_CHANNEL_ID,
)
from utils.listener_func.ball_reco_ping import recommend_ball
from utils.listener_func.battle_timer import detect_pokemeow_battle
from utils.listener_func.catchbot_listener import *
from utils.listener_func.held_item_ping import held_item_ping_handler
from utils.listener_func.perks_listener import auto_update_catchboost
from utils.listener_func.pokemon_timer import detect_pokemeow_reply
from utils.listener_func.relics_listener import handle_relics_message
from utils.listener_func.reminder_embed_handler import handle_reminder_embed
from utils.listener_func.waterstate_listener import on_waterstate_message
from utils.loggers.pretty_logs import pretty_log
from utils.listener_func.feeling_lucky import feeling_lucky_cd
from utils.listener_func.boosted_channel_listener import newly_boosted_channel_listener, remove_boosted_channel_listener
from config.straymons_constants import STRAYMONS__TEXT_CHANNELS
CC_BOT_LOG_ID = 1413576563559239931
WOOPER_ID = 1388515441592504483
KHY_CHANNEL_ID = 1050645885844987904
newly_boosted_trigger = (
    "<:checkedbox:752302633141665812> successfully applied a +5% channel boost to"
)
remove_boosted_trigger = "<:checkedbox:752302633141665812> successfully removed the channel boost from channel"
cb_return_trigger = ":robot: I have returned with some Pokemon for you!"
cb_command_embed_trigger = (
    ":battery: Your CatchBot is currently catching Pokemon for you!"
)
cb_checklist_trigger = "View your event checklist with ;e cl"
CATCHBOT_SPENT_PATTERN = re.compile(
    r"You spent <:[^:]+:\d+> \*\*[\d,]+ PokeCoins\*\* to run your catch bot\.",
    re.IGNORECASE,
)
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
            # 🐳 Only process Wooper's messages in CC_BOT_LOG_ID
            if (
                message.channel.id == CC_BOT_LOG_ID
            ):  # and message.author.id == WOOPER_ID:
                pretty_log(
                    "debug",
                    f"Message in CC log: {message.id}, author={message.author} ({message.author.id}), embeds={len(message.embeds)}",
                )

                await handle_reminder_embed(bot=self.bot, message=message)
                return

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
                1154753039685660793,
            ):
                # ⌚ detect PokéMeow replies
                await detect_pokemeow_reply(message)

                # ⌚ detect PokéMeow Battle replies
                await detect_pokemeow_battle(bot=self.bot, message=message)

                # 🐚 Held item ping
                await held_item_ping_handler(self.bot, message)

                # 🥎 Recommend ball
                await recommend_ball(message, self.bot)

                # 🧪 Debug: Relics processing
                await handle_relics_message(bot=self.bot, message=message)

                # 🧪 Autoupdate catch boost via ;perks
                await auto_update_catchboost(bot=self.bot, message=message)

                if message.channel.id == STRAYMONS__TEXT_CHANNELS.feeling_lucky:
                    # 🍀 Feeling Lucky Cooldown
                    await feeling_lucky_cd(bot=self.bot, message=message)

                # 🌟 Newly Channel Boost Listener
                if newly_boosted_trigger.lower() in message.content.lower():
                    await newly_boosted_channel_listener(bot=self.bot, message=message)

                # 😢 Remove Channel Boost Listener
                if remove_boosted_trigger.lower() in message.content.lower():
                    await remove_boosted_channel_listener(bot=self.bot, message=message)

                # 🟣 Catchbot processing
                if message.content:
                    # 1️⃣ CatchBot return text
                    if cb_return_trigger.lower() in message.content.lower():
                        pretty_log(
                            "info",
                            f"Matched CatchBot return trigger | Message ID: {message.id} | Channel: {message.channel.name}",
                        )
                        await handle_cb_return_message(bot=self.bot, message=message)

                    # 2️⃣ CatchBot run message
                    elif CATCHBOT_SPENT_PATTERN.search(message.content):
                        pretty_log(
                            "info",
                            f"Matched CatchBot spent pattern | Message ID: {message.id} | Channel: {message.channel.name}",
                        )
                        await handle_cb_run_message(bot=self.bot, message=message)

                # 3️⃣ CatchBot embeds
                if message.embeds:
                    embed = message.embeds[0]

                    # 🔹 Check fields
                    for field in embed.fields:
                        name = field.name.lower() if field.name else ""
                        value = field.value.lower() if field.value else ""

                        if cb_command_embed_trigger.lower() in name or cb_command_embed_trigger.lower() in value:
                            pretty_log("embed", f"Matched CatchBot command trigger in embed field: {field.name}")
                            await handle_cb_command_embed(bot=self.bot, message=message)
                            break

                    # 🔹 Check footer for ;cl command
                    if embed.footer and embed.footer.text:
                        footer_text = embed.footer.text.lower()
                        if cb_checklist_trigger.lower() in footer_text:
                            pretty_log("embed", f"Matched CatchBot checklist trigger in embed footer: {footer_text}")
                            await handle_cb_checklist_message(bot=self.bot, message=message)

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
