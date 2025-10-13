# 🪵 utils.loggers.pretty_logs import pretty_log

import traceback
from datetime import datetime

import discord
from discord.ext import commands

# -------------------- 🐭 Global Bot Reference --------------------
BOT_INSTANCE: commands.Bot | None = None


def set_minccino_bot(bot: commands.Bot):
    """Set the global bot instance for automatic logging."""
    global BOT_INSTANCE
    BOT_INSTANCE = bot


# -------------------- 🧀 Logging Tags --------------------
TAGS = {
    "info": "🐭 INFO",
    "db": "🍙 DB INFO",
    "cmd": "🧀 COMMAND",
    "ready": "🐁 READY",
    "error": "💥 ERROR",
    "warn": "⛔ WARN",
    "critical": "🚨 CRITICAL",
    "skip": "🤍 SKIP",
    "sent": "📨 SENT",
    "captcha": "📢 CAPTCHA",
    "background_task": "🫒  BACKGROUND TASK",
}

# -------------------- 🎨 ANSI Colors --------------------
COLOR_SILVER = "\033[38;2;211;211;211m"  # soft silver-gray
COLOR_YELLOW = "\033[93m"
COLOR_RED = "\033[91m"
COLOR_RESET = "\033[0m"

MAIN_COLORS = {
    "silver": COLOR_SILVER,
    "yellow": COLOR_YELLOW,
    "red": COLOR_RED,
    "reset": COLOR_RESET,
}

# -------------------- ⚠️ Critical Logs Channel --------------------
CRITICAL_LOG_CHANNEL_ID = (
    1410202143570530375  # TODO: replace with your Minccino error log channel
)


# -------------------- 🌸 Main Pretty Log --------------------
def main_pretty_log(message: str, level: str = "info", emoji: str = "💙"):
    """
    Prints a colored log for main.py with timestamp and emoji.

    Parameters:
    - message: str → the main log message
    - level: str → 'info', 'warn', 'error'
    - emoji: str → custom emoji for the log
    """
    now = datetime.now().strftime("%H:%M:%S")
    color = MAIN_COLORS.get("silver")

    if level == "warn":
        color = MAIN_COLORS.get("yellow")
    elif level == "error":
        color = MAIN_COLORS.get("red")

    print(f"{color}[{now}] [{emoji}] {message} {MAIN_COLORS['reset']}")


# -------------------- 🌟 Pretty Log --------------------
def pretty_log(
    tag: str = None,
    message: str = "",
    *,
    label: str = None,
    bot: commands.Bot = None,
    include_trace: bool = True,
):
    """
    Colored logging with timestamp. Automatically sends error/critical/warn to Discord channel.
    """
    prefix = TAGS.get(tag) if tag else ""
    prefix_part = f"[{prefix}] " if prefix else ""
    label_str = f"[{label}] " if label else ""

    # Choose color
    if tag in ("critical", "error"):
        color = COLOR_RED
    elif tag == "warn":
        color = COLOR_YELLOW
    else:
        color = COLOR_SILVER

    now = datetime.now().strftime("%H:%M:%S")
    log_message = f"{color}[{now}] {prefix_part}{label_str}{message}{COLOR_RESET}"
    print(log_message)

    # Print traceback in console
    if include_trace and tag in ("error", "critical"):
        traceback.print_exc()

    bot_to_use = bot or BOT_INSTANCE

    # Send to Discord channel if needed
    if bot_to_use and tag in ("critical", "error", "warn"):
        try:
            channel = bot_to_use.get_channel(CRITICAL_LOG_CHANNEL_ID)
            if channel:
                full_message = f"{prefix_part}{label_str}{message}"
                if include_trace and tag in ("error", "critical"):
                    full_message += f"\n```py\n{traceback.format_exc()}```"
                if len(full_message) > 2000:
                    full_message = full_message[:1997] + "..."
                bot_to_use.loop.create_task(channel.send(full_message))
        except Exception:
            print("[❌ ERROR] Failed to send log to bot channel:")
            traceback.print_exc()


# -------------------- 🎀 UI Error --------------------
def log_ui_error(
    *,
    error: Exception,
    interaction: discord.Interaction = None,
    label: str = "UI",
    bot: commands.Bot = None,
    include_trace: bool = True,
):
    """Logs UI errors with automatic Discord reporting."""
    location_info = ""
    if interaction:
        user = interaction.user
        location_info = f"User: {user} ({user.id}) | Channel: {interaction.channel} ({interaction.channel_id})"

    error_message = f"UI error occurred. {location_info}".strip()
    now = datetime.now().strftime("%H:%M:%S")

    print(
        f"{COLOR_RED}[{now}] [🚨 CRITICAL] {label} error: {error_message}{COLOR_RESET}"
    )

    if include_trace:
        traceback.print_exception(type(error), error, error.__traceback__)

    bot_to_use = bot or BOT_INSTANCE

    pretty_log(
        "error",
        error_message,
        label=label,
        bot=bot_to_use,
        include_trace=include_trace,
    )

    if bot_to_use:
        try:
            channel = bot_to_use.get_channel(CRITICAL_LOG_CHANNEL_ID)
            if channel:
                embed = discord.Embed(
                    title=f"⚠️ UI Error Logged [{label}]",
                    description=f"{location_info or '*No interaction data*'}",
                    color=0xFF5555,
                )
                if include_trace:
                    trace_text = "".join(
                        traceback.format_exception(
                            type(error), error, error.__traceback__
                        )
                    )
                    if len(trace_text) > 1000:
                        trace_text = trace_text[:1000] + "..."
                    embed.add_field(
                        name="Traceback", value=f"```py\n{trace_text}```", inline=False
                    )
                bot_to_use.loop.create_task(channel.send(embed=embed))
        except Exception:
            print("[❌ ERROR] Failed to send UI error to bot log channel:")
            traceback.print_exc()
