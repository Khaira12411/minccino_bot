import json
from dataclasses import dataclass

import discord

from utils.essentials.ball_names import normalize_ball_type
from utils.loggers.pretty_logs import pretty_log

# SQL SCRIPT
"""CREATE TABLE IF NOT EXISTS catchlist (
    user_id BIGINT PRIMARY KEY,
    user_name TEXT NOT NULL,
    catchlist_date TEXT NOT NULL,
    catchlist_mons JSONB,
    rank_name TEXT,
    total_exp INTEGER,
    exp_needed INTEGER
);"""


async def upsert_catchlist(
    bot: discord.Client,
    user_id: int,
    user_name: str,
    catchlist_date: str,
    catchlist_mons: list[dict],
    rank_name: str | None = None,
    total_exp: int | None = None,
    exp_needed: int | None = None,
):
    async with bot.pg_pool.acquire() as conn:
        await conn.execute(
            """
                INSERT INTO catchlist (user_id, user_name, catchlist_date, catchlist_mons, rank_name, total_exp, exp_needed)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                ON CONFLICT (user_id) DO UPDATE
                SET user_name = EXCLUDED.user_name,
                    catchlist_date = EXCLUDED.catchlist_date,
                    catchlist_mons = EXCLUDED.catchlist_mons,
                    rank_name = EXCLUDED.rank_name,
                    total_exp = EXCLUDED.total_exp,
                    exp_needed = EXCLUDED.exp_needed;
                """,
            user_id,
            user_name,
            catchlist_date,
            json.dumps(catchlist_mons, ensure_ascii=False),
            rank_name,
            total_exp,
            exp_needed,
        )
        from utils.cache.catchlist_cache import upsert_catchlist_cache

        upsert_catchlist_cache(
            user_id,
            {
                "user_id": user_id,
                "user_name": user_name,
                "catchlist_date": catchlist_date,
                "catchlist_mons": catchlist_mons,
                "rank_name": rank_name,
                "total_exp": total_exp,
                "exp_needed": exp_needed,
            },
        )


async def upsert_catchlist_rank(
    bot: discord.Client,
    user_id: int,
    user_name: str,
    catchlist_date: str,
    rank_name: str,
    total_exp: int,
    exp_needed: int,
):
    async with bot.pg_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
                INSERT INTO catchlist (
                    user_id, user_name, catchlist_date, catchlist_mons,
                    rank_name, total_exp, exp_needed
                )
                VALUES ($1, $2, $3, '[]'::jsonb, $4, $5, $6)
                ON CONFLICT (user_id) DO UPDATE
                SET user_name = EXCLUDED.user_name,
                    rank_name = EXCLUDED.rank_name,
                    total_exp = EXCLUDED.total_exp,
                    exp_needed = EXCLUDED.exp_needed
                RETURNING *;
                """,
            user_id,
            user_name,
            catchlist_date,
            rank_name,
            total_exp,
            exp_needed,
        )
        from utils.cache.catchlist_cache import upsert_catchlist_cache

        upsert_catchlist_cache(user_id, dict(row))


async def fetch_all_catchlists(bot: discord.Client):
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM catchlist")
            return [dict(row) for row in rows]
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Error fetching all catchlists: {e}",
            label="CatchlistDB",
        )
        return []


async def fetch_catchlist_by_user(bot: discord.Client, user_id: int):
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM catchlist WHERE user_id = $1", user_id
            )
            return dict(row) if row else None
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Error fetching catchlist for user {user_id}: {e}",
            label="CatchlistDB",
        )
        return None


async def has_empty_catchlist(bot: discord.Client, user_id: int) -> bool:
    """Return whether an existing user has no saved catchlist Pokémon."""
    async with bot.pg_pool.acquire() as conn:
        return await conn.fetchval(
            """
            SELECT EXISTS (
                SELECT 1
                FROM catchlist
                WHERE user_id = $1
                  AND (
                    catchlist_mons IS NULL
                    OR catchlist_mons = '[]'::jsonb
                    OR catchlist_mons = 'null'::jsonb
                  )
            )
            """,
            user_id,
        )


async def reset_all_catchlist(bot: discord.Client):
    # Reset all catchlist by deleting all columns except user_id and user_name for new monthly catchlist
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute("""
                UPDATE catchlist
                SET catchlist_date = NULL,
                    catchlist_mons = '[]'::jsonb,
                    rank_name = NULL,
                    total_exp = NULL,
                    exp_needed = NULL;
                """)
        from utils.cache.catchlist_cache import reset_catchlist_cache

        reset_catchlist_cache()

    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Error resetting all catchlists: {e}",
            label="CatchlistDB",
        )


async def update_completion_status(
    bot: discord.Client,
    user_id: int,
    pokemon_name: str,
    catch_type: str,
    completion: bool,
):
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE catchlist
                SET catchlist_mons = jsonb_set(
                    catchlist_mons,
                    ('{' || (i - 1) || ',completion}')::text[],
                    to_jsonb($4::boolean)
                )
                FROM (
                    SELECT i
                    FROM catchlist, jsonb_array_elements(catchlist_mons) WITH ORDINALITY arr(mon, i)
                    WHERE user_id = $1
                      AND mon->>'pokemon_name' = $2
                      AND mon->>'catch_type' = $3
                ) sub
                WHERE user_id = $1
                """,
                user_id,
                pokemon_name,
                catch_type,
                completion,
            )
            from utils.cache.catchlist_cache import update_mon_completion_in_catchlist

            update_mon_completion_in_catchlist(
                user_id, pokemon_name, catch_type, completion
            )

    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Error updating completion status for user {user_id}, pokemon {pokemon_name}: {e}",
            label="CatchlistDB",
        )


