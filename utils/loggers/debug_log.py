# utils/loggers/smart_debug.py
import logging
import inspect

# -----------------------------
# 🔹 Central Logger Setup
# -----------------------------
logger = logging.getLogger("smart_debug")
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
formatter = logging.Formatter("[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)

# -----------------------------
# 🔹 Global Debug Toggles
# -----------------------------
DEBUG_TOGGLES: dict[str, bool] = {}


def enable_debug(func_path: str):
    DEBUG_TOGGLES[func_path] = True


def disable_debug(func_path: str):
    DEBUG_TOGGLES[func_path] = False


def debug_enabled(func_path: str) -> bool:
    return DEBUG_TOGGLES.get(func_path, False)


def debug_log(message: str, highlight: bool = False, disabled: bool = False):
    """
    Logs a debug message if enabled for the calling function/module.
    Optional `highlight=True` will make the entire line stand out.
    Optional `disabled=True` will skip logging even if debug is enabled.
    """
    if disabled:
        return

    stack = inspect.stack()
    caller_frame = stack[1]
    func_name = caller_frame.function
    module_name = caller_frame.frame.f_globals.get("__name__", "__main__")
    key = f"{module_name}.{func_name}"

    if not debug_enabled(key):
        return

    log_line = f"[{key}] {message}"

    # ANSI escape code for bright cyan highlight for the whole line
    if highlight:
        log_line = f"\033[96m{log_line}\033[0m"

    logger.debug(log_line)
