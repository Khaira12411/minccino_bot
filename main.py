# ╭────────────────────────────────────────────╮
# │           🤎 Minccino Bot Imports 🤍       │
# ╰────────────────────────────────────────────╯

# ── 🐭 Standard Library Imports 🐭 ──
import asyncio
import glob
import logging
import os
import random
from datetime import datetime
from zoneinfo import ZoneInfo

# ── 🎀 Third-Party Imports 🎀 ──
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

# ── 🧸 Project-Specific Imports 🧸 ──
from config.current_setup import *
from utils.cache.centralized_cache import load_all_caches
from utils.essentials.get_pg_pool import get_pg_pool
from utils.essentials.role_checks import *
from utils.loggers.pretty_logs import pretty_log, set_minccino_bot
from utils.loggers.rate_limit_logger import setup_rate_limit_logging
from utils.background_task.scheduler import setup_scheduler
# ╭───────────────────────────────╮
# │   🤎  Suppress Logs  🤍      │
# ╰───────────────────────────────╯
logging.basicConfig(level=logging.CRITICAL)
for logger_name in [
    "discord",
    "discord.gateway",
    "discord.http",
    "discord.voice_client",
    "asyncio",
]:
    logging.getLogger(logger_name).setLevel(logging.CRITICAL)
logging.getLogger("discord.client").setLevel(logging.CRITICAL)

# ╭───────────────────────────────╮
# │   🤎  Constants / Helpers  🤍  │
# ╰───────────────────────────────╯
ASIA_MANILA = ZoneInfo("Asia/Manila")

MINCCINO_MORNING_STATUSES = [
    (discord.ActivityType.playing, "with timers for the morning rush ⏰🐭"),
    (discord.ActivityType.playing, "with commands and cleaning up delays 🧹🐭"),
    (discord.ActivityType.listening, "for your next Pokemon call 🎶🐭"),
    (discord.ActivityType.watching, "over every timer 👀🐭"),
]
MINCCINO_NIGHT_STATUSES = [
    (discord.ActivityType.playing, "with timers before bed 🌙🐭"),
    (discord.ActivityType.listening, "night-time Pokemon commands 🌌🐭"),
    (discord.ActivityType.watching, "over sleepy timers 👀🐭"),
]
MINCCINO_DEFAULT_STATUSES = [
    (discord.ActivityType.playing, "between timers and commands 🐭⏰"),
    (discord.ActivityType.listening, "to every timer ⏱️🐭"),
]


def pick_status_tuple():
    now = datetime.now(ASIA_MANILA)
    pool = MINCCINO_MORNING_STATUSES if 6 <= now.hour < 18 else MINCCINO_NIGHT_STATUSES
    return random.choice(pool)


# ╭───────────────────────────────╮
# │      🤎  Bot Factory  🤍      │
# ╰───────────────────────────────╯
# ── 🐾 Create & Configure Bot 🐾 ──
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
set_minccino_bot(bot)
setup_rate_limit_logging(bot)

# ╭────────────────────────────────────────────────╮
# │      🤎  Minccino Guild Join Handler  🤍      │
# ╰────────────────────────────────────────────────╯
# ──────────── 🐾 Stay or Leave 🐾 ────────────────
from utils.loggers.pretty_logs import pretty_log

ALLOWED_GUILD_IDS = [
    OKA_SERVER_ID,
    STRAYMONS_GUILD_ID,
    CC_GUILD_ID,
    1154753039685660793
]


@bot.event
async def on_guild_join(guild: discord.Guild):
    try:
        # Fetch Khy
        khy_user = await bot.fetch_user(KHY_USER_ID)

        # Fetch guild owner
        guild_owner = guild.owner or await bot.fetch_user(guild.owner_id)
        owner_name = guild_owner.name if guild_owner else "Unknown"
        owner_id = guild_owner.id if guild_owner else "Unknown"

        # 🐁 DM Khy about the new guild
        try:
            await khy_user.send(
                f"Minccino joined a guild:\n"
                f"Name: {guild.name}\n"
                f"ID: {guild.id}\n"
                f"Owner: {owner_name} (ID: {owner_id})"
            )
        except Exception:
            pretty_log(
                tag="warn",
                message=f"Could not DM Khy about guild join for {guild.name}.",
                label="MINCCINO",
            )

        # ✅ Authorized guild?
        if guild.id in ALLOWED_GUILD_IDS:
            pretty_log(
                tag="ready",
                message=f"Minccino joined authorized guild:\n"
                f"Name: {guild.name}\n"
                f"ID: {guild.id}\n"
                f"Owner: {owner_name} (ID: {owner_id})",
                label="MINCCINO",
            )
        else:
            pretty_log(
                tag="warn",
                message=f"Minccino joined unauthorized guild and will leave:\n"
                f"Name: {guild.name}\n"
                f"ID: {guild.id}\n"
                f"Owner: {owner_name} (ID: {owner_id})",
                label="MINCCINO",
            )

            # ⚠️ DM guild owner
            if guild_owner:
                try:
                    await guild_owner.send(
                        f"Hello {owner_name}!\n\n"
                        "Minccino can only function in authorized servers under Khy's supervision.\n"
                        "This server is not authorized, so Minccino will be leaving. Thank you for understanding!"
                    )
                except Exception:
                    pretty_log(
                        tag="warn",
                        message=f"Could not DM the owner of {guild.name}.",
                        label="MINCCINO",
                    )

            # Leave unauthorized guild
            await guild.leave()

    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Error in on_guild_join for guild {guild.name}: {e}",
            label="MINCCINO",
            include_trace=True,
        )


