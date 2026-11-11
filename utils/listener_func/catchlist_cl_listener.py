import re
import time
from dataclasses import dataclass, field

import discord

from utils.database.catchlist_db import upsert_catchlist, upsert_catchlist_rank
from utils.essentials.ball_names import normalize_ball_type
from utils.essentials.balls_to_bring import build_balls_to_bring_embed
from utils.essentials.pokemeow_helpers import get_pokemeow_reply_or_interaction_member
from utils.loggers.debug_log import debug_log
from utils.loggers.pretty_logs import pretty_log

CATCHLIST_CACHE_TTL = 30 * 60
_ROW_START = re.compile(r"^\s*(?:✅|◻️?|⬜️?)")


@dataclass
class CatchlistPages:
    title: str
    catch_list_date: str
    total_pages: int
    updated_at: float
    pages: dict[int, list[dict]] = field(default_factory=dict)
    profile_rank: dict | None = None
    expected_mons: int | None = None
    last_result: dict | None = None
    last_saved: dict | None = None
    last_rank_saved: dict | None = None


_catchlist_pages: dict[int, CatchlistPages] = {}


# Date Extractor
def extract_catch_list_date(message: str):
    match = re.search(r"-\s*(.+)$", message)

    catch_list_date = match.group(1).strip() if match else None
    return catch_list_date


def _parse_catchlist_mon(value: str) -> dict | None:
    pattern = re.compile(
        r"(?P<completion>✅|◻️?|⬜️?)\s*"
        r"<a?:[^:]+:\d+>\s*(?P<pokemon_name>.+?)\s+from\s*"
        r"<a?:[^:]+:\d+>\s*`(?P<catch_type>[^`]+)`\s*"
        r"(?:\r?\n|\s+)"
        r"<a?:[^:]+:\d+>\s*\*\*(?P<ball_type>.+?)\*\*\s*·\s*"
        r"(?P<exp_amount>(?:\d{1,3}(?:,\d{3})+|\d+))\s+EXP",
        re.IGNORECASE | re.DOTALL,
    )

    match = pattern.search(value)
    if not match:
        return None
    return {
        "pokemon_name": match.group("pokemon_name").strip().lower(),
        "ball_type": normalize_ball_type(match.group("ball_type")),
        "catch_type": match.group("catch_type").strip().lower(),
        "exp_amount": int(match.group("exp_amount").replace(",", "")),
        "completion": match.group("completion") == "✅",
    }


def parse_catchlist_mons(embed: discord.Embed):
    return [
        mon
        for embed_field in embed.fields
        if (mon := _parse_catchlist_mon(embed_field.value)) is not None
    ]


def _is_catchlist_row_field(value: str) -> bool:
    return bool(_ROW_START.match(value))


def parse_profile_rank(embed: discord.Embed):
    for field in embed.fields:
        if field.name.lower() == "profile rank":
            pattern = re.search(
                r"\*\*(.*?)\*\*.*?"
                r"\*\*([\d,]+)\*\*\s*total EXP.*?"
                r"\*\*([\d,]+)\s*EXP\*\*",
                field.value,
                re.IGNORECASE | re.DOTALL,
            )

            if not pattern:
                return None

            return {
                "rank_name": pattern.group(1).strip().lower(),
                "total_exp": int(pattern.group(2).replace(",", "")),
                "exp_needed_fr_nex_rank": int(pattern.group(3).replace(",", "")),
            }

    return None


def extract_catchlist_pages(footer: str):
    match = re.search(r"Page\s+(\d+)\s*/\s*(\d+)", footer, re.IGNORECASE)

    if not match:
        return None

    return {"current_page": int(match.group(1)), "total_pages": int(match.group(2))}


def is_catchlist_noncompact_embed(embed: discord.Embed | None) -> bool:
    if not embed:
        return False
    description = embed.description or ""
    footer = embed.footer.text or ""
    return (
        "Catch the listed Pokémon with its required ball" in description
        and "activity (all)" in footer.lower()
        and any(
            _is_catchlist_row_field(embed_field.value) for embed_field in embed.fields
        )
    )


def is_catchlist_owner(title: str, member: discord.Member | discord.User) -> bool:
    title = re.sub(r"\\(.)", r"\1", title)
    title = re.sub(r"[\u200b-\u200d\u2060\ufeff]", "", title)
    return bool(
        re.fullmatch(
            r"\s*(?:<a?:[^:]+:\d+>\s*|[^\w\s]+\s*)?"
            + re.escape(member.name)
            + r"'s catchlist\s*-\s*.+",
            title,
            re.IGNORECASE,
        )
    )


