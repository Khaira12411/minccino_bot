import asyncio
import discord

_TRANSIENT_HTTP_STATUSES = {500, 502, 503, 504}
_MAX_RETRY_ATTEMPTS = 3
_BASE_RETRY_DELAY_SECONDS = 1.0


async def _retry_discord_call(coro_func, *args, **kwargs):
    """Retry transient Discord API failures with exponential backoff."""
    for attempt in range(1, _MAX_RETRY_ATTEMPTS + 1):
        try:
            return await coro_func(*args, **kwargs)
        except discord.DiscordServerError:
            if attempt == _MAX_RETRY_ATTEMPTS:
                raise
            await asyncio.sleep(_BASE_RETRY_DELAY_SECONDS * (2 ** (attempt - 1)))
        except discord.HTTPException as e:
            if (
                e.status not in _TRANSIENT_HTTP_STATUSES
                or attempt == _MAX_RETRY_ATTEMPTS
            ):
                raise
            await asyncio.sleep(_BASE_RETRY_DELAY_SECONDS * (2 ** (attempt - 1)))
