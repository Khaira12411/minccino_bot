from utils.essentials.sched_helper import SchedulerManager
from utils.background_task.weekly_goal_reset import reset_weekly_goals
from utils.background_task.daily_ball_reset import daily_ball_reset
import zoneinfo

NYC = zoneinfo.ZoneInfo("America/New_York")  # auto-handles EST/EDT

# 🛠️ Create a SchedulerManager instance with Asia/Manila timezone
scheduler_manager = SchedulerManager(timezone_str="Asia/Manila")

async def setup_scheduler(bot):

    # Weekly Goals Reset - Every Sunday at Midnight NYC Time
    scheduler_manager.add_cron_job(
    reset_weekly_goals,
    "weekly_goals_reset",
    hour=0,
    minute=00,
    day_of_week="sun",
    args=[bot],
    timezone=NYC,
    )

    # Daily Faction Ball Reset - Every day at midnight NYC Time
    scheduler_manager.add_cron_job(
        daily_ball_reset,
        "daily_faction_ball_reset",
        hour=0,
        minute=00,
        args=[bot],
        timezone=NYC,
    )


    # 🛠️ Start the scheduler
    scheduler_manager.start()

    # ✅ Attach the actual manager to the bot
    bot.scheduler_manager = scheduler_manager
