# ──────────────────────────────
# 📦 Boosted Channels Helpers
# ──────────────────────────────
from utils.loggers.pretty_logs import pretty_log


# Fetch all rows
async def fetch_all_boosted_channels(bot) -> list[dict]:
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch(
                "SELECT id, channel_id, channel_name FROM boosted_channels ORDER BY id"
            )
            return [dict(row) for row in rows]
    except Exception as e:
        pretty_log("error", f"Failed to fetch all boosted channels: {e}", bot=bot)
        return []


# Fetch single channel by channel_id
async def fetch_boosted_channel(bot, channel_id: int) -> dict | None:
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT id, channel_id, channel_name FROM boosted_channels WHERE channel_id = $1",
                channel_id,
            )
            return dict(row) if row else None
    except Exception as e:
        pretty_log(
            "error", f"Failed to fetch boosted channel {channel_id}: {e}", bot=bot
        )
        return None


# Insert / upsert a channel
async def insert_boosted_channel(bot, channel_id: int, channel_name: str):
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO boosted_channels (channel_id, channel_name)
                VALUES ($1, $2)
                ON CONFLICT (channel_id)
                DO UPDATE SET channel_name = EXCLUDED.channel_name
                """,
                channel_id,
                channel_name,
            )
    except Exception as e:
        pretty_log(
            "error",
            f"Failed to insert/update boosted channel {channel_id}: {e}",
            bot=bot,
        )


# Delete a channel by channel_id
async def delete_boosted_channel(bot, channel_id: int):
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM boosted_channels WHERE channel_id = $1", channel_id
            )
    except Exception as e:
        pretty_log(
            "error", f"Failed to delete boosted channel {channel_id}: {e}", bot=bot
        )