def _read_page(embed: discord.Embed, message_id: int):
    title = embed.title or ""
    date = extract_catch_list_date(title)
    page_info = extract_catchlist_pages(embed.footer.text or "")
    description = embed.description or ""
    mons = parse_catchlist_mons(embed)
    row_fields = [
        embed_field
        for embed_field in embed.fields
        if _is_catchlist_row_field(embed_field.value)
    ]
    row_count = len(row_fields)
    problems = []
    if not date:
        problems.append(
            f"missing date in title (title present: {bool(title)}, "
            f"author present: {bool(embed.author.name)})"
        )
    if not page_info:
        problems.append("missing page numbers in footer")
    elif not 1 <= page_info["current_page"] <= page_info["total_pages"]:
        problems.append("invalid page numbers")
    if not row_count or len(mons) != row_count:
        problems.append(f"recognized {row_count} rows, parsed {len(mons)}")
    if problems:
        pretty_log(
            tag="warn",
            message=(
                f"Could not fully parse catchlist page for message {message_id}: "
                f"{'; '.join(problems)}. Not collecting it."
            ),
            label="CatchlistListener",
        )
        if not row_count or len(mons) != row_count:
            sample = next(
                (
                    embed_field.value
                    for embed_field in row_fields
                    if not _parse_catchlist_mon(embed_field.value)
                ),
                None,
            )
            if sample:
                pretty_log(
                    tag="debug",
                    message=f"Example unparsed catchlist row (raw): {sample!r}",
                    label="CatchlistListener",
                )
        return None
    expected_mons = None
    for embed_field in embed.fields:
        if embed_field.name.lower() == "this month":
            match = re.search(r"([\d,]+)\s*/\s*([\d,]+)", embed_field.value)
            if match:
                expected_mons = int(match.group(2).replace(",", ""))
            break
    return title, date, page_info, mons, parse_profile_rank(embed), expected_mons


def _format_catchlist_embeds(data: dict) -> list[discord.Embed]:
    lines = []
    for mon in data["catch_list_mons"]:
        status = "✅" if mon["completion"] else "◻️"
        lines.append(
            f"{status} **{mon['pokemon_name'].title()}** · "
            f"{mon['ball_type'].title()} · "
            f"`{mon['catch_type']}` · "
            f"**{mon['exp_amount']:,} EXP**"
        )

    chunks = []
    current = ""
    for line in lines:
        if len(current) + len(line) + 1 > 4000:
            chunks.append(current)
            current = ""
        current += line + "\n"
    if current:
        chunks.append(current)

    embeds = []
    for index, chunk in enumerate(chunks):
        response = discord.Embed(
            title=f"Catchlist Data - {data['catch_list_date']}",
            description=chunk,
            color=discord.Color.green(),
        )
        response.set_footer(
            text=f"Pokémon: {len(lines)} · Part {index + 1}/{len(chunks)}"
        )
        if index == 0:
            rank = data["profile_rank"]
            rank_text = "Not found"
            if rank:
                rank_text = (
                    f"**{rank['rank_name'].title()}**\n"
                    f"Total EXP: **{rank['total_exp']:,}**\n"
                    f"EXP to next rank: **{rank['exp_needed_fr_nex_rank']:,}**"
                )
            response.add_field(name="Profile Rank", value=rank_text, inline=False)
        embeds.append(response)
    return embeds


