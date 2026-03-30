import discord

from utils.loggers.pretty_logs import pretty_log

# SQL SCRIPT
"""CREATE TABLE watering_can (
    user_id BIGINT PRIMARY KEY,
    user_name TEXT,
    watering_can TEXT
);"""

async def upsert_watering_can(
    bot: discord.Client,
    user_id: int,
    user_name: str,
    watering_can_emoji: str,
):
    """Upserts a watering can for the given user_id."""
    async with bot.pg_pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO watering_can (user_id, user_name, watering_can)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id) DO UPDATE SET
                user_name = EXCLUDED.user_name,
                watering_can = EXCLUDED.watering_can
            """,
            user_id,
            user_name,
            watering_can_emoji,
        )
        pretty_log(
            "info",
            f"Upserted watering can for user_id {user_id}: {watering_can_emoji}",
        )

async def remove_watering_can(bot: discord.Client, user_id: int):
    """Removes the watering can entry for the given user_id."""
    async with bot.pg_pool.acquire() as conn:
        await conn.execute(
            """
            DELETE FROM watering_can
            WHERE user_id = $1
            """,
            user_id,
        )
        pretty_log(
            "info",
            f"Removed watering can for user_id {user_id}",
        )

async def get_watering_can(bot: discord.Client, user_id: int) -> str:
    """Fetches the watering can emoji for the given user_id."""
    async with bot.pg_pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT watering_can FROM watering_can
            WHERE user_id = $1
            """,
            user_id,
        )
        if row:
            watering_can_emoji = row["watering_can"]
            pretty_log(
                "info",
                f"Fetched watering can for user_id {user_id}: {watering_can_emoji}",
            )
            return watering_can_emoji
        else:
            pretty_log(
                "info",
                f"No watering can found for user_id {user_id}",
            )
            return None
