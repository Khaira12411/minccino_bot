import re
from enum import member

import discord

from utils.cache.cache_list import catchlist_cache, processed_spawn_messages
from utils.essentials.ball_names import format_ball
from utils.essentials.pokemeow_helpers import get_pokemeow_reply_or_interaction_member
from utils.loggers.debug_log import debug_log, enable_debug
from utils.loggers.pretty_logs import pretty_log

# enable_debug(f"{__name__}.catchlist_spawn_listener")
_spawn_messages_in_flight: set[int] = set()

FISHING_COLOR = 0x87CEFA
SAFARI_COLOR = 0x73BA5D


def extract_pokemon_name(message: str):
    match = re.search(r"\*\*((?:(?!\*\*)[^\n])+?)\*\*!", message)

    return match.group(1).strip() if match else None


def extract_safari_pokemon_name(message: str) -> str | None:
    match = re.search(
        r"^[ \t]*(?:<a?:[^:>\s]+:\d+>[ \t]*)+"
        r"\*\*(?P<name>(?:(?!\*\*)[^\r\n])+?)\*\*[ \t]*\r?\n"
        r"[ \t]*-[ \t]*Catch chance:",
        message,
        re.IGNORECASE | re.MULTILINE,
    )
    return match.group("name").strip() if match else None


async def catchlist_spawn_listener(
    bot: discord.Client,
    before_message: discord.Message,
    after_message: discord.Message,
    catch_type: str = ";p",
):
    member = await get_pokemeow_reply_or_interaction_member(before_message)
    if not member:
        debug_log(f"Member not found in message: {before_message.id}")
        return
    from utils.cache.user_alert_cache import fetch_user_alert_notify_cache

    catchlist_alert_type = fetch_user_alert_notify_cache(member.id, "catchlist")
    if not catchlist_alert_type:
        debug_log(f"No catchlist alert info for member {member.id}")
        return
    if catchlist_alert_type == "off":
        debug_log(f"Catchlist alerts are turned off for member {member.id}")
        return

    # Check if member is in cache
    if member.id not in catchlist_cache:
        debug_log(f"Member {member.id} not in catchlist cache")
        return

    debug_log(f"Catch type {catch_type}")
    embed = after_message.embeds[0] if after_message.embeds else None
    embed_description = embed.description if embed else ""
    embed_color = embed.color.value if embed and embed.color else None

    pokemon_name = None
    if catch_type == ";p" or catch_type == ";fish":
        pokemon_name = extract_pokemon_name(embed_description)
    elif catch_type == ";safarizone":
        pokemon_name = extract_safari_pokemon_name(embed_description)
    pokemon_name = pokemon_name.lower().strip() if pokemon_name else None

    if not pokemon_name:
        debug_log(
            f"Pokemon name could not be extracted from message: {after_message.id}"
        )
        return

    # Safari reuses one message for every encounter, so the ID alone is not unique.
    spawn_key = after_message.id
    if catch_type == ";safarizone":
        steps = re.search(r"Steps taken:\s*(\d+)", after_message.content or "")
        spawn_key = (after_message.id, steps.group(1) if steps else None, pokemon_name)
    if spawn_key in processed_spawn_messages or spawn_key in _spawn_messages_in_flight:
        debug_log(f"Message {after_message.id} already processed")
        return
    debug_log(f"Extracted Pokemon name {pokemon_name} from message {after_message.id}")
    # Check if pokemon has entry in catchlist for this member
    from utils.cache.catchlist_cache import get_mon_data_in_catchlist

    if not get_mon_data_in_catchlist(member.id, pokemon_name, catch_type):
        debug_log(
            f"No catchlist entry for Pokemon {pokemon_name} for member {member.id}"
        )
        return
    else:
        debug_log(
            f"Pokemon {pokemon_name} has an entry in catchlist for member {member.id}"
        )

    from utils.cache.catchlist_cache import get_mon_status_in_catchlist

    completion = get_mon_status_in_catchlist(member.id, pokemon_name, catch_type)
    if completion is None:
        debug_log(
            f"No catchlist status for Pokemon {pokemon_name} for member {member.id}"
        )
        return
    if completion:
        debug_log(
            f"Pokemon {pokemon_name} already completed in catchlist for member {member.id}"
        )
        return

    # Alert member for the right ball
    mon_data = get_mon_data_in_catchlist(member.id, pokemon_name, catch_type)
    if not mon_data:
        debug_log(f"No mon data for Pokemon {pokemon_name} for member {member.id}")
        return
    ball_type = mon_data.get("ball_type")
    exp_amount = mon_data.get("exp_amount")

    member_str = f"{member.mention}"
    if catchlist_alert_type == "on_no_pings":
        member_str = f"**{member.name}**"

    if ball_type and exp_amount:
        ball_formatted = format_ball(ball_type)
        content = f"{member_str}, **{pokemon_name.title()}** is in your catchlist! Use {ball_formatted} +{exp_amount} EXP!"
        debug_log(
            f"Alerting member {member.id} for Pokemon {pokemon_name} with ball {ball_type} and EXP {exp_amount}"
        )
        _spawn_messages_in_flight.add(spawn_key)
        try:
            await after_message.channel.send(content)
            processed_spawn_messages.add(spawn_key)
        finally:
            _spawn_messages_in_flight.discard(spawn_key)
