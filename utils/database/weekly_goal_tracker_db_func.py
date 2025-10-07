# 💠────────────────────────────────────────────
# [📦 HELPERS] Weekly Goal Tracker DB Functions
# 💠────────────────────────────────────────────
from typing import List
import discord


async def upsert_weekly_goal(
    bot: discord.Client,
    user:discord.Member,
    channel_id: int | None = None,
    pokemon_caught: int = 0,
    fish_caught: int = 0,
    battles_won: int = 0,
):
    """Insert or update a user's weekly goal stats."""
    from utils.cache.weekly_goal_tracker_cache import upsert_weekly_goal_cache
    user_id = user.id
    user_name = user.name

    query = """
        INSERT INTO weekly_goal_tracker (
            user_id, user_name, channel_id, pokemon_caught, fish_caught, battles_won
        )
        VALUES ($1, $2, $3, $4, $5, $6)
        ON CONFLICT(user_id) DO UPDATE SET
            user_name = EXCLUDED.user_name,
            channel_id = EXCLUDED.channel_id,
            pokemon_caught = EXCLUDED.pokemon_caught,
            fish_caught = EXCLUDED.fish_caught,
            battles_won = EXCLUDED.battles_won;
    """
    async with bot.pg_pool.acquire() as conn:
        await conn.execute(
            query,
            user_id,
            user_name,
            channel_id,
            pokemon_caught,
            fish_caught,
            battles_won,
        )
    # Also update cache
    upsert_weekly_goal_cache(
        user,
        channel_id=channel_id,
        pokemon_caught=pokemon_caught,
        fish_caught=fish_caught,
        battles_won=battles_won,
    )


async def fetch_all_weekly_goals(bot: discord.Client) -> List[dict]:
    """Fetch all rows from weekly_goal_tracker."""
    query = "SELECT * FROM weekly_goal_tracker;"
    async with bot.pg_pool.acquire() as conn:
        rows = await conn.fetch(query)
        # Convert asyncpg.Record to dict
        return [dict(row) for row in rows]
