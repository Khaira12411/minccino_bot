# utils/database/jsonb_helper.py
import json
from typing import Any, Optional
import asyncpg

from utils.loggers.pretty_logs import (
    pretty_log,
)
# Example usage of jsonb_helper with nested reminders

"""
Example usage of reminder_json helper functions with nested JSON:

from utils.database import reminder_json

# 1️⃣ Create a new row for user 123
await reminder_json.set_json_field(
    bot,
    "user_pokemeow_reminders",
    "user_id",
    123,
    "reminders",
    {
        "relics": {"has_exchanged": False, "enabled": False},
        "catchbot": {"enabled": True},
    }
)

# 2️⃣ Update a single nested key
await reminder_json.update_json_key(
    bot,
    "user_pokemeow_reminders",
    "user_id",
    123,
    "reminders",
    "relics.has_exchanged",
    True
)

# 3️⃣ Merge multiple nested keys at once
await reminder_json.merge_json_fields(
    bot,
    "user_pokemeow_reminders",
    "user_id",
    123,
    "reminders",
    {
        "relics.enabled": True,
        "catchbot.enabled": False
    }
)

# 4️⃣ Fetch the final JSONB object
final = await reminder_json.get_json_field(
    bot,
    "user_pokemeow_reminders",
    "user_id",
    123,
    "reminders"
)

print(final)

# Expected output:
# {
#     "relics": {"has_exchanged": True, "enabled": True},
#     "catchbot": {"enabled": False}
# }
"""


# 💠────────────────────────────────────────────
# [🟣 HELPER] JSONB field manager
# ─────────────────────────────────────────────
def _to_pg_json_path(path: str) -> str:
    """
    Convert a dot-separated path to PostgreSQL JSONB path format.
    Example: 'relics.has_exchanged' -> '{relics,has_exchanged}'
    """
    return "{" + ",".join(path.split(".")) + "}"


async def get_json_field(
    bot,
    table: str,
    key_column: str,
    key_value: Any,
    json_column: str,
) -> Optional[dict]:
    """
    Fetch a JSONB column and return it as a Python dict.

    Usage:
    ```python
    reminders = await get_json_field(bot, "user_pokemeow_reminders", "user_id", 123, "reminders")
    ```
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                f"SELECT {json_column} FROM {table} WHERE {key_column}=$1",
                key_value,
            )
        data = row[json_column] if row else None
        pretty_log(
            tag="db",
            message=f"Fetched {json_column} for {table}.{key_column}={key_value}: {data}",
            label="JSONB",
            bot=bot,
        )
        return data
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to fetch {json_column} from {table}: {e}",
            label="JSONB",
            bot=bot,
        )
        return None


async def set_json_field(
    bot,
    table: str,
    key_column: str,
    key_value: Any,
    json_column: str,
    new_data: dict,
) -> None:
    """
    Insert or update a full JSONB dict.

    Usage:
    ```python
    await set_json_field(
        bot,
        "user_pokemeow_reminders",
        "user_id",
        123,
        "reminders",
        {"relics": {"has_exchanged": False, "enabled": False}, "catchbot": {"enabled": True}}
    )
    ```
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                f"""
                INSERT INTO {table} ({key_column}, {json_column})
                VALUES ($1, $2)
                ON CONFLICT ({key_column}) DO UPDATE
                SET {json_column} = EXCLUDED.{json_column}
                """,
                key_value,
                json.dumps(new_data),
            )
        pretty_log(
            tag="db",
            message=f"Set {json_column} for {table}.{key_column}={key_value} → {new_data}",
            label="JSONB",
            bot=bot,
        )
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to set {json_column} in {table}: {e}",
            label="JSONB",
            bot=bot,
        )


async def update_json_key(
    bot,
    table: str,
    key_column: str,
    key_value: Any,
    json_column: str,
    field_path: str,
    value: Any,
) -> None:
    """
    Update a single key (supports nested keys) inside a JSONB column.

    Usage:
    ```python
    await update_json_key(
        bot,
        "user_pokemeow_reminders",
        "user_id",
        123,
        "reminders",
        "relics.has_exchanged",
        True
    )
    ```
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                f"""
                UPDATE {table}
                SET {json_column} = jsonb_set(
                    COALESCE({json_column}, '{{}}'::jsonb),
                    $2,
                    to_jsonb($3::text)
                )
                WHERE {key_column} = $1
                """,
                key_value,
                _to_pg_json_path(field_path),
                str(value),
            )
        pretty_log(
            tag="db",
            message=f"Updated {json_column}.{field_path} for {table}.{key_column}={key_value} → {value}",
            label="JSONB",
            bot=bot,
        )
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to update {json_column}.{field_path} in {table}: {e}",
            label="JSONB",
            bot=bot,
        )


async def merge_json_fields(
    bot,
    table: str,
    key_column: str,
    key_value: Any,
    json_column: str,
    updates: dict,
) -> None:
    """
    Merge multiple key-value pairs (supports nested keys) into a JSONB column in one query.

    Usage:
    ```python
    await merge_json_fields(
        bot,
        "user_pokemeow_reminders",
        "user_id",
        123,
        "reminders",
        {
            "relics.has_exchanged": True,
            "relics.enabled": False,
            "catchbot.enabled": True
        }
    )
    ```
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            query = f"COALESCE({json_column}, '{{}}'::jsonb)"
            params = [key_value]
            param_index = 2

            for key, value in updates.items():
                query = f"jsonb_set({query}, ${param_index}, to_jsonb(${param_index + 1}::text))"
                params.extend([_to_pg_json_path(key), str(value)])
                param_index += 2

            await conn.execute(
                f"UPDATE {table} SET {json_column} = {query} WHERE {key_column} = $1",
                *params,
            )

        pretty_log(
            tag="db",
            message=f"Merged fields into {json_column} for {table}.{key_column}={key_value} → {updates}",
            label="JSONB",
            bot=bot,
        )
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to merge fields into {json_column} in {table}: {e}",
            label="JSONB",
            bot=bot,
        )
