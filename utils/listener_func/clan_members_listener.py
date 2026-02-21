import asyncio
import re
from datetime import datetime

import discord

from config.current_setup import STRAYMONS_GUILD_ID, REQUIRED_PROBATION_CATCHES
from config.straymons_constants import STRAYMONS__ROLES, STRAYMONS__TEXT_CHANNELS
from utils.cache.straymon_member_cache import straymon_member_cache
from utils.loggers.debug_log import debug_log, enable_debug
from utils.loggers.pretty_logs import pretty_log
from utils.database.probation_members_db import (
    get_probation_member_status,
    update_probation_member_status,
    upsert_probation_member,
)
from utils.essentials.webhook import send_webhook

# enable_debug(f"{__name__}.fl_rs_checker")


def extract_page_numbers(text):
    match = re.search(r"Page\s*(\d+)\s*/\s*(\d+)", text)
    if match:
        current_page = int(match.group(1))
        total_pages = int(match.group(2))
        return current_page, total_pages
    return None, None


def get_member_from_line(guild: discord.Guild, user_line):
    """Extract member object from user line in embed."""
    cleaned = user_line.replace("**", "").strip()
    # Try to match patterns like '<@id> - id}' or '<@id> - id' or just 'id'
    # Regex for <@digits> - digits (with or without trailing })
    match = re.match(r"\d+\s+<@(?P<uid1>\d+)>\s*-\s*(?P<uid2>\d+)}?", cleaned)
    if match:
        # Always use the second ID after the dash for cache lookup
        user_id = int(match.group("uid2"))
        member = guild.get_member(user_id)
        if member:
            return member, user_id
        else:
            return None, user_id

    # Try to match just <@id> - id (without leading number)
    match2 = re.match(r"<@(?P<uid1>\d+)>\s*-\s*(?P<uid2>\d+)}?", cleaned)
    if match2:
        user_id = int(match2.group("uid2"))
        member = guild.get_member(user_id)
        if member:
            return member, user_id
        else:
            return None, user_id

    # Fallback: try to extract last word as user id if it's all digits
    parts = cleaned.split()
    if parts and re.fullmatch(r"\d{10,}", parts[-1]):
        user_id = int(parts[-1])
        member = guild.get_member(user_id)
        return member
    # Otherwise, fallback to original logic: everything after first space
    from utils.cache.straymon_member_cache import fetch_straymon_user_id_by_username

    user_name = cleaned.split(" ", 1)[-1] if " " in cleaned else cleaned
    user_id = fetch_straymon_user_id_by_username(user_name)
    if user_id:
        member = guild.get_member(user_id)
        return member, user_id
    else:
        return None, None


async def clan_members_command_listener(
    bot, message: discord.Message, msg_context: str = None
):
    """Listener for clan members command."""

    embed = message.embeds[0] if message.embeds else None
    if not embed:
        debug_log("No embed found in message.")
        return

    embed_description = embed.description or ""
    if "Clan Member Information - Straymons" not in embed_description:
        debug_log("Embed does not contain expected description header.")
        return

    straymon_guild = bot.get_guild(STRAYMONS_GUILD_ID)
    if not straymon_guild:
        return

    user_lines = embed.fields[0].value.splitlines()
    contribution_line = embed.fields[1].value.splitlines()
    current_page, total_pages = extract_page_numbers(embed.footer.text)
    debug_log(
        f"Extracted page numbers: current_page={current_page}, total_pages={total_pages}"
    )

    # Process each user line and contribution line together
    for user_line, contrib_line in zip(user_lines, contribution_line):
        debug_log(f"Processing user_line: {user_line}, contrib_line: {contrib_line}")
        user_name = user_line.split(" ", 1)[-1].replace("**", "").strip()
        member, user_id = get_member_from_line(straymon_guild, user_line)

        if not member:
            debug_log(f"Could not find member for user_line: {user_line}")
            continue

        # Check if member has probation role
        probation_role = straymon_guild.get_role(STRAYMONS__ROLES.probation)
        if probation_role not in member.roles:
            debug_log(f"Member {member} does not have probation role, skipping.")
            continue
        # Extract contribution number from contrib_line
        contrib_match = re.search(r"> ?\*?\*?([\d,]+)", contrib_line)
        catches = (
            int(contrib_match.group(1).replace(",", "")) if contrib_match else None
        )
        debug_log(f"Extracted catches: {catches} from contrib_line: {contrib_line}")

        if catches and catches >= REQUIRED_PROBATION_CATCHES:
            # Update status to Passed
            await update_probation_member_status(bot, member.id, "Passed")
            pretty_log(
                "info",
                f"Probation status updated to 'Passed' for {member.name} ({member.id}) after catching {catches} Pokémon.",
                label="💠 Weekly Goal Tracker",
            )
            embed = discord.Embed(
                title="Probation Member Status Set to Passed",
                description=(
                    f"**Member:** {member.mention}\n"
                    f"**Reason:** Caught {catches} Pokémon during probation period."
                ),
                color=discord.Color.green(),
                timestamp=datetime.now(),
            )
            embed.set_footer(text=f"User ID: {member.id}", icon_url=straymon_guild.icon.url)
            embed.set_author(
                name=member.display_name, icon_url=member.display_avatar.url
            )
            report_channel = straymon_guild.get_channel(
                STRAYMONS__TEXT_CHANNELS.reports
            )
            await send_webhook(bot, report_channel, embed=embed)
