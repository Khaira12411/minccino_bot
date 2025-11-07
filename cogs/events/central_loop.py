import asyncio
from discord.ext import commands
from utils.loggers.pretty_logs import pretty_log

# 🧹 Import your scheduled tasks
from utils.background_task.pokemon_reminders_checker import pokemon_reminder_checker
from utils.background_task.fl_cd_checker import fl_cd_checker
from utils.background_task.special_battle_timer_checker import special_battle_timer_checker
# 🍰──────────────────────────────
#   🎀 Cog: CentralLoop
#   Handles background tasks every 60 seconds
# 🍰──────────────────────────────
class CentralLoop(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.loop_task = None

    def cog_unload(self):
        if self.loop_task and not self.loop_task.done():
            self.loop_task.cancel()
            pretty_log(
                "warn",
                "Loop task cancelled on cog unload.",
                label="CENTRAL LOOP",
                bot=self.bot,
            )

    async def central_loop(self):
        """Background loop that ticks every 60 seconds"""
        await self.bot.wait_until_ready()
        from utils.cache.weekly_goal_tracker_cache import flush_weekly_goal_cache
        pretty_log(
            "",
            "✅ Central loop started!",
            label="🧭 CENTRAL LOOP",
            bot=self.bot,
        )
        while not self.bot.is_closed():
            try:
                pretty_log(
                    "",
                    "🔂 Running background checks...",
                    label="🧭 CENTRAL LOOP",
                    bot=self.bot,
                )

                # 🦭 Check if any pokemon reminder is due
                await pokemon_reminder_checker(self.bot)

                # 🍀 Check if any Feeling Lucky cd is due
                await fl_cd_checker(bot=self.bot)

                # 💠 Flush any dirty weekly goal stats to DB
                await flush_weekly_goal_cache(self.bot)

                # ⏰ Check if any special battle timers are due  (Disabled for now)
                #await special_battle_timer_checker(bot=self.bot)

            except Exception as e:
                pretty_log(
                    "error",
                    f"{e}",
                    label="CENTRAL LOOP ERROR",
                    bot=self.bot,
                )
            await asyncio.sleep(60)  # ⏱ tick interval

    @commands.Cog.listener()
    async def on_ready(self):
        """Start the loop automatically once the bot is ready"""
        if not self.loop_task:
            self.loop_task = asyncio.create_task(self.central_loop())


# ====================
# 🔹 Setup
# ====================
async def setup(bot: commands.Bot):
    cog = CentralLoop(bot)
    await bot.add_cog(cog)

    print("\n[📋 CENTRAL LOOP CHECKLIST] Scheduled tasks loaded:")
    print("  ─────────────────────────────────────────────")
    print("  ✅ 🦭  pokemon_reminder_checker")
    print("  ✅ 🍀  fl_cd_checker")
    print("  ✅ 💠  flush_weekly_goal_cache")
    print("  ✅ ⏰  special_battle_timer_checker")
    print("  🧭 CentralLoop ticking every 60 seconds!")
    print("  ─────────────────────────────────────────────\n")
