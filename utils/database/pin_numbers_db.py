import discord

from utils.loggers.pretty_logs import pretty_log

# SQL SCRIPT
"""CREATE TABLE pin_numbers (
    user_id BIGINT PRIMARY KEY,
    user_name VARCHAR(255),
    pokemon_pin TEXT,
    fish_pin TEXT,
    sz_pin TEXT
);"""


async def upsert_pin_number_type(
    bot: discord.Client,
    user_id: int,
    user_name: str,
    type: str,
    value: str,
):
    pin_type = f"{type}_pin"
    async with bot.pg_pool.acquire() as conn:
        await conn.execute(
            f"""
            INSERT INTO pin_numbers (user_id, user_name, {pin_type})
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id) DO UPDATE
            SET {pin_type} = EXCLUDED.{pin_type},
                user_name = EXCLUDED.user_name;
            """,
            user_id,
            user_name,
            value,
        )


async def fetch_pin_number_type(
    bot: discord.Client,
    user_id: int,
    type: str,
) -> str | None:
    pin_type = f"{type}_pin"
    async with bot.pg_pool.acquire() as conn:
        row = await conn.fetchrow(
            f"""
            SELECT {pin_type}
            FROM pin_numbers
            WHERE user_id = $1;
            """,
            user_id,
        )
        return row[pin_type] if row else None


async def fetch_all_pin_numbers(
    bot: discord.Client,
    user_id: int,
) -> dict[str, str] | None:
    async with bot.pg_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT pokemon_pin, fish_pin, sz_pin
            FROM pin_numbers
            WHERE user_id = $1;
            """,
            user_id,
        )
        return dict(row) if row else None


async def remove_user_pin_numbers(
    bot: discord.Client,
    user_id: int,
):
    async with bot.pg_pool.acquire() as conn:
        await conn.execute(
            """
            DELETE FROM pin_numbers
            WHERE user_id = $1;
            """,
            user_id,
        )
