from utils.essentials.sched_helper import SchedulerManager
from utils.background_task.weekly_goal_reset import reset_weekly_goals

# 🛠️ Create a SchedulerManager instance with Asia/Manila timezone
scheduler_manager = SchedulerManager(timezone_str="Asia/Manila")

async def setup_scheduler(bot):

    # Weekly Goals Reset - Every Sunday at Noon Manila Time
    scheduler_manager.add_cron_job(
    reset_weekly_goals,
    "weekly_goals_reset",
    hour=12,
    minute=00,
    day_of_week="sun",
    args=[bot],
    )

    # 🛠️ Start the scheduler
    scheduler_manager.start()

    # ✅ Attach the actual manager to the bot
    bot.scheduler_manager = scheduler_manager
