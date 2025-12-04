# 🟣────────────────────────────────────────────
#        Timers DB Functions for Espeon (bot.pg_pool)
# 🟣────────────────────────────────────────────

from utils.loggers.pretty_logs import pretty_log


# --------------------
#  Upsert a timer setting field for a user
# --------------------
async def set_timer(
    bot,
    user_id: int,
    user_name: str | None = None,
    pokemon_setting: str | None = None,
    fish_setting: str | None = None,
    battle_setting: str | None = None,
):
    """
    Insert or update a user's timer settings.
    Only fields provided (not None) will be updated.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO timers (user_id, user_name, pokemon_setting, fish_setting, battle_setting)
                VALUES ($1, $2, $3, $4, $5)
                ON CONFLICT (user_id) DO UPDATE SET
                    user_name = COALESCE($2, timers.user_name),
                    pokemon_setting = COALESCE($3, timers.pokemon_setting),
                    fish_setting = COALESCE($4, timers.fish_setting),
                    battle_setting = COALESCE($5, timers.battle_setting)
                """,
                user_id,
                user_name,
                pokemon_setting,
                fish_setting,
                battle_setting,
            )

            pretty_log(
                tag="db",
                message=f"Set timer settings for user {user_id} ({user_name})",
                label="STRAYMONS",
                bot=bot,
            )


    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to set timer settings for user {user_id}: {e}",
            label="STRAYMONS",
            bot=bot,
        )


async def update_pokemon_setting(bot, user_id: int, pokemon_setting: str):
    """
    Update only the pokemon_setting field for a user.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE timers
                SET pokemon_setting = $2
                WHERE user_id = $1
                """,
                user_id,
                pokemon_setting,
            )

            pretty_log(
                tag="db",
                message=f"Updated pokemon_setting for user {user_id} to {pokemon_setting}",
                label="STRAYMONS",
                bot=bot,
            )

            # Update cache
            from utils.cache.timers_cache import update_pokemon_setting_in_cache
            update_pokemon_setting_in_cache(user_id, pokemon_setting)

    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to update pokemon_setting for user {user_id}: {e}",
            label="STRAYMONS",
            bot=bot,
        )



async def update_battle_setting(bot, user_id: int, battle_setting: str):
    """
    Update only the battle_setting field for a user.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE timers
                SET battle_setting = $2
                WHERE user_id = $1
                """,
                user_id,
                battle_setting,
            )

            pretty_log(
                tag="db",
                message=f"Updated battle_setting for user {user_id} to {battle_setting}",
                label="STRAYMONS",
                bot=bot,
            )
            # Update cache
            from utils.cache.timers_cache import update_battle_setting_in_cache
            update_battle_setting_in_cache(user_id, battle_setting)
            
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to update battle_setting for user {user_id}: {e}",
            label="STRAYMONS",
            bot=bot,
        )
# --------------------
#  Fetch all rows
# --------------------
async def fetch_all_timers(bot) -> list[dict]:
    """
    Return all rows in timers table as list of dicts.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch("SELECT * FROM timers")
            return [dict(row) for row in rows]
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to fetch timers: {e}",
            label="STRAYMONS",
            bot=bot,
        )
        return []


# --------------------
#  Fetch single user by ID
# --------------------
async def fetch_timer(bot, user_id: int) -> dict | None:
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT * FROM timers WHERE user_id = $1", user_id
            )
            return dict(row) if row else None
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to fetch timer for user {user_id}: {e}",
            label="STRAYMONS",
            bot=bot,
        )
        return None


# --------------------
#  Delete user timers
# --------------------
async def delete_timer(bot, user_id: int) -> bool:
    try:
        async with bot.pg_pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM timers WHERE user_id = $1", user_id
            )
        deleted = result.endswith("DELETE 1")
        pretty_log(
            tag="db",
            message=f"Deleted timers for user {user_id}: {deleted}",
            label="STRAYMONS",
            bot=bot,
        )
        return deleted
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to delete timers for user {user_id}: {e}",
            label="STRAYMONS",
            bot=bot,
        )
        return False
