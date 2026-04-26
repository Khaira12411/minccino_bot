import re

import discord
from discord.ext import commands

from group_func.toggle.held_item.held_item_ping_helpers import held_item_message
from utils.loggers.pretty_logs import pretty_log
from utils.essentials.pokemeow_helpers import get_pokemeow_reply_member
from utils.loggers.debug_log import debug_log, enable_debug

async def held_item_ping_handler(bot: commands.Bot, message: discord.Message):
    """
    Scan message embeds for Pokemon spawns.
    Logs all Pokemon, but only pings if spawn has a held item AND user is subscribed.
    """
    from utils.cache.held_item_cache import held_item_cache

    """pretty_log(
        "info", f"Processing message {message.id}", label="🐭 HELD ITEM PING", bot=bot
    )"""

    target_user = await get_pokemeow_reply_member(message)
    if not target_user:
        """pretty_log(
            "skip", "Skipped: reply has no author", label="🐭 HELD ITEM PING", bot=bot
        )"""
        trainer_name = re.search(r"\*\*(.+?)\*\* found a wild", message.content)
        if not trainer_name:
            debug_log("No username match found in message content.")
            return

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
        """pretty_log(
            "skip",
            f"User {target_user.id} not in held_item_cache, skipping",
            label="🐭 HELD ITEM PING",
            bot=bot,
        )"""
        return

    user_sub = held_item_cache[target_user.id]
    """pretty_log(
        "info", f"Target user: {target_user.id}", label="🐭 HELD ITEM PING", bot=bot
    )"""

    user_sub = held_item_cache.get(target_user.id, {})

    if not message.embeds:
        """pretty_log(
            "skip", "Skipped: message has no embeds", label="🐭 HELD ITEM PING", bot=bot
        )"""
        return

    for embed in message.embeds:
        desc = embed.description or ""

        """pretty_log(
            "debug",
            f"Embed description raw: {repr(desc)}",
            label="🐭 HELD ITEM PING",
            bot=bot,
        )"""

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
            """pretty_log(
                "info",
                f"Detected Pokemon: {pokemon_name}, Held item? {has_held_item}",
                label="🐭 HELD ITEM PING",
                bot=bot,
            )"""

            # Only ping if the spawn actually has a held item
            if not has_held_item:
                continue

            msg = held_item_message(pokemon_name, user_sub)
            if not msg:
                """pretty_log(
                    "skip",
                    f"User {target_user.id} not subscribed for {pokemon_name}'s items",
                    label="🐭 HELD ITEM PING",
                    bot=bot,
                )"""
                continue

            try:
                await message.channel.send(f"<@{target_user.id}> {msg}")
                pretty_log(
                    "info",
                    f"Pinged {target_user.id} for {pokemon_name}",
                    label="🐭 HELD ITEM PING",
                    bot=bot,
                )
            except Exception as e:
                pretty_log(
                    "error",
                    f"Failed to ping {target_user.id} for {pokemon_name}: {e}",
                    label="🐭 HELD ITEM PING",
                    bot=bot,
                )
