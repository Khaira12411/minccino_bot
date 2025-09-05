from typing import Optional
import json
from utils.loggers.pretty_logs import pretty_log
from utils.essentials.db_json_helper import *


# 💠────────────────────────────────────────────
# [🟣 DB FUNCTION] Fetch a single user's row
# ─────────────────────────────────────────────
async def fetch_user_row(bot, user_id: int) -> Optional[dict]:
    """
    Fetch a single user's row from user_pokemeow_reminders.
    """
    query = "SELECT * FROM user_pokemeow_reminders WHERE user_id = $1"

    try:
        # Try via pool
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(query, user_id)
    except Exception as e:
        pretty_log("warn", f"Pool fetch failed for {user_id}: {e}", bot=bot)
        try:
            # Fallback raw connection
            raw_conn = await asyncpg.connect(
                dsn=bot.pg_pool.dsn, ssl=bot.pg_pool.ssl_context
            )
            row = await raw_conn.fetchrow(query, user_id)
            await raw_conn.close()
            pretty_log("info", f"[Fallback] Fetched row for {user_id}", bot=bot)
        except Exception as e2:
            pretty_log("error", f"Failed to fetch user row {user_id}: {e2}", bot=bot)
            return None

    if not row:
        return None

    row_dict = dict(row)
    reminders = row_dict.get("reminders")
    if isinstance(reminders, str):
        row_dict["reminders"] = json.loads(reminders)
    return row_dict

# 💠────────────────────────────────────────────
# [🟣 DB FUNCTION] Fetch all rows
# ─────────────────────────────────────────────
async def fetch_all_rows(bot) -> list[dict]:
    """
    Fetch all rows from user_pokemeow_reminders.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM user_pokemeow_reminders")
        result = []
        for row in rows:
            row_dict = dict(row)
            reminders = row_dict.get("reminders")
            if isinstance(reminders, str):
                row_dict["reminders"] = json.loads(reminders)
            result.append(row_dict)
        return result
    except Exception as e:
        pretty_log("error", f"Failed to fetch all user rows: {e}", bot=bot)
        return []


# 💠────────────────────────────────────────────
# [🟣 DB FUNCTION] Upsert a user's row
# ─────────────────────────────────────────────
import asyncpg
import json
from utils.loggers.pretty_logs import pretty_log


async def old_upsert_user_row(bot, user_id: int, user_name: str, reminders: dict = None):
    """
    Insert a new user row or update the existing row (upsert).
    Uses SafePool first; falls back to raw connection if pool fails.
    """
    reminders = reminders or {}
    query = """
        INSERT INTO user_pokemeow_reminders (user_id, user_name, reminders)
        VALUES ($1, $2, $3)
        ON CONFLICT (user_id) DO UPDATE
        SET user_name = EXCLUDED.user_name,
            reminders = EXCLUDED.reminders
    """

    try:
        # Try normal pool acquire
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(query, user_id, user_name, json.dumps(reminders))
        pretty_log("info", f"Upserted user {user_id} successfully.", bot=bot)

    except Exception as e:
        pretty_log(
            "warn",
            f"Pool upsert failed for user {user_id}, retrying with raw connection: {e}",
            bot=bot,
        )
        try:
            # Fallback: raw connection
            raw_conn = await asyncpg.connect(
                dsn=bot.pg_pool.dsn, ssl=bot.pg_pool.ssl_context
            )
            await raw_conn.execute(query, user_id, user_name, json.dumps(reminders))
            await raw_conn.close()
            pretty_log(
                "info",
                f"[Fallback] Upserted user {user_id} successfully with raw connection.",
                bot=bot,
            )
        except Exception as e2:
            pretty_log(
                "error",
                f"Failed to upsert user {user_id} even with raw connection: {e2}",
                bot=bot,
            )
import copy
import json
from utils.loggers.pretty_logs import pretty_log

# 🔹 Default structures for reminders
RELICS_DEFAULTS = {
    "mode": "off",
    "has_exchanged": False,
    "expiration_timestamp": None,
}

CATCHBOT_DEFAULTS = {
    "mode": "off",
    "repeating": None,
}

REMINDERS_DEFAULTS = {
    "relics": copy.deepcopy(RELICS_DEFAULTS),
    "catchbot": copy.deepcopy(CATCHBOT_DEFAULTS),
}


def merge_with_defaults(reminders: dict) -> dict:
    """
    Merge a reminders dict with defaults.
    Ensures all expected keys exist but keeps user’s data.
    """
    merged = copy.deepcopy(REMINDERS_DEFAULTS)
    for section, defaults in REMINDERS_DEFAULTS.items():
        section_data = reminders.get(section)
        if isinstance(section_data, dict):
            merged[section].update(section_data)
    return merged


async def upsert_user_reminders(bot, user_id: int, user_name: str, updates: dict):
    """
    Incrementally upsert reminders for a user.
    - Creates a row if missing
    - Merges with defaults (new fields auto-added)
    - Applies only the provided updates
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            # 🔹 1. Fetch current row (if any)
            row = await conn.fetchrow(
                "SELECT reminders FROM user_pokemeow_reminders WHERE user_id = $1",
                user_id,
            )

            # 🔹 Safely parse JSON from DB
            if row and row["reminders"]:
                if isinstance(row["reminders"], str):
                    try:
                        current_reminders = json.loads(row["reminders"])
                    except json.JSONDecodeError:
                        current_reminders = {}
                elif isinstance(row["reminders"], dict):
                    current_reminders = row["reminders"]
                else:
                    current_reminders = {}
            else:
                current_reminders = {}

            # 🔹 Merge with defaults
            merged = merge_with_defaults(current_reminders)

            # 🔹 Apply incremental updates (multi-field safe)
            for section, changes in updates.items():
                if section not in merged or not isinstance(merged[section], dict):
                    merged[section] = {}
                if isinstance(changes, dict):
                    merged[section].update(changes)

            # 🔹 Upsert row
            await conn.execute(
                """
                INSERT INTO user_pokemeow_reminders (user_id, user_name, reminders)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id) DO UPDATE
                SET user_name = EXCLUDED.user_name,
                    reminders = EXCLUDED.reminders
                """,
                user_id,
                user_name,
                json.dumps(merged),
            )

        pretty_log("info", f"Incrementally upserted user {user_id}", bot=bot)
        return merged

    except Exception as e:
        pretty_log(
            "error", f"Failed incremental upsert for user {user_id}: {e}", bot=bot
        )
        return None


