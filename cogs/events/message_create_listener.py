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
    KHY_USER_ID
)
from config.straymons_constants import STRAYMONS__TEXT_CHANNELS
from utils.listener_func.ball_reco_ping import recommend_ball
from utils.listener_func.battle_timer import detect_pokemeow_battle
from utils.listener_func.battle_won_listener import battle_won_listener
from utils.listener_func.boosted_channel_listener import (
    newly_boosted_channel_listener,
    remove_boosted_channel_listener,
)
from utils.listener_func.captcha_alert_listener import captcha_alert_handler
from utils.listener_func.catchbot_listener import *
from utils.listener_func.clan_members_listener import clan_members_command_listener
from utils.listener_func.egg_listener import (
    egg_hatched_listener,
    egg_ready_to_hatch_listener,
)
from utils.listener_func.faction_ball_alert import faction_ball_alert
from utils.listener_func.faction_ball_listener import (
    extract_faction_ball_from_daily,
    extract_faction_ball_from_fa,
)
from utils.listener_func.feeling_lucky import feeling_lucky_cd
from utils.listener_func.fish_timer import fish_timer_handler
from utils.listener_func.halloween_contest_listener import (
    halloween_contest_embed_listener,
)
from utils.listener_func.held_item_ping import held_item_ping_handler
from utils.listener_func.hiker import hiker_snow_damage_listener
from utils.listener_func.perks_listener import auto_update_catchboost
from utils.listener_func.pokemon_timer import detect_pokemeow_reply
from utils.listener_func.relics_listener import handle_relics_message
from utils.listener_func.reminder_embed_handler import handle_reminder_embed
from utils.listener_func.secret_santa_listener import (
    secret_santa_listener,
    secret_santa_timer_listener,
)
from utils.listener_func.special_battle_npc_listener import (
    special_battle_npc_listener,
    special_battle_npc_timer_listener,
)
from utils.listener_func.waterstate_listener import on_waterstate_message
from utils.listener_func.wb_reg_listener import (

    register_wb_battle_reminder,
)
from utils.listener_func.weekly_stats_syncer import weekly_stats_syncer
from utils.loggers.pretty_logs import pretty_log
from utils.listener_func.berry_listener import berry_listener
from utils.listener_func.berry_water_listener import (
    handle_berry_water_message,
    handle_mulch_message,
)
from utils.listener_func.message_listener_tester import test_message_listener
weekly_stats_trigger = "**Clan Weekly Stats — Straymons**"
battle_won_trigger = "won the battle! :tada:"
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
captcha_alert_trigger = "A wild Captcha has appeared"
captcha_description_trigger = (
    "you must type your answer to the captcha below to continue playing"
)

