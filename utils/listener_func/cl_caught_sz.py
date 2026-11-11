import re

import discord

from utils.cache.cache_list import catchlist_cache, processed_catchlist_sz_catches
from utils.database.catchlist_db import apply_catchlist_catch
from utils.essentials.ball_names import normalize_ball_type
from utils.essentials.pokemeow_helpers import get_pokemeow_reply_or_interaction_member
from utils.loggers.debug_log import debug_log, enable_debug
from utils.loggers.pretty_logs import pretty_log

# enable_debug(f"{__name__}.catchlist_sz_caught_listener")

_catches_in_flight: set[tuple[int, int | None, str]] = set()


def extract_pokemon_name(message: str):
    match = re.search(
        r"Caught\s+(?:<a?:[^:]+:\d+>\s+)+(.+?)\s+with\s+a\b", message, re.IGNORECASE
    )
    if not match:
        return None
    return match.group(1).replace("*", "").strip().lower() or None


def extract_steps_taken(message: str) -> int | None:
    match = re.search(r"Steps taken:\s*(\d+)", message, re.IGNORECASE)
    return int(match.group(1)) if match else None


async def catchlist_sz_caught_listener(
    bot: discord.Client, before_message: discord.Message, after_message: discord.Message
):
    member = await get_pokemeow_reply_or_interaction_member(before_message)
    if not member:
        debug_log(f"Member not found in message: {before_message.id}")
        return

    # Check if member is in cache
    if member.id not in catchlist_cache:
        debug_log(f"Member {member.id} not in catchlist cache")
        return

    message_content = after_message.content
    pokemon_caught = extract_pokemon_name(message_content)
    if not pokemon_caught:
        debug_log(
            f"Pokemon name could not be extracted from message: {after_message.id}"
        )
        return

    ball_used = "safariball"
    catch_type = ";safarizone"

    catch_key = (
        after_message.id,
        extract_steps_taken(message_content),
        pokemon_caught,
    )
    if catch_key in processed_catchlist_sz_catches or catch_key in _catches_in_flight:
        debug_log(f"Safari catch {catch_key} already processed")
        return

    from utils.cache.catchlist_cache import is_catchlist_mons_missing

    if is_catchlist_mons_missing(member.id):
        content = f"{member.mention} your catchlist is missing Pokémon entries. Please check `;catchlist` and scroll thru the pages."
        await before_message.channel.send(content)
        return
    # Check if pokemon has entry in catchlist for this member
    from utils.cache.catchlist_cache import get_mon_data_in_catchlist

    mon_data = get_mon_data_in_catchlist(member.id, pokemon_caught, catch_type)
    if not mon_data:
        debug_log(f"No mon data for Pokemon {pokemon_caught} for member {member.id}")
        return
    ball_type = mon_data.get("ball_type")
    ball_type = normalize_ball_type(ball_type) if ball_type else None
    if ball_type != ball_used:
        debug_log(
            f"Ball mismatch for {pokemon_caught}: expected {ball_type}, used {ball_used}."
        )
        return

    _catches_in_flight.add(catch_key)
    try:
        result = await apply_catchlist_catch(
            bot, member.id, pokemon_caught, catch_type, ball_used
        )
        if result is None:
            debug_log(
                f"No incomplete matching catchlist entry in the database for {pokemon_caught}."
            )
            return
        processed_catchlist_sz_catches.add(catch_key)
        if result.rank_data_missing:
            pretty_log(
                tag="warn",
                message=f"Missing rank EXP for user {member.id}; refresh the catchlist or profile.",
                label="CatchlistCaughtListener",
            )
        if result.rank_up:
            content = f"{member.mention} you have ranked up! Please check ;catchlist for your new rank!"
            await after_message.channel.send(content)
        elif result.exp_needed is not None:
            await after_message.channel.send(
                f"{member.mention} you need **{result.exp_needed:,} EXP** to rank up!"
            )
    finally:
        _catches_in_flight.discard(catch_key)