# 💠────────────────────────────────────────────
# [🟣 DB FUNCTION] Update reminders JSON (supports nested keys)
# ─────────────────────────────────────────────
async def update_user_reminders(bot, user_id: int, updates: dict):
    """
    Merge multiple nested keys into a user's reminders column.

    Handles dotted keys like "relics.mode" safely in Python.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            # Fetch current reminders
            row = await conn.fetchrow(
                "SELECT reminders FROM user_pokemeow_reminders WHERE user_id = $1",
                user_id,
            )
            if not row:
                pretty_log("warn", f"No user row found for {user_id}", bot=bot)
                return

            reminders = row["reminders"] or {}
            if isinstance(reminders, str):
                import json

                reminders = json.loads(reminders)

            # Apply updates (dotted keys)
            for key, value in updates.items():
                parts = key.split(".")
                d = reminders
                for p in parts[:-1]:
                    if p not in d or not isinstance(d[p], dict):
                        d[p] = {}
                    d = d[p]
                d[parts[-1]] = value

            # Write back as JSON
            import json

            await conn.execute(
                "UPDATE user_pokemeow_reminders SET reminders = $1 WHERE user_id = $2",
                json.dumps(reminders),
                user_id,
            )

        pretty_log("info", f"Updated reminders for user {user_id}: {updates}", bot=bot)

    except Exception as e:
        pretty_log(
            "error",
            f"[JSONB] Failed to update reminders for user {user_id}: {e}",
            bot=bot,
        )


# 💠────────────────────────────────────────────
# [🟣 DB FUNCTION] Delete a user's row
# ─────────────────────────────────────────────
async def delete_user_row(bot, user_id: int):
    """
    Delete a user's row from user_pokemeow_reminders.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM user_pokemeow_reminders WHERE user_id = $1",
                user_id,
            )
        pretty_log("info", f"Deleted user row {user_id} successfully.", bot=bot)
    except Exception as e:
        pretty_log("error", f"Failed to delete user row {user_id}: {e}", bot=bot)


# updates a single field
import json


def _deep_set(d: dict, keys: list[str], value):
    """
    Safely set a nested dict value by key path.
    Example: _deep_set(d, ["relics", "expiration_timestamp"], 12345)
    """

    for k in keys[:-1]:
        if k not in d or not isinstance(d[k], dict):
            d[k] = {}
        d = d[k]
    d[keys[-1]] = value


async def update_user_reminders_fields(
    bot, user_id: int, user_name: str, updates: dict
):
    """
    Safely update multiple nested fields in a user's reminders.
    - updates: dict where keys are dotted paths (e.g., "catchbot.schedule.next_run")
               and values are the values to set.
    - Merge-safe: only updates provided fields, keeps all other data intact.
    - Updates both cache and DB incrementally.

    Example:
        await update_user_reminders_fields(
            bot,
            123,
            "TestUser",
            {
                "catchbot.schedule.next_run": 1757217600,
                "relics.has_exchanged": True
            }
        )
    """
    from utils.cache.reminders_cache import user_reminders_cache
    from group_func.toggle.reminders.user_reminders_db_func import upsert_user_reminders

    try:
        # ───────────── Fetch current cache or init ─────────────
        current_reminders = user_reminders_cache.get(user_id, {})

        # ───────────── Apply all updates safely ─────────────
        for field_path, value in updates.items():
            keys = field_path.split(".")
            if not keys:
                raise ValueError(f"Invalid field_path: {field_path}")
            d = current_reminders
            for k in keys[:-1]:
                if k not in d or not isinstance(d[k], dict):
                    d[k] = {}
                d = d[k]
            d[keys[-1]] = value

        # Save back to cache immediately
        user_reminders_cache[user_id] = current_reminders

        # ───────────── Prepare nested update for DB ─────────────
        # Build a dict grouped by top-level section
        nested_updates = {}
        for field_path, value in updates.items():
            keys = field_path.split(".")
            section = keys[0]
            d = nested_updates.setdefault(section, {})
            # Traverse / set the rest
            for k in keys[1:-1]:
                if k not in d or not isinstance(d[k], dict):
                    d[k] = {}
                d = d[k]
            d[keys[-1]] = value

        # ───────────── Upsert to DB ─────────────
        merged = await upsert_user_reminders(bot, user_id, user_name, nested_updates)

        # Update cache with merged DB result for safety
        if merged:
            user_reminders_cache[user_id] = merged

        pretty_log(
            "info",
            f"Updated multiple fields for user {user_id} (cache + DB): {list(updates.keys())}",
            bot=bot,
        )

    except Exception as e:
        pretty_log(
            "error",
            f"Failed to update fields for user {user_id}: {e}",
            bot=bot,
        )


"""await update_user_reminders_field(
    bot, 123, "TestUser", "relics.has_exchanged", True
)

await update_user_reminders_field(
    bot, 123, "TestUser", "catchbot.mode", "dm"
)"""
