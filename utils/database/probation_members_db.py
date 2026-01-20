import discord

from utils.loggers.pretty_logs import pretty_log

# SQL SCRIPT
"""CREATE TABLE probation_members (
    user_id BIGINT PRIMARY KEY,
    user_name TEXT,
    status TEXT DEFAULT 'pending'
);"""


# 🤍💫────────────────────────────────────────────💫🤍
#        🕒 Probation Members DB Functions
# 🤍💫────────────────────────────────────────────💫🤍
async def upsert_probation_member(
    bot: discord.Client,
    user_id: int,
    user_name: str,
    status: str = "pending",
):
    """
    Upserts a probation member with the given user_id, user_name, and status.
    """
    query = """
        INSERT INTO probation_members (user_id, user_name, status)
        VALUES ($1, $2, $3)
        ON CONFLICT (user_id) DO UPDATE SET
            user_name = EXCLUDED.user_name,
            status = EXCLUDED.status
    """
    async with bot.pg_pool.acquire() as conn:
        await conn.execute(query, user_id, user_name, status)
    pretty_log(
        "db",
        f"Upserted probation member {user_name} ({user_id}) with status '{status}'",
    )
    # Update in cache as well
    from utils.cache.probation_members_cache import upsert_probation_member_in_cache
    upsert_probation_member_in_cache(
        user_id,
        user_name,
        status,
    )

async def fetch_all_probation_members(bot: discord.Client) -> list[dict]:
    """
    Fetches all probation members from the database.
    Returns a list of dictionaries with keys: user_id, user_name, status.
    """
    query = "SELECT user_id, user_name, status FROM probation_members"
    async with bot.pg_pool.acquire() as conn:
        rows = await conn.fetch(query)
    members = [
        {"user_id": row["user_id"], "user_name": row["user_name"], "status": row["status"]}
        for row in rows
    ]
    pretty_log(
        "db",
        f"Fetched {len(members)} probation members from the database",
    )
    return members

async def remove_probation_member(bot: discord.Client, user_id: int):
    """
    Removes the probation member with the given user_id.
    """
    query = "DELETE FROM probation_members WHERE user_id = $1"
    async with bot.pg_pool.acquire() as conn:
        await conn.execute(query, user_id)
    pretty_log(
        "db",
        f"Removed probation member with user_id {user_id}",
    )


async def get_probation_member_status(bot: discord.Client, user_id: int) -> str:
    """
    Retrieves the status of the probation member with the given user_id.
    Returns None if the member does not exist.
    """
    query = "SELECT status FROM probation_members WHERE user_id = $1"
    async with bot.pg_pool.acquire() as conn:
        result = await conn.fetchrow(query, user_id)
    if result:
        status = result["status"]
        pretty_log(
            "db",
            f"Retrieved status '{status}' for probation member with user_id {user_id}",
        )
        return status
    else:
        pretty_log(
            "db",
            f"No probation member found with user_id {user_id}",
        )
        return None


async def update_probation_member_status(
    bot: discord.Client,
    user_id: int,
    new_status: str,
):
    """
    Updates the status of the probation member with the given user_id.
    """
    query = "UPDATE probation_members SET status = $1 WHERE user_id = $2"
    async with bot.pg_pool.acquire() as conn:
        await conn.execute(query, new_status, user_id)
    pretty_log(
        "db",
        f"Updated status to '{new_status}' for probation member with user_id {user_id}",
    )
    # Update in cache as well
    from utils.cache.probation_members_cache import update_probation_member_status_in_cache
    update_probation_member_status_in_cache(
        user_id,
        new_status,
    )