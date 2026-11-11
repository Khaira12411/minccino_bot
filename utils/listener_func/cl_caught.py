import re

import discord

from utils.cache.cache_list import (
    catchlist_cache,
    processed_caught_catchlist_messages,
    processed_spawn_messages,
)
from utils.database.catchlist_db import apply_catchlist_catch
from utils.essentials.ball_names import format_ball, normalize_ball_type
from utils.essentials.pokemeow_helpers import get_pokemeow_reply_or_interaction_member
from utils.loggers.debug_log import debug_log, enable_debug
from utils.loggers.pretty_logs import pretty_log

DEFAULT_BALLS = ["pokeball", "greatball", "ultraball", "masterball", "premierball"]
FISHING_COLOR = 0x87CEFA
# enable_debug(f"{__name__}.catchlist_caught_listener")
_caught_messages_in_flight: set[int] = set()


def extract_catch_details(message: str):
    match = re.search(
        r"\*\*(?P<pokemon_caught>.+?)\*\*\s+with an?\s+"
        r"<:[^:]+:\d+>\s+(?P<ball_used>.+?)!",
        message,
        re.IGNORECASE,
    )

    if not match:
        return None

    return {
        "pokemon_caught": match.group("pokemon_caught").strip().lower(),
        "ball_used": match.group("ball_used").strip().lower(),
    }


async def catchlist_caught_listener(
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

    embed = after_message.embeds[0] if after_message.embeds else None
    embed_description = embed.description if embed else ""
    embed_color = embed.color.value if embed and embed.color else None
    catch_details = extract_catch_details(embed_description)
    if not catch_details:
        debug_log(
            f"Catch details could not be extracted from message: {after_message.id}"
        )
        return

    pokemon_caught = catch_details["pokemon_caught"]
    ball_used = normalize_ball_type(catch_details["ball_used"])

    catch_type = ";fish" if embed_color == FISHING_COLOR else ";p"

    if (
        after_message.id in processed_caught_catchlist_messages
        or after_message.id in _caught_messages_in_flight
    ):
        debug_log(f"Message {after_message.id} already processed")
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
    if after_message.id not in processed_spawn_messages:
        before_embed = before_message.embeds[0] if before_message.embeds else None
        before_description = before_embed.description if before_embed else None
        debug_log(
            f"No spawn alert recorded for message {after_message.id}; "
            f"previous embed description: {before_description!r}"
        )
    ball_type = mon_data.get("ball_type")
    ball_type = normalize_ball_type(ball_type) if ball_type else None
    if ball_type != ball_used:
        debug_log(
            f"Ball mismatch for {pokemon_caught}: expected {ball_type}, used {ball_used}."
        )
        return

    _caught_messages_in_flight.add(after_message.id)
    try:
        result = await apply_catchlist_catch(
            bot, member.id, pokemon_caught, catch_type, ball_used
        )
        if result is None:
            debug_log(
                f"No incomplete matching catchlist entry in the database for {pokemon_caught}."
            )
            return
        processed_caught_catchlist_messages.add(after_message.id)
        if result.rank_data_missing:
            pretty_log(
                tag="warn",
                message=f"Missing rank EXP for user {member.id}; refresh the catchlist or profile.",
                label="CatchlistCaughtListener",
            )
        if result.rank_up:
            content = f"{member.mention} you have ranked up! Please check ;catchlist for your new rank!"
            await after_message.channel.send(content)
        from utils.cache.catchlist_cache import is_ball_still_needed

        if ball_used not in DEFAULT_BALLS and not is_ball_still_needed(
            member.id, catch_type, ball_used
        ):
            command = ";f" if catch_type == ";fish" else ";p"
            await after_message.channel.send(
                f"{member.mention} you no longer need {format_ball(ball_used)}! "
                f"You can remove it from your `{command}` ball order."
            )
        """elif result.exp_needed is not None:
            await after_message.channel.send(
                f"{member.mention} you need **{result.exp_needed:,} EXP** to rank up!"
            )"""
    finally:
        _caught_messages_in_flight.discard(after_message.id)
