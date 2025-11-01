import zoneinfo
from datetime import datetime
from zoneinfo import ZoneInfo

from utils.background_task.daily_ball_reset import daily_ball_reset
from utils.background_task.weekly_goal_reset import reset_weekly_goals
from utils.essentials.sched_helper import SchedulerManager
from utils.loggers.pretty_logs import pretty_log

NYC = zoneinfo.ZoneInfo("America/New_York")  # auto-handles EST/EDT

# 🛠️ Create a SchedulerManager instance with Asia/Manila timezone
scheduler_manager = SchedulerManager(timezone_str="Asia/Manila")


def format_next_run_manila(next_run_time):
    """
    Converts a timezone-aware datetime to Asia/Manila time and returns a readable string.
    """
    if next_run_time is None:
        return "No scheduled run time."
    # Convert to Manila timezone
    manila_tz = ZoneInfo("Asia/Manila")
    manila_time = next_run_time.astimezone(manila_tz)
    # Format as: Sunday, Nov 3, 2025 at 12:00 PM (Asia/Manila)
    return manila_time.strftime("%A, %b %d, %Y at %I:%M %p (Asia/Manila)")


# 🌈─────────────────────────────────────────────────────────────
# 💙 Minccino Scheduler Setup (setup_scheduler)
# 🌈─────────────────────────────────────────────────────────────
async def setup_scheduler(bot):

    # Start the scheduler
    scheduler_manager.start()

    # 🌸─────────────────────────────────────────────────────────
    # 💜 WEEKLY GOALS RESET  — Every Sunday at Midnight (NYC)
    # 🌸─────────────────────────────────────────────────────────
    try:
        weekly_reset_job = scheduler_manager.add_cron_job(
            reset_weekly_goals,
            "weekly_goals_reset",
            hour=0,
            minute=0,
            day_of_week="sun",
            args=[bot],
            timezone=NYC,
        )
        readable_next_run = format_next_run_manila(weekly_reset_job.next_run_time)
        pretty_log(
            tag="background_task",
            message=f"Weekly goals reset job scheduled at {readable_next_run}",
            bot=bot,
        )
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to schedule weekly goals reset job: {e}",
            bot=bot,
        )

    # ✨─────────────────────────────────────────────────────────
    # 🤍 DAILY FACTION BALL RESET — Every Midnight (NYC)
    # ✨─────────────────────────────────────────────────────────
    try:
        daily_faction_ball_reset_job = scheduler_manager.add_cron_job(
            daily_ball_reset,
            "daily_faction_ball_reset",
            hour=0,
            minute=0,
            args=[bot],
            timezone=NYC,
        )
        readable_next_run = format_next_run_manila(
            daily_faction_ball_reset_job.next_run_time
        )
        pretty_log(
            tag="background_task",
            message=f"Daily faction ball reset job scheduled at {readable_next_run}",
            bot=bot,
        )
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to schedule daily faction ball reset job: {e}",
            bot=bot,
        )