# ╭───────────────────────────────╮
# │     🤎  Background Tasks  🤍   │
# ╰───────────────────────────────╯
# ── 🌤️🐭 Status Rotator 🐭🌤️ ──
@tasks.loop(minutes=5)
async def status_rotator():
    activity_type, message = pick_status_tuple()
    pretty_log(
        "", "🌤️  STATUS ROTATOR", f"Switching status → {activity_type.name}: {message}"
    )
    await bot.change_presence(
        activity=discord.Activity(type=activity_type, name=message)
    )


# ── 🖌️🌼 Startup Tasks 🌼🖌️ ──
@tasks.loop(count=1)
async def startup_tasks():
    await bot.wait_until_ready()
    await load_all_caches(bot)
    if not refresh_all_caches.is_running():
        refresh_all_caches.start()

    # ── 🤎🐾 Status Rotator 🐾🤎 ──
    if not status_rotator.is_running():
        status_rotator.start()
    activity_type, message = pick_status_tuple()
    await bot.change_presence(
        activity=discord.Activity(type=activity_type, name=message)
    )
    pretty_log(
        tag="",
        message=f"Initial presence set: {activity_type} {message}",
        label="🍵 Status Rotator",
    )
    await startup_checklist(bot)


# ── ⏱️🧸 Refresh All Caches 🧸⏱️ ──
@tasks.loop(hours=1)
async def refresh_all_caches():
    # Skip the very first run
    if not hasattr(refresh_all_caches, "has_run"):
        refresh_all_caches.has_run = True
        return

    await load_all_caches(bot)


# ╭───────────────────────────────╮
# │      🤎  Event Hooks  🤍     │
# ╰───────────────────────────────╯
# ── 🤎🐾 On Ready 🐾🤎 ──
@bot.event
async def on_ready():
    pretty_log("ready", f"Minccino bot awake as {bot.user}")

    # ── 🤎🐾 Tree Synced🐾🤎 ──
    await bot.tree.sync()

    # ── 🤎🐾 On Ready 🐾🤎 ──
    if not startup_tasks.is_running():
        startup_tasks.start()


# ── 🐭✨ Slash Command Error Handler ✨🐭 ──
async def on_app_command_error(
    interaction: discord.Interaction, error: app_commands.AppCommandError
):
    # Ignore slash command not found
    if isinstance(error, app_commands.CommandNotFound):
        return

    # Handle your custom role-check failures
    if isinstance(
        error,
        (
            ClanStaffCheckFailure,
            VIPCheckFailure,
            ClanMemberCheckFailure,
            OwnerCheckFailure,
            OwnerCoownerCheckFailure,
            KhyCheckFailure,
        ),
    ):
        await interaction.response.send_message(error.args[0], ephemeral=True)
        return

    # Fallback for other slash errors
    await interaction.response.send_message("❌ Something went wrong.", ephemeral=True)
    pretty_log(
        tag="error",
        message=f"Slash command error: {error}",
        include_trace=True,
    )


# Register the slash command handler
bot.tree.error(on_app_command_error)


# ── 🐭✨ Prefix Command Error Handler ✨🐭 ──
@bot.event
async def on_command_error(ctx, error):
    # Ignore prefix command not found
    if isinstance(error, commands.CommandNotFound):
        return

    # You can handle other prefix errors here if needed
    await ctx.send("❌ Something went wrong.")
    pretty_log(
        tag="error",
        message=f"Prefix command error: {error}",
        include_trace=True,
    )