async def parse_catchlist_cl_noncompact(
    bot: discord.Client, message: discord.Message, before: discord.Message | None = None
):
    member = await get_pokemeow_reply_or_interaction_member(message)
    if not member:
        return None
    from utils.cache.user_alert_cache import fetch_user_alert_notify_cache

    catchlist_alert_type = fetch_user_alert_notify_cache(member.id, "catchlist")
    if not catchlist_alert_type:
        debug_log(f"No catchlist alert info for member {member.id}")
        return

    now = time.monotonic()
    for message_id, state in list(_catchlist_pages.items()):
        if now - state.updated_at >= CATCHLIST_CACHE_TTL:
            del _catchlist_pages[message_id]
            pretty_log(
                tag="debug",
                message=f"Expired catchlist collection for message {message_id}.",
                label="CatchlistListener",
            )

    embed = message.embeds[0] if message.embeds else None
    if not is_catchlist_noncompact_embed(embed):
        return None
    page = _read_page(embed, message.id)
    if not page:
        _catchlist_pages.pop(message.id, None)
        return None
    title, date, page_info, mons, rank, expected_mons = page
    state = _catchlist_pages.get(message.id)
    if (
        state is None
        or state.title != title
        or state.catch_list_date != date
        or state.total_pages != page_info["total_pages"]
        or (
            expected_mons is not None
            and state.expected_mons is not None
            and state.expected_mons != expected_mons
        )
        or (
            before is not None
            and before.embeds
            and not is_catchlist_noncompact_embed(before.embeds[0])
        )
    ):
        state = CatchlistPages(title, date, page_info["total_pages"], now)
        _catchlist_pages[message.id] = state

    if before and before.id == message.id and before.embeds:
        previous_embed = before.embeds[0]
        if is_catchlist_noncompact_embed(previous_embed):
            previous = _read_page(previous_embed, message.id)
            if previous:
                old_title, old_date, old_info, old_mons, old_rank, old_expected = (
                    previous
                )
                if (
                    old_title == title
                    and old_date == date
                    and old_info["total_pages"] == state.total_pages
                    and (
                        old_expected is None
                        or expected_mons is None
                        or old_expected == expected_mons
                    )
                    and old_info["current_page"] not in state.pages
                ):
                    state.pages[old_info["current_page"]] = old_mons
                    if old_rank:
                        state.profile_rank = old_rank
                    if old_expected is not None:
                        state.expected_mons = old_expected

    state.updated_at = now
    state.pages[page_info["current_page"]] = mons
    if rank:
        state.profile_rank = rank
    if expected_mons is not None:
        state.expected_mons = expected_mons
    if len(state.pages) != state.total_pages:
        rank_to_save = state.profile_rank
        if (
            rank_to_save
            and rank_to_save != state.last_rank_saved
            and is_catchlist_owner(state.title, member)
        ):
            await upsert_catchlist_rank(
                bot=bot,
                user_id=member.id,
                user_name=member.name,
                catchlist_date=state.catch_list_date,
                rank_name=rank_to_save["rank_name"],
                total_exp=rank_to_save["total_exp"],
                exp_needed=rank_to_save["exp_needed_fr_nex_rank"],
            )
            state.last_rank_saved = rank_to_save
        return None

    data = {
        "catch_list_date": state.catch_list_date,
        "catch_list_mons": [
            mon
            for number in range(1, state.total_pages + 1)
            for mon in state.pages[number]
        ],
        "profile_rank": state.profile_rank,
    }
    if (
        state.expected_mons is not None
        and len(data["catch_list_mons"]) != state.expected_mons
    ):
        pretty_log(
            tag="warn",
            message=(
                f"Catchlist message {message.id} has {len(data['catch_list_mons'])} "
                f"parsed Pokémon, but reports {state.expected_mons}; not completing it."
            ),
            label="CatchlistListener",
        )
        return None
    if not is_catchlist_owner(state.title, member):
        pretty_log(
            tag="warn",
            message=(
                f"Catchlist owner could not be verified against command user "
                f"{member.id} for message {message.id}; not saving."
            ),
            label="CatchlistListener",
        )
        pretty_log(
            tag="debug",
            message=(
                f"Owner verification: title={state.title!r}, "
                f"username={member.name!r}, display_name={member.display_name!r}."
            ),
            label="CatchlistListener",
        )
        return data
    elif data != state.last_saved:
        rank = data["profile_rank"] or {}
        await upsert_catchlist(
            bot=bot,
            user_id=member.id,
            user_name=member.name,
            catchlist_date=data["catch_list_date"],
            catchlist_mons=data["catch_list_mons"],
            rank_name=rank.get("rank_name"),
            total_exp=rank.get("total_exp"),
            exp_needed=rank.get("exp_needed_fr_nex_rank"),
        )
        state.last_saved = data
        pretty_log(
            tag="db",
            message=f"Saved catchlist for user {member.id}.",
            label="CatchlistListener",
        )

    if data == state.last_result:
        return None
    state.last_result = data
    try:
        # for response in _format_catchlist_embeds(data):
        #     await message.channel.send(embed=response)
        balls_embed = build_balls_to_bring_embed(data["catch_list_mons"])
        await message.channel.send(
            "Catchlist successfully saved!",
            **({"embed": balls_embed} if balls_embed else {}),
        )
    except discord.HTTPException:
        state.last_result = None
        raise
    return data
