import re

import discord

from utils.cache.cache_list import processed_pin_numbers_messages
from utils.database.pin_numbers_db import (
    fetch_all_pin_numbers,
    fetch_pin_number_type,
    upsert_pin_number_type,
)
from utils.database.user_alerts_db import fetch_user_alert_notify, upsert_user_alert
from utils.essentials.pokemeow_helpers import (
    get_pokemeow_reply_member,
    get_pokemeow_reply_or_interaction_member,
)
from utils.essentials.retry_function import _retry_discord_call
from utils.loggers.debug_log import debug_log, enable_debug
from utils.loggers.pretty_logs import pretty_log

#enable_debug(f"{__name__}.pokemon_pin_numbers_listener")

from itertools import permutations


def get_combinations(*pins: str | None) -> list[str]:
    """Returns all joined permutations of the given pins; missing pins appear as '?'."""
    if not pins:
        return []
    normalized = [p if p else "?" for p in pins]
    # dict.fromkeys dedupes repeated '?' placeholders while preserving order
    return list(dict.fromkeys("".join(combo) for combo in permutations(normalized)))


def extract_trainer_name_from_pin_description(description: str) -> str | None:
    """Extracts the bolded trainer name from a 'found/fished a wild' embed description."""
    match = re.search(r"\*\*(.+?)\*\*\s+(?:found|fished) a wild", description)
    if match:
        return match.group(1).strip()
    return None


async def pokemon_pin_numbers_listener(
    bot: discord.Client, message: discord.Message, pin_number: str, source: str
):
    debug_log(
        f"Pin-number listener triggered: message_id={message.id}, "
        f"pin_number={pin_number!r}, channel_id={message.channel.id}"
    )

    if message.id in processed_pin_numbers_messages:
        debug_log(f"Skipping already processed message: {message.id}")
        return
    processed_pin_numbers_messages.add(message.id)
    debug_log(f"Marked message as processed: {message.id}")

    # Get member object
    member = await get_pokemeow_reply_or_interaction_member(message)
    debug_log(f"Resolved pin-number member: {member!r}")
    if not member:
        return

    user_id = member.id
    debug_log(f"Resolved member ID: {user_id}")
    if not user_id:
        debug_log("Resolved member has no user ID; returning")
        return

    # Check if user id is in the pin numbers cache
    user_pin_notify = await fetch_user_alert_notify(bot, user_id, "pin_numbers")
    debug_log(f"Pin alert cache lookup for user {user_id}: {user_pin_notify!r}")

    if not user_pin_notify:
        # Upsert with default on_no_pings
        debug_log(f"No pin alert found for user {user_id}; creating on_no_pings alert")
        await upsert_user_alert(bot, user_id, member.name, "pin_numbers", "on_no_pings")
        user_pin_notify = "on_no_pings"
        debug_log(f"Created default pin alert for user {user_id}")

    debug_log(f"User pin notify setting: {user_pin_notify}")
    if user_pin_notify.lower() == "off":
        debug_log("User notify setting is off, returning early")
        return
    if source == "pokemon":
        command = ";p"
    elif source == "fish":
        command = ";f"
    elif source == "safari":
        command = ";sz"
    else:
        command = ";p"
    if user_pin_notify.lower() == "on":
        content = (
            f"#️⃣ {member.mention}, your `{command}` pin number is **{pin_number}**"
        )
        debug_log(f"Using mention notification mode for user {user_id}")
    elif user_pin_notify.lower() == "on_no_pings":
        content = (
            f"#️⃣ **{member.name}**, your `{command}` pin number is **{pin_number}**"
        )
        debug_log(f"Using name-only notification mode for user {user_id}")

    else:
        debug_log(f"Unknown user pin notification setting: {user_pin_notify}")
        return

    debug_log(
        f"Sending pin-number alert from {source} to channel {message.channel.name}"
    )
    await _retry_discord_call(message.channel.send, content=content)
    debug_log(f"Pin-number alert sent successfully for user {user_id}")

    # Check for changes then update
    db_type = {"pokemon": "pokemon", "fish": "fish", "safari": "sz"}.get(
        source, "pokemon"
    )
    current_pin_number = await fetch_pin_number_type(bot, user_id, db_type)
    if current_pin_number is not None and str(current_pin_number) == pin_number:
        debug_log(f"Pin number for user {user_id} is unchanged; skipping summary")
        return

    debug_log(
        f"Pin number for user {user_id} has changed from {current_pin_number} to {pin_number}, updating..."
    )
    await upsert_pin_number_type(bot, user_id, member.name, db_type, pin_number)

    # Get all pin numbers for the user
    all_pin_numbers = await fetch_all_pin_numbers(bot, user_id)
    debug_log(f"All pin numbers for user {user_id}: {all_pin_numbers!r}")
    pokemon_pin = all_pin_numbers.get("pokemon_pin") if all_pin_numbers else None
    fish_pin = all_pin_numbers.get("fish_pin") if all_pin_numbers else None
    safari_pin = all_pin_numbers.get("sz_pin") if all_pin_numbers else None
    debug_log(
        f"Resolved individual pin numbers for user {user_id}: pokemon_pin={pokemon_pin}, fish_pin={fish_pin}, safari_pin={safari_pin}"
    )
    footer_text = "To view your pin numbers, use !pins or /pin view"
    pin_numbers_embed = create_pin_numbers_embed(
        member, pokemon_pin, fish_pin, safari_pin, footer_text=footer_text
    )

    all_discovered = all(
        pin is not None and str(pin) != ""
        for pin in (pokemon_pin, fish_pin, safari_pin)
    )
    if (current_pin_number is None or current_pin_number == "") and all_discovered:
        await message.channel.send(
            content="All pin numbers have been discovered!",
            embed=pin_numbers_embed,
        )
    else:
        await message.channel.send(embed=pin_numbers_embed)


def create_pin_numbers_embed(
    member: discord.Member,
    pokemon_pin: str | None,
    fish_pin: str | None,
    safari_pin: str | None,
    footer_text: str,
):
    # DB stores pins as INTEGER; coerce to str for joining/display
    pokemon_pin = str(pokemon_pin) if pokemon_pin is not None else None
    fish_pin = str(fish_pin) if fish_pin is not None else None
    safari_pin = str(safari_pin) if safari_pin is not None else None
    all_combinations = get_combinations(pokemon_pin, fish_pin, safari_pin)
    combinations_text = ", ".join(all_combinations) if all_combinations else "?"
    desc = (
        f"- **Pokemon pin**: {pokemon_pin or '?'}\n"
        f"- **Fish pin**: {fish_pin or '?'}\n"
        f"- **Safari zone pin**: {safari_pin or '?'}\n"
        f"- **All combinations**: {combinations_text}"
    )
    embed = discord.Embed(
        title=f"{member.name}'s Pin Numbers",
        description=desc,
        color=discord.Color.blue(),
    )
    embed.set_author(
        name=f"{member.name}", icon_url=member.avatar.url if member.avatar else None
    )
    embed.set_footer(text=footer_text)
    return embed
