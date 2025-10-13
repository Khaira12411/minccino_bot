import re
import discord
from config.faction_data import FACTION_LOGO_EMOJIS, get_faction_by_emoji
from utils.loggers.pretty_logs import pretty_log
from utils.cache.daily_fa_ball_cache import daily_faction_ball_cache
from utils.cache.straymon_member_cache import straymon_member_cache
from utils.cache.faction_ball_alert_cache import faction_ball_alert_cache
from utils.essentials.pokemeow_helpers import get_pokemeow_reply_member
from utils.database.daily_fa_ball import update_faction_ball
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
    embed = message.embeds[0] if message.embeds else None
    if not embed:
        return

    embed_description = embed.description or ""
    if not embed_description or "daily streak" not in embed_description:
        return

    # Regex to match: <:team_logo:ID> **|** Your Faction's daily ball-type is <:ball_emoji:ID> BallName
    match = re.search(
        r"(<:team_logo:\d+>) \*\*\|\*\* Your Faction's daily ball-type is (<:[^:]+:\d+>) (\w+ball)",
        embed.description,
    )
    if not match:
        return

    faction_team_emoji = match.group(1)
    daily_ball_emoji = match.group(2)
    daily_ball = match.group(3)
    daily_ball = daily_ball.lower()

    faction = get_faction_by_emoji(faction_team_emoji)
    if not faction:
        pretty_log(
            "info",
            f"Could not determine faction from emoji {faction_team_emoji} in daily message.",
            bot=bot,
        )
        return

    member = await get_pokemeow_reply_member(message)
    if not member:
        return

    # Check if user has faction or not
    user_id = member.id
    cached_member = straymon_member_cache.get(user_id)
    if not cached_member:
        return # Not straymon member
    user_faction = cached_member.get("faction")
    if not user_faction:
        # Update user faction
        await update_faction(bot, user_id, faction)
        straymon_member_cache[user_id]["faction"] = faction

    # Check if there is already a ball for that faction
    latest_ball = daily_faction_ball_cache.get(faction)
    if latest_ball == daily_ball:
        return  # No change
    
    # Update db and cache
    await update_faction_ball(bot, faction, daily_ball)


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
        return # Not straymon member
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