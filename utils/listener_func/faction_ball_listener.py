import re

import discord

from config.faction_data import FACTION_LOGO_EMOJIS, get_faction_by_emoji
from utils.cache.daily_fa_ball_cache import daily_faction_ball_cache
from utils.cache.faction_ball_alert_cache import faction_ball_alert_cache
from utils.cache.straymon_member_cache import straymon_member_cache
from utils.database.daily_fa_ball import update_faction_ball
from utils.essentials.pokemeow_helpers import get_pokemeow_reply_member
from utils.loggers.debug_log import debug_log, enable_debug
from utils.loggers.pretty_logs import pretty_log

enable_debug(f"{__name__}.extract_faction_ball_from_daily")
STRAYMONS_GUILD_ID = 1047856017121214555


async def update_faction(bot: discord.Client, user_id: int, faction: str | None):
    """
    Updates the faction for a user in straymons_members.
    Pass None to clear the faction.
    """
    guild = bot.get_guild(STRAYMONS_GUILD_ID)
    user = guild.get_member(user_id)
    user_display = user if user else "Unknown Member"
    query = "UPDATE straymons_members SET faction = $1 WHERE user_id = $2"
    async with bot.pg_pool.acquire() as conn:
        await conn.execute(query, faction, user_id)
        pretty_log(
            "success",
            f"Updated faction for user {user_id} ({user_display}) to '{faction}'",
        )


# 🛡️────────────────────────────────────────────
#      🛡️ Faction Ball Listener Functions
# 🛡️────────────────────────────────────────────
async def extract_faction_ball_from_daily(bot, message: discord.Message):
    """Listens to PokéMeow's daily message for faction ball info."""
    debug_log("Starting extract_faction_ball_from_daily")
    embed = message.embeds[0] if message.embeds else None
    if not embed:
        debug_log("No embed found in daily message.")
        return

    embed_description = embed.description or ""
    debug_log(f"Embed description: {embed_description}")
    if not embed_description or "daily streak" not in embed_description:
        debug_log("Embed description missing or does not contain 'daily streak'.")
        return

    # Regex to match: <:team_logo:ID> **|** Your Faction's daily ball-type is <:ball_emoji:ID> BallName
    match = re.search(
        r"(<:team_logo:\d+>) \*\*\|\*\* Your Faction's daily ball-type is (<:[^:]+:\d+>) ([A-Za-z]+)",
        embed.description,
    )
    debug_log(f"Regex match result: {match}")
    if not match:
        pretty_log(
            "info",
            "Could not find faction ball info in daily message.",
            bot=bot,
        )
        return

    faction_team_emoji = match.group(1)
    daily_ball_emoji = match.group(2)
    daily_ball = match.group(3)
    debug_log(
        f"Matched faction_team_emoji: {faction_team_emoji}, daily_ball_emoji: {daily_ball_emoji}, daily_ball: {daily_ball}"
    )
    daily_ball = daily_ball.lower()
    pretty_log(
        "info",
        f"Extracted faction ball from daily message in {message.channel.name}: Faction Emoji: {faction_team_emoji}, Ball: {daily_ball}",
        bot=bot,
    )
    faction = get_faction_by_emoji(faction_team_emoji)
    debug_log(f"Faction resolved from emoji: {faction}")
    if not faction:
        pretty_log(
            "info",
            f"Could not determine faction from emoji {faction_team_emoji} in daily message.",
            bot=bot,
        )
        return

    member = await get_pokemeow_reply_member(message)
    debug_log(f"Member resolved from message: {member}")
    if not member:
        debug_log("No member found from get_pokemeow_reply_member.")
        return

    # Check if there is already a ball for that faction
    latest_ball = daily_faction_ball_cache.get(faction)
    debug_log(f"Latest ball in cache for faction {faction}: {latest_ball}")

    if latest_ball != daily_ball:
        debug_log(f"Updating faction ball for {faction}: {latest_ball} -> {daily_ball}")
        # Update db and cache
        await update_faction_ball(bot, faction, daily_ball)
    else:
        debug_log(f"No update needed for faction {faction}, ball unchanged.")

    # Check if user has faction or not
    user_id = member.id
    cached_member = straymon_member_cache.get(user_id)
    debug_log(f"Cached member for user_id {user_id}: {cached_member}")
    if not cached_member:
        debug_log("User is not a straymon member.")
        return  # Not straymon member
    user_faction = cached_member.get("faction")
    debug_log(f"User's current faction: {user_faction}")
    if not user_faction:
        debug_log(f"Updating user {user_id} faction to {faction}")
        # Update user faction
        await update_faction(bot, user_id, faction)
        straymon_member_cache[user_id]["faction"] = faction
    else:
        debug_log(f"User {user_id} already has faction: {user_faction}")


# 🍥──────────────────────────────────────────────
#   Extract Faction Ball from Faction Command
# 🍥──────────────────────────────────────────────
async def extract_faction_ball_from_fa(bot, message: discord.Message):
    # Extract faction from author line (e.g. "Team Magma — Headquarters")
    embed = message.embeds[0] if message.embeds else None
    if not embed:
        return

    faction = None
    if not embed.author or not embed.author.name:
        return

    author_match = re.search(r"Team (\w+)", embed.author.name)
    if not author_match:
        return

    faction = author_match.group(1)
    faction = faction.lower()

    member = await get_pokemeow_reply_member(message)
    if not member:
        return

    # Check if member has a faction
    user_id = member.id
    cached_member = straymon_member_cache.get(user_id)
    if not cached_member:
        return  # Not straymon member
    user_faction = cached_member.get("faction")
    if not user_faction:
        # Update user faction
        await update_faction(bot, user_id, faction)
        straymon_member_cache[user_id]["faction"] = faction

    # Check if there is already a ball for that faction
    daily_ball_faction = daily_faction_ball_cache.get(faction)
    if daily_ball_faction:
        return  # No change

    # Extract ball from embed description (e.g. "Your faction's daily ball-type is <:ball_emoji:ID> BallName")
    daily_ball = None
    if not embed.description:
        return

    ball_match = re.search(
        r"<:([a-zA-Z0-9_]+):\d+>\s+\*\*Today's target Pokemon are\*\*",
        embed.description,
    )
    if not ball_match:
        return
    daily_ball = ball_match.group(1)

    # Update db and cache
    if daily_ball:
        await update_faction_ball(bot, faction, daily_ball)
