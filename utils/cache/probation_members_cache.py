import discord

from utils.cache.cache_list import probation_members_cache
from utils.database.probation_members_db import fetch_all_probation_members
from utils.loggers.pretty_logs import pretty_log


# 🤍💫────────────────────────────────────────────💫🤍
#        🕒 Probation Members Cache Functions
# 🤍💫────────────────────────────────────────────💫🤍
async def load_probation_members_cache(bot: discord.Client):
    """
    Loads all probation members from the database into the in-memory cache.
    """
    global probation_members_cache
    members = await fetch_all_probation_members(bot)
    probation_members_cache.clear()
    for member in members:
        probation_members_cache[member["user_id"]] = {
            "user_name": member["user_name"],
            "status": member["status"],
        }
    pretty_log(
        "cache",
        f"Loaded {len(probation_members_cache)} probation members into cache",
    )
    return probation_members_cache


def upsert_probation_member_in_cache(
    user_id: int,
    user_name: str,
    status: str = "Pending",
):
    """
    Upserts a probation member in the in-memory cache.
    """
    probation_members_cache[user_id] = {
        "user_name": user_name,
        "status": status,
    }
    pretty_log(
        "cache",
        f"Upserted probation member {user_name} ({user_id}) with status '{status}' in cache",
    )


def update_probation_member_status_in_cache(
    user_id: int,
    status: str,
):
    """
    Updates or adds a probation member in the in-memory cache.
    """
    user_name = probation_members_cache.get(user_id, {}).get("user_name", "Unknown")
    probation_members_cache[user_id] = {
        "user_name": user_name,
        "status": status,
    }
    pretty_log(
        "cache",
        f"Updated probation member {user_name} ({user_id}) with status '{status}' in cache",
    )