FACTIONS = ["aqua", "flare", "galactic", "magma", "plasma", "rocket", "skull", "yell"]
BANNED_PERKS_PHRASES = {"PokeMeow Clans — Perks Info", "PokeMeow Clans — Rank Info"}
secret_santa_phrases = [
    "You sent <:PokeCoin:666879070650236928>",
    "to a random user!",
    "Your odds to receive items was boosted by",
    "You received",
]
triggers = {
    "hiker": "I could use some help clearing the snow, I left my Sirfetchd in my PC!",
    "clan_member": "Clan Member Information - Straymons",
}


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
            # 💜────────────────────────────────────────────
            #          🧪 Message Test Listener
            # 💜────────────────────────────────────────────
            if message.content and message.content.startswith("mtest") and message.author.id == KHY_USER_ID:
                pretty_log(
                    "info",
                    f"Running message listener tests for message ID: {message.id}",
                )
                await test_message_listener(bot=self.bot, message=message)


            # --- Weakness chart + general processing ---
            if message.guild and message.guild.id in (
                ACTIVE_GUILD_ID,
                STAFF_SERVER_GUILD_ID,
                STRAYMONS_GUILD_ID,
                1154753039685660793,
            ):
                content = message.content
                first_embed = message.embeds[0] if message.embeds else None
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
                # 💜────────────────────────────────────────────
                #           ⏲️ Pokemon Timer Processing Only
                # 💜────────────────────────────────────────────
                if message.embeds and message.embeds[0]:
                    embed = message.embeds[0]
                    embed_description = embed.description if embed else None
                    if embed_description and "found a wild" in embed_description:
                        await detect_pokemeow_reply(message)

                        # 🥎 Recommend ball
                        await recommend_ball(message, self.bot)

                # Faction Ball Alert
                if first_embed:
                    if (
                        first_embed.description
                        and "<:team_logo:" in first_embed.description
                        and "found a wild" in first_embed.description
                    ):
                        await faction_ball_alert(before=message, after=message)
                # 💜────────────────────────────────────────────
                # ⚔️ Held Item Ping Processing Only
                # 💜────────────────────────────────────────────
                if (
                    first_embed_description
                    and "<:held_item:" in first_embed_description
                ):
                    await held_item_ping_handler(self.bot, message)
                # 💜────────────────────────────────────────────
                #           🎣 Fish Timer Processing Only
                # 💜────────────────────────────────────────────
                if message.embeds and message.embeds[0]:
                    embed = message.embeds[0]
                    embed_description = embed.description if embed else None
                    if (
                        embed_description
                        and "cast a" in embed_description
                        and "into the water" in embed_description
                    ):
                        await fish_timer_handler(message)

                # 💜────────────────────────────────────────────
                # ⚔️ Battle Timer Processing Only
                # 💜────────────────────────────────────────────
                if first_embed_author and "PokeMeow Battles" in first_embed_author:
                    await detect_pokemeow_battle(bot=self.bot, message=message)

                # Process battle won
                if message.content and battle_won_trigger in message.content:

                    await battle_won_listener(bot=self.bot, message=message)

                # 💜────────────────────────────────────────────
                # ⚔️ Relics Processing Only
                # 💜────────────────────────────────────────────
                if (
                    first_embed_author
                    and "pokemeow research lab" in first_embed_author.lower()
                ):
                    await handle_relics_message(bot=self.bot, message=message)

                # 🧪 Autoupdate catch boost via ;perks
                if first_embed:
                    embed_author_name = (
                        first_embed.author.name
                        if first_embed.author and first_embed.author.name
                        else ""
                    )
                    if "perks" in embed_author_name.lower() and not any(
                        phrase in embed_author_name for phrase in BANNED_PERKS_PHRASES
                    ):
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

                # ⏰ Weekly Stats Syncer
                embed = message.embeds[0] if message.embeds else None
                if embed:
                    embed_title = embed.title or ""
                    if weekly_stats_trigger in embed_title:
                        pretty_log(
                            "info",
                            f"Matched Weekly Stats trigger  from created message | Message ID: {message.id} | Channel: {message.channel.name}",
                        )
                        await weekly_stats_syncer(
                            bot=self.bot,
                            before=message,
                            message=message,
                        )

                # Faction Ball Listener from ;fa command
                if first_embed:
                    if first_embed.author and any(
                        f in first_embed.author.name.lower() for f in FACTIONS
                    ):
                        await extract_faction_ball_from_fa(
                            bot=self.bot, message=message
                        )

                # Daily Faction Ball Listener
                if first_embed:
                    if (
                        first_embed.title
                        and "daily streak" in first_embed.title.lower()
                    ):
                        pretty_log(
                            "info",
                            f"Matched Daily Faction Ball Listener | Message ID: {message.id} | Channel: {message.channel.name}",
                        )
                        await extract_faction_ball_from_daily(
                            bot=self.bot, message=message
                        )
                # World Boss Battle Reminder Registration
                if first_embed:
                    embed_description = first_embed.description or ""
                    if (
                        "<:checkedbox:752302633141665812> You are registered for this fight"
                        in embed_description
                        and ";wb fight" in embed_description
                    ):
                        pretty_log(
                            "info",
                            f"Matched World Boss Battle Reminder Registration | Message ID: {message.id} | Channel: {message.channel.name}",
                        )
                        await register_wb_battle_reminder(bot=self.bot, message=message)

                # 💜────────────────────────────────────────────
                # Egg Hatching Listeners
                # 💜────────────────────────────────────────────
                if message.content and message.author.id == POKEMEOW_APPLICATION_ID:
                    if (
                        "your egg is ready to hatch! `/egg hatch` to hatch it."
                        in message.content
                    ):
                        pretty_log(
                            "info",
                            f"🔹 Matched Egg Ready to Hatch Listener | message_id={message.id}",
                        )
                        await egg_ready_to_hatch_listener(bot=self.bot, message=message)
                # Egg Hatched Listener
                if first_embed:
                    if (
                        first_embed_footer
                        and "PokeMeow | Egg Hatch" in first_embed.footer.text
                    ):
                        pretty_log(
                            "info",
                            f"🔹 Matched Egg Hatched Listener | message_id={message.id}",
                        )
                        await egg_hatched_listener(bot=self.bot, message=message)

                # Special Battle NPC Listener (Disabled for now)
                if first_embed:
                    if (
                        first_embed.description
                        and "challenged <:xmas_blue:1451059140955734110> **XMAS Blue** to a battle!"
                        in first_embed.description
                    ):
                        pretty_log(
                            "info",
                            f"🔹 Matched Special Battle NPC Listener for XMAS BLUE | message_id={message.id}",
                        )
                        await special_battle_npc_listener(bot=self.bot, message=message)
                if (
                    content
                    and ":x: You cannot fight XMAS Blue yet! He will be available for you to re-battle"
                    in content
                ):
                    pretty_log(
                        "info",
                        f"🔹 Matched Special Battle NPC Timer Listener for XMAS BLUE | message_id={message.id}",
                    )
                    await special_battle_npc_timer_listener(
                        bot=self.bot, message=message
                    )
                # 🛡️ Captcha Alert Listener
                if first_embed:
                    title = first_embed.title.lower() if first_embed.title else ""
                    description = (
                        first_embed.description.lower()
                        if first_embed.description
                        else ""
                    )
                    if (
                        ("captcha" in title or "captcha" in description)
                        and "captcha forgiveness centre" not in title
                        and "captcha forgiveness centre" not in description
                    ):

                        await captcha_alert_handler(bot=self.bot, message=message)

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
                if first_embed:

                    # 🔹 Check fields
                    for field in first_embed.fields:
                        name = field.name.lower() if field.name else ""
                        value = field.value.lower() if field.value else ""

                        if (
                            cb_command_embed_trigger.lower() in name
                            or cb_command_embed_trigger.lower() in value
                        ):
                            pretty_log(
                                "embed",
                                f"Matched CatchBot command trigger in embed field: {field.name}",
                            )
                            await handle_cb_command_embed(bot=self.bot, message=message)
                            break

                    # 🔹 Check footer for ;cl command
                    if first_embed.footer and first_embed.footer.text:
                        footer_text = first_embed.footer.text.lower()
                        if cb_checklist_trigger.lower() in footer_text:
                            """pretty_log(
                                "embed",
                                f"Matched CatchBot checklist trigger in embed footer: {footer_text}",
                            )"""
                            await handle_cb_checklist_message(
                                bot=self.bot, message=message
                            )
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
                            message,
                        )
                # 💜────────────────────────────────────────────
                #          🧑‍🌾 Berry Reminder Listener
                # 💜────────────────────────────────────────────
                if first_embed:
                    if (
                        first_embed_description
                        and "garden overview" in first_embed_description.lower()
                    ):
                        pretty_log(
                            "info",
                            "Detected Garden Overview embed, processing berry reminders...",
                        )
                        await berry_listener(
                            bot=self.bot,
                            before_message=message,
                            message=message,
                        )

                # 💜────────────────────────────────────────────
                #          🧑‍🌾 Berry Water Listener
                # 💜────────────────────────────────────────────
                if message.content:
                    if "Watered" in message.content and "Next stage" in message.content:
                        pretty_log(
                            "info",
                            "Detected Berry Water message, processing berry water reminders...",
                        )
                        await handle_berry_water_message(bot=self.bot, message=message)
                # 💜────────────────────────────────────────────
                #          🧑‍🌾  Mulch Listener
                # 💜────────────────────────────────────────────
                if message.content:
                    if (
                        "Applied" in message.content
                        and "Mulch" in message.content
                        and "to Slot" in message.content
                    ):
                        pretty_log(
                            "info",
                            "Detected Mulch message, processing growth mulch reminders...",
                        )
                        await handle_mulch_message(bot=self.bot, message=message)

                # 💜────────────────────────────────────────────
                #          ⛄️ Seasonal Listeners
                # 💜────────────────────────────────────────────
                # Secret Santa Listener
                if message.content:
                    # Check if all ss phrases are in the message content
                    if all(
                        phrase in message.content for phrase in secret_santa_phrases
                    ):
                        pretty_log(
                            "info",
                            f"🎅 Matched Secret Santa Listener | Message ID: {message.id} | Channel: {message.channel.name}",
                        )
                        await secret_santa_listener(bot=self.bot, message=message)
                # Secret Santa Timer Listener
                if message.content:
                    if ":x: You may send out another gift on" in message.content:
                        pretty_log(
                            "info",
                            f"🎅 Matched Secret Santa Timer Listener | Message ID: {message.id} | Channel: {message.channel.name}",
                        )
                        await secret_santa_timer_listener(bot=self.bot, message=message)
                # ❄️ Hiker Snow Damage Listener
                if (
                    first_embed_description
                    and triggers["hiker"] in first_embed_description
                ):
                    pretty_log(
                        "info",
                        f"❄️ Matched Hiker Snow Damage Listener | Message ID: {message.id} | Channel: {message.channel.name}",
                    )
                    await hiker_snow_damage_listener(message=message)

                # 🎃 Halloween Contest Embed Listener
                if first_embed:
                    embed_author = first_embed.author.name if first_embed.author else ""
                    if (
                        embed_author
                        and "halloween catch contest" in embed_author.lower()
                    ):
                        pretty_log(
                            "info",
                            f"🎃 Matched Halloween Contest Embed Listener | Message ID: {message.id} | Channel: {message.channel.name}",
                        )
                        await halloween_contest_embed_listener(
                            bot=self.bot, message=message
                        )

            # 🌊 Waterstate channel processing ---
            if message.channel.id == WATERSTATE_CHANNEL_ID:
                await on_waterstate_message(message)

        except Exception as e:
            pretty_log(
                tag="critical",
                message=f"Unhandled exception in on_message | Message ID: {message.id} | Channel ID: {message.channel.id} | {e}",
            )


# 💜────────────────────────────────────────────
# [🟣 SETUP] Add Cog to Bot
# ─────────────────────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(MessageCreateListener(bot))
