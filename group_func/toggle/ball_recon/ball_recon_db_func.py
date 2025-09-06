# ─────────────────────────────────────────────
#       🟣 User Ball Recommendations DB
# ─────────────────────────────────────────────

from typing import Optional

from asyncpg import Connection

from utils.loggers.pretty_logs import pretty_log

TABLE_NAME = "user_ball_recommendations"
import json

from utils.loggers.pretty_logs import pretty_log


async def fetch_all_user_recs(bot) -> list[dict]:
    """
    Return all rows in user_ball_recommendations table as list of dicts.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch(f"SELECT * FROM {TABLE_NAME}")
            return [dict(row) for row in rows]
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to fetch all user ball recommendations: {e}",
            label="STRAYMONS",
            bot=bot,
        )
        return []


async def fetch_user_rec(bot, user_id: int) -> Optional[dict]:
    """
    Fetch a single user's ball recommendations by user_id.
    Returns None if not found.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                f"SELECT * FROM {TABLE_NAME} WHERE user_id = $1", user_id
            )
            return dict(row) if row else None
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to fetch ball recommendation for user {user_id}: {e}",
            label="STRAYMONS",
            bot=bot,
        )
        return None


async def upsert_user_rec(
    bot,
    user_id: int,
    user_name: str,
    is_patreon: bool = False,
    catch_rate_bonus: float = 0,
    held_items: dict = None,
    pokemon: dict = None,
    fishing: dict = None,
):
    """
    Insert or update a user's ball recommendation preferences.
    Converts dicts to JSON strings for asyncpg.
    """
    # Ensure dicts
    held_items = held_items or {}
    pokemon = pokemon or {}
    fishing = fishing or {}

    # Serialize to JSON strings
    held_items_json = json.dumps(held_items)
    pokemon_json = json.dumps(pokemon)
    fishing_json = json.dumps(fishing)

    query = f"""
    INSERT INTO {TABLE_NAME}
        (user_id, user_name, is_patreon, catch_rate_bonus, held_items, pokemon, fishing)
    VALUES ($1, $2, $3, $4, $5::jsonb, $6::jsonb, $7::jsonb)
    ON CONFLICT (user_id)
    DO UPDATE SET
        user_name = EXCLUDED.user_name,
        is_patreon = EXCLUDED.is_patreon,
        catch_rate_bonus = EXCLUDED.catch_rate_bonus,
        held_items = EXCLUDED.held_items,
        pokemon = EXCLUDED.pokemon,
        fishing = EXCLUDED.fishing,
        last_updated = NOW()
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                query,
                user_id,
                user_name,
                is_patreon,
                catch_rate_bonus,
                held_items_json,
                pokemon_json,
                fishing_json,
            )
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to upsert ball recommendation for user {user_id}: {e}",
            label="STRAYMONS",
            bot=bot,
        )


async def delete_user_rec(bot, user_id: int):
    """
    Delete a user's ball recommendation preferences by user_id.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(f"DELETE FROM {TABLE_NAME} WHERE user_id = $1", user_id)
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to delete ball recommendation for user {user_id}: {e}",
            label="STRAYMONS",
            bot=bot,
        )


# ─────────────────────────────────────────────
#       🟣 User Ball Recommendations Partial Updates
# ─────────────────────────────────────────────


TABLE_NAME = "user_ball_recommendations"


import json


async def update_held_items(bot, user_id: int, held_items: dict):
    """
    Update only the held_items JSONB column for a user.
    """
    query = f"""
    UPDATE {TABLE_NAME}
    SET held_items = $1::jsonb,
        last_updated = NOW()
    WHERE user_id = $2
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(query, json.dumps(held_items), user_id)
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to update held_items for user {user_id}: {e}",
            label="STRAYMONS",
            bot=bot,
        )


async def update_pokemon(bot, user_id: int, pokemon: dict):
    """
    Update only the pokemon JSONB column for a user.
    """
    query = f"""
    UPDATE {TABLE_NAME}
    SET pokemon = $1::jsonb,
        last_updated = NOW()
    WHERE user_id = $2
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(query, json.dumps(pokemon), user_id)
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to update pokemon for user {user_id}: {e}",
            label="STRAYMONS",
            bot=bot,
        )


async def update_fishing(bot, user_id: int, fishing: dict):
    """
    Update only the fishing JSONB column for a user.
    """
    query = f"""
    UPDATE {TABLE_NAME}
    SET fishing = $1::jsonb,
        last_updated = NOW()
    WHERE user_id = $2
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(query, json.dumps(fishing), user_id)
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to update fishing for user {user_id}: {e}",
            label="STRAYMONS",
            bot=bot,
        )


# ─────────────────────────────────────────────
#       🟣 Update Patreon or Catch Rate Bonus Separately
# ─────────────────────────────────────────────


async def update_is_patreon(bot, user_id: int, is_patreon: bool):
    """
    Update only the is_patreon column for a user.
    """
    query = f"""
    UPDATE {TABLE_NAME}
    SET is_patreon = $1,
        last_updated = NOW()
    WHERE user_id = $2
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(query, is_patreon, user_id)
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to update is_patreon for user {user_id}: {e}",
            label="STRAYMONS",
            bot=bot,
        )


async def update_catch_rate_bonus(bot, user_id: int, catch_rate_bonus: float):
    """
    Update only the catch_rate_bonus column for a user.
    """
    query = f"""
    UPDATE {TABLE_NAME}
    SET catch_rate_bonus = $1,
        last_updated = NOW()
    WHERE user_id = $2
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(query, catch_rate_bonus, user_id)
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to update catch_rate_bonus for user {user_id}: {e}",
            label="STRAYMONS",
            bot=bot,
        )

# ─────────────────────────────────────────────
#       🟣 User Ball Recommendations Enabled Toggle
# ─────────────────────────────────────────────


async def update_enabled(bot, user_id: int, enabled: bool):
    """
    Update only the enabled column for a user.
    """
    query = f"""
    UPDATE {TABLE_NAME}
    SET enabled = $1,
        last_updated = NOW()
    WHERE user_id = $2
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(query, enabled, user_id)
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to update enabled for user {user_id}: {e}",
            label="STRAYMONS",
            bot=bot,
        )


async def fetch_enabled(bot, user_id: int) -> bool:
    """
    Fetch the enabled status for a user.
    Returns True if not set (default enabled).
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                f"SELECT enabled FROM {TABLE_NAME} WHERE user_id = $1", user_id
            )
            return row["enabled"] if row and "enabled" in row else True
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to fetch enabled status for user {user_id}: {e}",
            label="STRAYMONS",
            bot=bot,
        )
        return True



async def update_display_mode(bot, user_id: int, category: str, mode: str):
    """
    Update the 'display_mode' key inside the JSONB column for a user/category.
    """
    column_name = category  # e.g., "pokemon", "held_items", "fishing"

    query = f"""
        UPDATE user_ball_recommendations
        SET {column_name} = jsonb_set(
            coalesce({column_name}, '{{}}')::jsonb,
            '{{display_mode}}',
            to_jsonb($1::text),
            true
        )
        WHERE user_id = $2
    """

    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(query, mode, user_id)
    except Exception as e:
        from utils.loggers.pretty_logs import pretty_log

        pretty_log(
            "error",
            f"Failed to update display_mode for user {user_id}, category {category}: {e}",
            label="STRAYMONS",
            bot=bot,
        )
