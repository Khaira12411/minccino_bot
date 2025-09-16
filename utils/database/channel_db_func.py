from utils.loggers.pretty_logs import pretty_log


# 🍭 Get a registered personal channel
import discord

async def get_registered_personal_channel(
    bot: discord.Client, user_id: int
) -> int | None:
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT channel_id FROM personal_channels WHERE user_id = $1", user_id
            )
            return row["channel_id"] if row else None
    except Exception as e:
        pretty_log("warn", f"Failed to fetch personal channel for user {user_id}: {e}")
        return None