@dataclass(frozen=True)
class CatchlistCatchResult:
    rank_up: bool
    rank_data_missing: bool
    exp_needed: int | None


async def apply_catchlist_catch(
    bot: discord.Client,
    user_id: int,
    pokemon_name: str,
    catch_type: str,
    ball_used: str,
) -> CatchlistCatchResult | None:
    """Atomically complete an eligible Pokémon and update known EXP values."""
    async with bot.pg_pool.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                "SELECT * FROM catchlist WHERE user_id = $1 FOR UPDATE", user_id
            )
            if row is None:
                return None
            record = dict(row)
            mons = record["catchlist_mons"]
            if isinstance(mons, str):
                mons = json.loads(mons)
            if not isinstance(mons, list):
                raise ValueError(f"Invalid catchlist Pokémon for user {user_id}")

            matching = [
                mon
                for mon in mons
                if mon["pokemon_name"].lower() == pokemon_name.lower()
                and mon["catch_type"].lower() == catch_type.lower()
            ]
            if not matching:
                return None
            if len(matching) != 1:
                raise ValueError(
                    f"Duplicate catchlist entry for user {user_id}: {pokemon_name} ({catch_type})"
                )
            mon = matching[0]
            if mon["completion"] or normalize_ball_type(
                mon["ball_type"]
            ) != normalize_ball_type(ball_used):
                return None

            exp_amount = mon["exp_amount"]
            if (
                not isinstance(exp_amount, int)
                or isinstance(exp_amount, bool)
                or exp_amount < 0
            ):
                raise ValueError(
                    f"Invalid catchlist EXP for user {user_id}: {pokemon_name}"
                )
            total_exp = record["total_exp"]
            exp_needed = record["exp_needed"]
            rank_data_missing = total_exp is None or exp_needed is None
            rank_up = (
                exp_needed is not None and exp_needed > 0 and exp_needed <= exp_amount
            )
            if total_exp is not None:
                total_exp += exp_amount
            if exp_needed is not None:
                exp_needed = (
                    None if exp_needed <= exp_amount else exp_needed - exp_amount
                )
            mon["completion"] = True
            await conn.execute(
                """
                UPDATE catchlist
                SET catchlist_mons = $2, total_exp = $3, exp_needed = $4
                WHERE user_id = $1
                """,
                user_id,
                json.dumps(mons, ensure_ascii=False),
                total_exp,
                exp_needed,
            )
            record.update(
                catchlist_mons=mons, total_exp=total_exp, exp_needed=exp_needed
            )

        from utils.cache.catchlist_cache import upsert_catchlist_cache

        upsert_catchlist_cache(user_id, record)
    return CatchlistCatchResult(
        rank_up=rank_up, rank_data_missing=rank_data_missing, exp_needed=exp_needed
    )


async def update_user_exp(
    bot: discord.Client, user_id: int, new_exp_needed: int, new_total_exp: int
):
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE catchlist
                SET exp_needed = $2,
                    total_exp = $3
                WHERE user_id = $1
                """,
                user_id,
                new_exp_needed,
                new_total_exp,
            )
            from utils.cache.catchlist_cache import update_user_exp_in_catchlist

            update_user_exp_in_catchlist(user_id, new_exp_needed, new_total_exp)
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Error updating user exp for user {user_id}: {e}",
            label="CatchlistDB",
        )
