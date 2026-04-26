import re

import discord
from discord.ext import commands

from group_func.toggle.held_item.held_item_ping_helpers import held_item_message
from utils.essentials.pokemeow_helpers import get_pokemeow_reply_member
from utils.loggers.debug_log import debug_log, enable_debug

enable_debug(f"{__name__}.held_item_ping_handler")


async def held_item_ping_handler(bot: commands.Bot, message: discord.Message):
    """
    Scan message embeds for Pokemon spawns.
    Logs all Pokemon, but only pings if spawn has a held item AND user is subscribed.
    """
    from utils.cache.held_item_cache import held_item_cache

    target_user = await get_pokemeow_reply_member(message)
    if not target_user:
        debug_log(
            "Message is not a reply to a PokéMeow message or failed to fetch user from reply."
        )
        trainer_match = re.search(r"\*\*(.+?)\*\* found a wild", message.content)
        if not trainer_match:
            debug_log("No username match found in message content.")
            return
        trainer_name = trainer_match.group(1).strip()

        # If we got a trainer name from the embed, we can try to find the user ID from the name
        from utils.cache.straymon_member_cache import get_user_id_by_name

        target_user_id = get_user_id_by_name(trainer_name)
        if not target_user_id:
            debug_log(
                f"Skipped: could not find user ID for trainer name '{trainer_name}' extracted from embed author"
            )
            return
        target_user = await bot.fetch_user(target_user_id)
        if not target_user:
            debug_log(
                f"Skipped: could not fetch user with ID {target_user_id} extracted from embed author"
            )
            return

    # ✅ Skip if user is not in held_item_cache
    if target_user.id not in held_item_cache:
        debug_log(f"User {target_user.id} not in held_item_cache, skipping")
        return

    user_sub = held_item_cache[target_user.id]
    debug_log(f"Target user: {target_user.id}")

    user_sub = held_item_cache.get(target_user.id, {})

    if not message.embeds:
        debug_log("Skipped: message has no embeds")
        return

    for embed in message.embeds:
        desc = embed.description or ""

        debug_log(f"Embed description raw: {repr(desc)}")

        # Regex: extract optional held item and Pokemon name
        pattern = (
            r"(?:<:[^:]+:\d+>\s*)?"  # optional leading NPC emoji
            r"\*\*.+?\*\*\s*found a wild\s*"
            r"(?P<teamlogo><:team_logo:\d+>)?\s*"  # optional team logo emoji
            r"(?P<held><:held_item:\d+>)?\s*"  # optional held item emoji
            r"(?:<:[^:]+:\d+>\s*)+"  # Pokemon emoji (+ optional dexCaught)
            r"\*\*(?P<pokemon>[A-Za-z_-]+)\*\*"  # pokemon name (allow hyphens)
        )
        matches = re.finditer(pattern, desc)

        for match in matches:
            pokemon_name = match.group("pokemon").lower()
            has_held_item = bool(match.group("held"))

            # Log every Pokemon
            debug_log(f"Detected Pokemon: {pokemon_name}, Held item? {has_held_item}")

            # Only ping if the spawn actually has a held item
            if not has_held_item:
                continue

            msg = held_item_message(pokemon_name, user_sub)
            if not msg:
                debug_log(
                    f"User {target_user.id} not subscribed for {pokemon_name}'s items"
                )
                continue

            try:
                await message.channel.send(f"<@{target_user.id}> {msg}")
                debug_log(f"Pinged {target_user.id} for {pokemon_name}")
            except Exception as e:
                debug_log(f"Failed to ping {target_user.id} for {pokemon_name}: {e}")
