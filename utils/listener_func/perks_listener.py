# ─────────────────────────────
# 🔹 Auto-fetch PokéMeow perks (updated with reactions)
# ─────────────────────────────
import re
import json
import discord
from utils.cache.ball_reco_cache import load_ball_reco_cache
from group_func.toggle.ball_recon.ball_recon_db_func import (
    fetch_user_rec,
    upsert_user_rec,
    update_user_rec,
)
from utils.loggers.pretty_logs import pretty_log
from utils.essentials.pokemeow_helpers import is_pokemeow_reply
from config.straymons_constants import STRAYMONS__ROLES

ALLOWED_ROLES = {STRAYMONS__ROLES.clan_staff, STRAYMONS__ROLES.sunrise_scone}


async def auto_update_catchboost(bot: discord.Client, message: discord.Message):
    """
    Listen for PokéMeow perk embeds and auto-update user's catch boost.

    Only triggers if:
    - Message is a PokéMeow reply
    - Member has allowed roles
    - Embed contains catch boost info
    """
    try:
        member = is_pokemeow_reply(message)
        if not member:
            return

        # 🛑 Member must have allowed roles (IDs)
        member_role_ids = {r.id for r in member.roles}
        if not (ALLOWED_ROLES & member_role_ids):
            return

        # 🛑 Must have embed
        if not getattr(message, "embeds", None) or not message.embeds:
            return

        embed = message.embeds[0]
        description = embed.description or ""

        # 🛑 Must have perks in author name
        if not getattr(embed.author, "name", "") or "perks" not in embed.author.name.lower():
            return

        # 🛑 Extract catch boost
        catchboost_match = re.search(r"Catch boost\*\*: \+?([\d.]+)%", description)
        catchboost = float(catchboost_match.group(1)) if catchboost_match else 0.0

        # 🛑 Check if "ninja" is in description → is_patreon
        is_patreon = "ninja" in description.lower()

        # 🛑 Fetch existing record
        existing = await fetch_user_rec(bot, member.id)

        # Normalize schemas for held_items, pokemon, fishing
        DEFAULT_HELD_ITEMS = {
            "rare": False,
            "shiny": False,
            "common": False,
            "uncommon": False,
            "legendary": False,
            "superrare": False,
            "display_mode": "Best Ball",
        }
        DEFAULT_POKEMON = DEFAULT_HELD_ITEMS.copy()
        DEFAULT_FISHING = DEFAULT_HELD_ITEMS.copy()

        def normalize(data, defaults):
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except json.JSONDecodeError:
                    data = {}
            if not isinstance(data, dict):
                data = {}
            return {key: bool(data.get(key, False)) for key in defaults.keys()}

        held_items = normalize(
            existing.get("held_items") if existing else {}, DEFAULT_HELD_ITEMS
        )
        pokemon = normalize(
            existing.get("pokemon") if existing else {}, DEFAULT_POKEMON
        )
        fishing = normalize(
            existing.get("fishing") if existing else {}, DEFAULT_FISHING
        )

        # 🛑 Upsert if no record, else update only if changed
        action = None
        if not existing:
            await upsert_user_rec(
                bot,
                user_id=member.id,
                user_name=str(member),
                catch_rate_bonus=catchboost,
                is_patreon=is_patreon,
                held_items=held_items,
                pokemon=pokemon,
                fishing=fishing,
            )
            action = "Inserted"
        else:
            db_catch = existing.get("catch_rate_bonus", 0)
            db_patreon = existing.get("is_patreon", False)
            if db_catch == catchboost and db_patreon == is_patreon:
                return  # nothing changed
            await update_user_rec(
                bot,
                user_id=member.id,
                user_name=str(member),
                catch_rate_bonus=catchboost,
                is_patreon=is_patreon,
                held_items=held_items,
                pokemon=pokemon,
                fishing=fishing,
            )
            action = "Updated"

        # 🛑 Reload cache
        await load_ball_reco_cache(bot)

        # 🛑 React to the original member's message
        try:
            if message.reference and message.reference.resolved:
                await message.reference.resolved.add_reaction("✅")
        except Exception as e:
            pretty_log(
                tag="error",
                message=f"Failed to add reaction to member's message: {e}",
                label="BALL_RECO",
            )

        pretty_log(
            tag="success",
            message=f"{action} catch boost for {member} → {catchboost}%, is_patreon={is_patreon}",
            label="BALL_RECO",
        )

    except Exception as e:
        pretty_log(
            tag="error",
            message=f"Failed to auto-update catch boost: {e}",
            label="BALL_RECO",
        )
