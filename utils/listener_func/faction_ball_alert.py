import re

import discord

from config.aesthetic import Emojis_Balls, Emojis_Factions
from config.faction_data import get_faction_by_emoji
from utils.cache.daily_fa_ball_cache import daily_faction_ball_cache
from utils.cache.faction_ball_alert_cache import faction_ball_alert_cache
from utils.cache.straymon_member_cache import straymon_member_cache
from utils.essentials.pokemeow_helpers import get_pokemeow_reply_member
from utils.loggers.debug_log import debug_log, enable_debug
from utils.loggers.pretty_logs import pretty_log

#enable_debug(f"{__name__}.faction_ball_alert")
FISHING_COLOR = 0x87CEFA


# 🛡️────────────────────────────────────────────
#      🛡️ Faction Ball Alert Listener
# 🛡️────────────────────────────────────────────
async def faction_ball_alert(before: discord.Message, after: discord.Message):
    try:
        debug_log("Function called")
        if not after.embeds or not after.embeds[0].description:
            debug_log("No embeds or description found, returning early")
            return

        description_text = after.embeds[0].description
        debug_log(f"Embed description: {description_text!r}")

        if description_text and "<:team_logo:" not in description_text:
            debug_log("No team_logo emoji in description, returning early")
            return
        team_logo_emoji = re.findall(r"<:team_logo:\d+>", description_text)
        debug_log(f"Extracted team_logo emojis: {team_logo_emoji}")

        if len(team_logo_emoji) != 1:
            debug_log(
                f"Expected exactly one team_logo emoji, found {len(team_logo_emoji)}. Returning early."
            )
            return

        embed_faction = (
            get_faction_by_emoji(team_logo_emoji[0]) if team_logo_emoji else None
        )
        debug_log(f"Embed faction: {embed_faction}")
        if not embed_faction:
            debug_log("Could not determine faction from emoji, returning early")
            return

        trainer_id = None
        trainer_name = None
        user_id = None
        member = await get_pokemeow_reply_member(before)
        debug_log(f"Reply member: {member}")
        if not member:
            debug_log("No replied member found, attempting fallback extraction")
            embed_color = after.embeds[0].color
            if embed_color and (
                embed_color.value == FISHING_COLOR or embed_color == FISHING_COLOR
            ):
                debug_log(
                    "Embed color matches fishing color, attempting to extract trainer ID from reference"
                )
                if after.reference and getattr(after.reference, "resolved", None):
                    resolved_author = getattr(after.reference.resolved, "author", None)
                    trainer_id = resolved_author.id if resolved_author else None
                    debug_log(f"Extracted trainer ID from reference: {trainer_id}")

                if not trainer_id and after.embeds[0].description:
                    name_match = re.search(r"\*\*(.+?)\*\*", after.embeds[0].description)
                    if name_match:
                        trainer_name = name_match.group(1)
                        debug_log(f"Extracted trainer name: {trainer_name}")

                if not trainer_id and not trainer_name:
                    debug_log("Could not extract trainer ID or name, returning early")
                    return
            else:
                debug_log("Embed color does not match fishing color, returning early")
                return
        #
        if member:
            user_id = member.id
        elif trainer_id:
            user_id = trainer_id
        elif trainer_name:
            user = discord.utils.find(lambda m: m.display_name == trainer_name, after.guild.members)
            user_id = user.id if user else None

        user_faction_ball_alert = faction_ball_alert_cache.get(user_id)
        debug_log(f"User faction ball alert settings: {user_faction_ball_alert}")
        if not user_faction_ball_alert:
            debug_log("No faction ball alert settings for user, returning early")
            return

        user_faction_ball_notify = user_faction_ball_alert.get("notify")
        debug_log(f"User faction ball notify setting: {user_faction_ball_notify}")
        if not user_faction_ball_notify or user_faction_ball_notify.lower() == "off":
            debug_log("User notify setting is off or missing, returning early")
            return

        display_embed_faction_emoji = getattr(Emojis_Factions, embed_faction)
        display_embed_faction = (
            f"{display_embed_faction_emoji} {embed_faction.title()}"
            if display_embed_faction_emoji
            else embed_faction.title()
        )
        user_name = member.display_name
        user_mention = member.mention

        user_faction = straymon_member_cache.get(user_id, {}).get("faction")
        debug_log(f"User faction: {user_faction}")
        if not user_faction:
            debug_log("User has no faction set, returning early")
            return

        faction_ball = daily_faction_ball_cache.get(user_faction)
        debug_log(f"Faction daily ball: {faction_ball}")
        if not faction_ball:
            content = f"{user_mention} I don't know your faction's daily ball yet, can you do `;fa`? Thanks!."
            await after.channel.send(content=content)
            pretty_log(
                "info",
                f"Could not send faction ball alert to {user_name} ({user_id}) for {embed_faction} daily ball because their faction {user_faction} has no daily ball set.",
            )
            debug_log(
                "No daily ball set for user's faction, sent reminder message and returned early"
            )
            return

        ball_emoji = getattr(Emojis_Balls, faction_ball.lower())
        debug_log(f"Ball emoji for daily ball: {ball_emoji}")
        if ball_emoji:
            if user_faction_ball_notify == "on":
                content = f"<@{user_id}>, This Pokemon is a daily {display_embed_faction} hunt! Use {ball_emoji}!"
                await after.channel.send(content)
                pretty_log(
                    "sent",
                    f"Sent faction ball alert to {user_name} ({user_id}) for {embed_faction} daily ball {faction_ball}",
                )
                debug_log("Sent faction ball alert with ping")
            elif user_faction_ball_notify == "on_no_pings":
                content = f"{user_name}, This Pokemon is a daily {display_embed_faction} hunt! Use {ball_emoji}!"
                await after.channel.send(content)
                pretty_log(
                    "sent",
                    f"Sent faction ball alert (no ping) to {user_name} ({user_id}) for {embed_faction} daily ball {faction_ball}",
                )
                debug_log("Sent faction ball alert without ping")
            elif user_faction_ball_notify == "react":
                try:
                    await after.add_reaction(ball_emoji)
                    debug_log("Added ball emoji reaction")
                except Exception as e:
                    pretty_log("error", f"Failed to add reaction {ball_emoji}: {e}")
                    debug_log(f"Failed to add reaction: {e}")
        else:
            debug_log("No ball emoji found for daily ball, nothing sent")

    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to process faction ball alert: {e}",
            label="FACTION_BALL_ALERT",
        )
        debug_log(f"Exception occurred: {e}", highlight=True)
