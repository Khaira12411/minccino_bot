# utils/debug_helpers.py
from utils.loggers.pretty_logs import pretty_log

# Default can be False, but each file can override
DEBUG = False


async def debug_log(source: str, message: str, debug_enabled: bool | None = None):
    """
    Logs a debug message if debug is enabled.
    `debug_enabled` overrides the global DEBUG flag for this call.
    """
    if debug_enabled is None:
        debug_enabled = DEBUG

    if debug_enabled:
        pretty_log(tag="info", message=f"[🧪 {source.upper()} DEBUG] {message}")
