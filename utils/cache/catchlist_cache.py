import json

import discord

from utils.cache.cache_list import catchlist_cache
from utils.database.catchlist_db import fetch_all_catchlists
from utils.loggers.pretty_logs import pretty_log


async def load_catchlist_cache(bot: discord.Client):
    catchlists = await fetch_all_catchlists(bot)
    loaded = {
        catchlist["user_id"]: _normalize_catchlist(catchlist)
        for catchlist in catchlists
    }
    catchlist_cache.clear()
    catchlist_cache.update(loaded)
    pretty_log(
        tag="info",
        label="🦋 CATCHLIST CACHE",
        message=f"Loaded {len(catchlist_cache)} catchlists into cache",
    )


def _normalize_catchlist(catchlist: dict) -> dict:
    mons = catchlist["catchlist_mons"]
    if isinstance(mons, str):
        mons = json.loads(mons)
    if mons is None:
        mons = []
    if not isinstance(mons, list) or not all(isinstance(mon, dict) for mon in mons):
        raise ValueError(f"Invalid catchlist Pokémon for user {catchlist['user_id']}")
    return {**catchlist, "catchlist_mons": mons}


def upsert_catchlist_cache(user_id: int, catchlist: dict):
    catchlist_cache[user_id] = _normalize_catchlist(catchlist)
    pretty_log(
        tag="info",
        label="🦋 CATCHLIST CACHE",
        message=f"Upserted catchlist for user_id {user_id}",
    )


def delete_catchlist_cache(user_id: int):
    if user_id in catchlist_cache:
        del catchlist_cache[user_id]
        pretty_log(
            tag="info",
            label="🦋 CATCHLIST CACHE",
            message=f"Deleted catchlist for user_id {user_id}",
        )


def reset_catchlist_cache():
    catchlist_cache.clear()
    pretty_log(
        tag="info",
        label="🦋 CATCHLIST CACHE",
        message="Reset all catchlists in cache",
    )


def update_mon_completion_in_catchlist(
    user_id: int, pokemon_name: str, catch_type: str, completion: bool
):
    catchlist = catchlist_cache.get(user_id)
    if not catchlist:
        return
    for mon in catchlist["catchlist_mons"]:
        if (
            mon["pokemon_name"].lower() == pokemon_name.lower()
            and mon["catch_type"].lower() == catch_type.lower()
        ):
            mon["completion"] = completion
            break
    pretty_log(
        tag="info",
        label="🦋 CATCHLIST CACHE",
        message=f"Updated completion status for {pokemon_name} ({catch_type}) in catchlist for user_id {user_id}",
    )


def get_mon_status_in_catchlist(
    user_id: int, pokemon_name: str, catch_type: str
) -> bool | None:
    catchlist = catchlist_cache.get(user_id)
    if not catchlist:
        return None
    for mon in catchlist["catchlist_mons"]:
        if (
            mon["pokemon_name"].lower() == pokemon_name.lower()
            and mon["catch_type"].lower() == catch_type.lower()
        ):
            return mon["completion"]
    return None


def get_mon_data_in_catchlist(
    user_id: int, pokemon_name: str, catch_type: str | None = None
) -> dict | None:
    catchlist = catchlist_cache.get(user_id)
    if not catchlist:
        return None
    for mon in catchlist["catchlist_mons"]:
        if mon["pokemon_name"].lower() == pokemon_name.lower() and (
            catch_type is None or mon["catch_type"].lower() == catch_type.lower()
        ):
            return mon
    return None


def get_user_data_in_catchlist(user_id: int) -> dict | None:
    return catchlist_cache.get(user_id)


def is_ball_still_needed(user_id: int, catch_type: str, ball_type: str) -> bool:
    """True if any incomplete catchlist Pokémon for this catch type needs the ball."""
    from utils.essentials.ball_names import normalize_ball_type

    catchlist = catchlist_cache.get(user_id)
    if not catchlist:
        return True
    ball = normalize_ball_type(ball_type)
    return any(
        not mon["completion"]
        and mon["catch_type"].lower() == catch_type.lower()
        and normalize_ball_type(mon["ball_type"]) == ball
        for mon in catchlist["catchlist_mons"]
    )


def update_user_exp_in_catchlist(user_id: int, new_exp_needed: int, new_total_exp: int):
    catchlist = catchlist_cache.get(user_id)
    if not catchlist:
        return
    catchlist["exp_needed"] = new_exp_needed
    catchlist["total_exp"] = new_total_exp
    pretty_log(
        tag="info",
        label="🦋 CATCHLIST CACHE",
        message=f"Updated exp for user_id {user_id} in catchlist",
    )


# Check if the user is in cache and if they dont have a catchlist_mons saved yet and returns true or false
def is_catchlist_mons_missing(user_id: int) -> bool:
    catchlist = catchlist_cache.get(user_id)
    if not catchlist:
        return True
    if "catchlist_mons" not in catchlist or not catchlist["catchlist_mons"]:
        return True
    return False
