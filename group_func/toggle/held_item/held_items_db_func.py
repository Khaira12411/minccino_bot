from config.held_items import HELD_ITEMS_DICT
from utils.loggers.pretty_logs import pretty_log


# ────────────────────────────────────────────
#       🐭 Fetch all user item pings 🐭
# ────────────────────────────────────────────
async def fetch_all_user_item_pings(bot) -> list[dict]:
    """
    Returns all rows in user_item_pings table including relic columns.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT user_id, user_name, held_item_pings, has_exchanged_relics, relics_reminder
                FROM user_item_pings
                """
            )
            return [dict(row) for row in rows]
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to fetch user item pings: {e}",
            label="MINCCINO",
            bot=bot,
        )
        return []


# ────────────────────────────────────────────
#       🐭 Update a single item subscription 🐭
# ────────────────────────────────────────────
async def set_user_item_subscription(
    bot, user_id: int, item_name: str, subscribed: bool
):
    """
    Update or insert a single held item subscription for a user.
    """
    from utils.cache.held_item_cache import load_held_item_cache

    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO user_item_pings (user_id, held_item_pings)
                VALUES ($1, jsonb_build_object($2::text, $3::boolean))
                ON CONFLICT (user_id) DO UPDATE
                SET held_item_pings = jsonb_set(
                    COALESCE(user_item_pings.held_item_pings, '{}'),
                    ARRAY[$2::text],
                    to_jsonb($3::boolean),
                    true
                )
                """,
                user_id,
                item_name,
                subscribed,
            )
        pretty_log(
            "info",
            f"Set item '{item_name}' -> {subscribed} for user {user_id} (upserted if needed)",
        )

    except Exception as e:
        pretty_log(
            "warn",
            f"Failed to set item subscription for user {user_id}: {e}",
            label="MINCCINO",
            bot=bot,
        )
# utils/group_func/held_item_db_func.py  (example location)


async def update_user_name(bot, user_id: int, new_user_name: str):
    """
    Update the user_name column only if it's different from the current value.
    """
    query = """
    UPDATE user_item_pings
    SET user_name = $2
    WHERE user_id = $1
      AND (user_name IS DISTINCT FROM $2);
    """
    async with bot.pg_pool.acquire() as conn:
        await conn.execute(query, user_id, new_user_name)


# ────────────────────────────────────────────
#       🐭 Remove a user's subscription 🐭
# ────────────────────────────────────────────
async def remove_user_item(bot, user_id: int, item_name: str):
    """
    Remove a held item subscription from a user.
    """
    from utils.cache.held_item_cache import load_held_item_cache

    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE user_item_pings
                SET held_item_pings = held_item_pings - $2
                WHERE user_id = $1
                """,
                user_id,
                item_name,
            )
            # await load_held_item_cache(bot)

    except Exception as e:
        pretty_log(
            tag="warn",
            message=f"Failed to remove item {item_name} for user {user_id}: {e}",
            label="MINCCINO",
            bot=bot,
        )


# ────────────────────────────────────────────
#        🐭 Minccino Ping Helper Functions 🐭
# ────────────────────────────────────────────
async def get_users_to_ping(bot, pokemon_name: str, held_item_name: str) -> list[dict]:
    """
    Return a list of users who are subscribed to the given held item
    AND the Pokemon is one that can carry this item.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT user_id, user_name
                FROM user_item_pings
                WHERE held_item_pings ->> $1 = 'true'
                """,
                held_item_name,
            )
            result = []
            item_meta = HELD_ITEMS_DICT.get(held_item_name)
            if not item_meta:
                return []

            for row in rows:
                if pokemon_name.lower() in item_meta["pokemon"]:
                    result.append(
                        {"user_id": row["user_id"], "user_name": row["user_name"]}
                    )

            return result

    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to get users to ping for {held_item_name} / {pokemon_name}: {e}",
            label="MINCCINO",
            bot=bot,
        )
        return []


# ────────────────────────────────────────────
#        🐭 Example Usage 🐭
# ────────────────────────────────────────────
async def ping_users_for_mon(bot, channel, pokemon_name: str, held_item_name: str):
    users = await get_users_to_ping(bot, pokemon_name, held_item_name)
    if not users:
        return

    emoji = HELD_ITEMS_DICT.get(held_item_name, {}).get("emoji", "🐭")
    mentions = " ".join(f"<@{u['user_id']}>" for u in users)
    await channel.send(
        f"{emoji} {mentions} {pokemon_name.title()} may have a {held_item_name}!"
    )


# ────────────────────────────────────────────
#       🐭 Set has_exchanged_relics Flag 🐭
# ────────────────────────────────────────────
async def set_has_exchanged_relics(bot, user_id: int, exchanged: bool):
    """
    Update the has_exchanged_relics column for a user.
    """
    query = "UPDATE user_item_pings SET has_exchanged_relics = $1 WHERE user_id = $2"
    async with bot.pg_pool.acquire() as conn:
        await conn.execute(query, exchanged, user_id)


# ────────────────────────────────────────────
#       🐭 Set relics_reminder Flag 🐭
# ────────────────────────────────────────────
async def set_relics_reminder(bot, user_id: int, reminder: bool):
    """
    Update the relics_reminder column for a user.
    """
    query = "UPDATE user_item_pings SET relics_reminder = $1 WHERE user_id = $2"
    async with bot.pg_pool.acquire() as conn:
        await conn.execute(query, reminder, user_id)