# ── 🧸🍂 Setup Hook 🍂🧸 ──
@bot.event
async def setup_hook():
    # 🥛 PostgreSQL connection
    try:
        bot.pg_pool = await get_pg_pool()
    except Exception as e:
        pretty_log("critical", f"Postgres connection failed: {e}", include_trace=True)

    # 🍪 Load all cogs
    for cog_path in glob.glob("cogs/**/*.py", recursive=True):
        relative_path = os.path.relpath(cog_path, "cogs")
        module_name = relative_path[:-3].replace(os.sep, ".")
        cog_name = f"cogs.{module_name}"
        try:
            await bot.load_extension(cog_name)
        except Exception as e:
            pretty_log("error", f"Failed to load {cog_name}: {e}", include_trace=True)

    # ── 🤎 Scheduler Setup ──
    await setup_scheduler(bot)
    # Optional: store scheduler manager on bot for easy access later
    bot.scheduler_manager = bot.scheduler_manager or None
# ╭───────────────────────────────╮
# │     🤎  Startup Checklist  🤍  │
# ╰───────────────────────────────╯
async def startup_checklist(bot: commands.Bot):
    from utils.cache import (
        ball_reco_cache,
        boosted_channels_cache,
        get_water_state,
        held_item_cache,
        timer_cache,
        user_reminders_cache,
        feeling_lucky_cache,
        user_captcha_alert_cache,
        res_fossils_alert_cache,
        straymon_member_cache,
        weekly_goal_cache,
        daily_faction_ball_cache,
        faction_ball_alert_cache,
    )

    print("\n★━━━━━━━━━━━━━━━━━━━━★")
    print(f"✅ {len(bot.cogs)} 🌼 Cogs Loaded")
    print(f"✅ 🌊 {get_water_state()} Waterstate")  # use getter
    print(f"✅ {len(straymon_member_cache)} 🐥 Straymon Members")
    print(f"✅ {len(weekly_goal_cache)} 🎀 Weekly Goal Trackers")
    print(f"✅ {len(timer_cache)} ⌚ Pokemon Timer Users")
    print(f"✅ {len(held_item_cache)} 🍄 Held Item Ping Users")
    print(f"✅ {len(ball_reco_cache)} 🍚 Ball Recommendation Users")
    print(f"✅ {len(user_reminders_cache)} ⚾ User Reminders")
    print(f"✅ {len(boosted_channels_cache)} 💒 Boosted Channels")
    print(f"✅ {len(daily_faction_ball_cache)} 🎯 Daily Faction Balls")
    print(f"✅ {len(feeling_lucky_cache)} 🍀 Feeling Lucky Cooldowns")
    print(f"✅ {len(user_captcha_alert_cache)} 🛡️  Captcha Alert Users")
    print(f"✅ {len(res_fossils_alert_cache)} 🦴  Research Fossils Alert Users")
    print(f"✅ {len(faction_ball_alert_cache)} 🥟  Faction Ball Alert Users")
    print(f"✅ {status_rotator.is_running()} 🍵 Status Rotator Running")
    print(f"✅ {startup_tasks.is_running()} 🖌️  Startup Tasks Running")
    pg_status = "Ready" if hasattr(bot, "pg_pool") else "Not Ready"
    print(f"✅ {pg_status} 🧀  PostgreSQL Pool")
    total_slash_commands = sum(1 for _ in bot.tree.walk_commands())
    print(f"✅ {total_slash_commands} 🍞 Slash Commands Synced")
    # Check weekly goals reset job
    scheduler_status = "Not Scheduled"
    if hasattr(bot, "scheduler_manager") and bot.scheduler_manager:
        job = bot.scheduler_manager.jobs.get("weekly_goals_reset")
        if job:
            scheduler_status = f"Scheduled ✅ next run: {job.next_run_time}"

    print(f"✅ {scheduler_status} ⏰ Weekly Goals Reset")
    print("★━━━━━━━━━━━━━━━━━━━━★\n")


# ╭───────────────────────────────╮
# │  🤎  Main Async Runner  🤍      │
# ╰───────────────────────────────╯
async def main():
    load_dotenv()
    pretty_log("ready", "MinccinoBot is starting...")

    retry_delay = 5
    while True:
        try:
            await bot.start(os.getenv("DISCORD_TOKEN"))
        except KeyboardInterrupt:
            pretty_log("ready", "Shutting down MinccinoBot...")
            break
        except Exception as e:
            pretty_log("error", f"Bot crashed: {e}", include_trace=True)
            pretty_log("ready", f"Restarting MinccinoBot in {retry_delay} seconds...")
            await asyncio.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, 60)


if __name__ == "__main__":
    asyncio.run(main())
