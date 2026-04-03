import discord

from config.aesthetic import Emojis
from utils.loggers.pretty_logs import pretty_log
import time
# SQL TABLE
"""CREATE TABLE berry_reminder (
    user_id BIGINT,
    user_name TEXT,
    slot_number INT,
    mulch_type TEXT,
    grows_on BIGINT,
    stage TEXT,
    channel_id BIGINT,
    channel_name TEXT,
    berry_name TEXT,
    water_can_type TEXT,
    watered bool DEFAULT TRUE,
    notified_for_water bool default FALSE,
    notified bool default FALSE,
    moisture_dries_on BIGINT,
    PRIMARY KEY (user_id, slot_number)
);"""
TWO_H_MOISTURE_DRY_OUT_DURATION = 7 * 3600  # 7 hours in seconds
THREE_H_BERRY_MOISTURE_DRY_OUT_DURATION = 8 * 3600  # 8 hours in seconds
# 8 hours + 20 minutes in seconds
FOUR_H_BERRY_MOISTURE_DRY_OUT_DURATION = (8 * 3600) + (
    20 * 60
)  # 8 hours 20 minutes in seconds
FIVE_H_BERRY_MOISTURE_DRY_OUT_DURATION = 10 * 3600  # 10 hours in seconds
SIX_H_BERRY_MOISTURE_DRY_OUT_DURATION = 13 * 3600  # 13 hours in seconds


berry_map = {
    "oran berry": {
        "emoji": Emojis.oran_berry,
        "growth_duration": 2,
        "moisture_dry_out_duration": TWO_H_MOISTURE_DRY_OUT_DURATION,
    },
    "cheri berry": {
        "emoji": Emojis.cheri_berry,
        "growth_duration": 2,
        "moisture_dry_out_duration": TWO_H_MOISTURE_DRY_OUT_DURATION,
    },
    "rawst berry": {
        "emoji": Emojis.rawst_berry,
        "growth_duration": 2,
        "moisture_dry_out_duration": TWO_H_MOISTURE_DRY_OUT_DURATION,
    },
    "pecha berry": {
        "emoji": Emojis.pecha_berry,
        "growth_duration": 2,
        "moisture_dry_out_duration": TWO_H_MOISTURE_DRY_OUT_DURATION,
    },
    "aspear berry": {
        "emoji": Emojis.aspear_berry,
        "growth_duration": 2,
        "moisture_dry_out_duration": TWO_H_MOISTURE_DRY_OUT_DURATION,
    },
    "sitrus berry": {
        "emoji": Emojis.sitrus_berry,
        "growth_duration": 2,
        "moisture_dry_out_duration": TWO_H_MOISTURE_DRY_OUT_DURATION,
    },
    "salac berry": {
        "emoji": Emojis.salac_berry,
        "growth_duration": 6,
        "moisture_dry_out_duration": SIX_H_BERRY_MOISTURE_DRY_OUT_DURATION,
    },
    "chesto berry": {
        "emoji": Emojis.chesto_berry,
        "growth_duration": 3,
        "moisture_dry_out_duration": THREE_H_BERRY_MOISTURE_DRY_OUT_DURATION,
    },
    "persim berry": {
        "emoji": Emojis.persim_berry,
        "growth_duration": 3,
        "moisture_dry_out_duration": THREE_H_BERRY_MOISTURE_DRY_OUT_DURATION,
    },
    "pomeg berry": {
        "emoji": Emojis.pomeg_berry,
        "growth_duration": 4,
        "moisture_dry_out_duration": FOUR_H_BERRY_MOISTURE_DRY_OUT_DURATION,
    },
    "kelpsy berry": {
        "emoji": Emojis.kelpsy_berry,
        "growth_duration": 4,
        "moisture_dry_out_duration": FOUR_H_BERRY_MOISTURE_DRY_OUT_DURATION,
    },
    "qualot berry": {
        "emoji": Emojis.qualot_berry,
        "growth_duration": 4,
        "moisture_dry_out_duration": FOUR_H_BERRY_MOISTURE_DRY_OUT_DURATION,
    },
    "hondew berry": {
        "emoji": Emojis.hondew_berry,
        "growth_duration": 4,
        "moisture_dry_out_duration": FOUR_H_BERRY_MOISTURE_DRY_OUT_DURATION,
    },
    "grepa berry": {
        "emoji": Emojis.grepa_berry,
        "growth_duration": 4,
        "moisture_dry_out_duration": FOUR_H_BERRY_MOISTURE_DRY_OUT_DURATION,
    },
    "tamato berry": {
        "emoji": Emojis.tomato_berry,
        "growth_duration": 4,
        "moisture_dry_out_duration": FOUR_H_BERRY_MOISTURE_DRY_OUT_DURATION,
    },
    "lum berry": {
        "emoji": Emojis.lum_berry,
        "growth_duration": 5,
        "moisture_dry_out_duration": FIVE_H_BERRY_MOISTURE_DRY_OUT_DURATION,
    },
    "occa berry": {
        "emoji": Emojis.occa_berry,
        "growth_duration": FIVE_H_BERRY_MOISTURE_DRY_OUT_DURATION,
    },
    "yache berry": {
        "emoji": Emojis.yache_berry,
        "growth_duration": FIVE_H_BERRY_MOISTURE_DRY_OUT_DURATION,
    },
    "shuca berry": {
        "emoji": Emojis.shuca_berry,
        "growth_duration": FIVE_H_BERRY_MOISTURE_DRY_OUT_DURATION,
    },
}

next_stage_map = {
    "planted": "sprouted",
    "sprouted": "taller",
    "taller": "blooming",
    "blooming": "berry",
}


async def upsert_berry_reminder(
    bot: discord.Client,
    user_id: int,
    user_name: str,
    slot_number: int,
    grows_on: int,
    stage: str,
    channel_id: int,
    channel_name: str,
    berry_name: str,
    water_can_type: str = None,
    watered: bool = True,
    notified_for_water: bool = False,
    notified: bool = False,
    mulch_type: str = None,
    moisture_dries_on: int = None,
):
    """Upserts a berry reminder for the given user_id and slot_number."""
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO berry_reminder (
                    user_id, user_name, slot_number, mulch_type,
                    grows_on, stage, channel_id, channel_name,
                    berry_name, water_can_type, watered,
                    notified_for_water, notified, moisture_dries_on
                )
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                ON CONFLICT (user_id, slot_number) DO UPDATE SET
                    user_name = EXCLUDED.user_name,
                    mulch_type = COALESCE(EXCLUDED.mulch_type, berry_reminder.mulch_type),
                    grows_on = EXCLUDED.grows_on,
                    stage = EXCLUDED.stage,
                    channel_id = EXCLUDED.channel_id,
                    channel_name = EXCLUDED.channel_name,
                    berry_name = EXCLUDED.berry_name,
                    water_can_type = COALESCE(EXCLUDED.water_can_type, berry_reminder.water_can_type),
                    watered = COALESCE(EXCLUDED.watered, berry_reminder.watered),
                    notified_for_water = COALESCE(EXCLUDED.notified_for_water, berry_reminder.notified_for_water),
                    notified = COALESCE(EXCLUDED.notified, berry_reminder.notified),
                    moisture_dries_on = COALESCE(EXCLUDED.moisture_dries_on, berry_reminder.moisture_dries_on)
                """,
                user_id,
                user_name,
                slot_number,
                mulch_type,
                grows_on,
                stage,
                channel_id,
                channel_name,
                berry_name,
                water_can_type,
                watered,
                notified_for_water,
                notified,
                moisture_dries_on,
            )
        pretty_log(
            "db",
            f"Upserted berry reminder for {user_name} (user_id: {user_id}) in slot {slot_number}, "
            f"mulch={mulch_type}, grows_on={grows_on}, stage={stage}, watered={watered}, "
            f"notified_for_water={notified_for_water}, notified={notified}",
        )
    except Exception as e:
        pretty_log(
            "warn",
            f"Failed to upsert berry reminder for user {user_id} in slot {slot_number}: {e}",
        )


async def update_mulch_info(
    bot: discord.Client, user_id: int, slot_number: int, mulch_type: str
):
    """Updates the mulch type for a specific berry reminder."""
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE berry_reminder
                SET mulch_type = $1
                WHERE user_id = $2 AND slot_number = $3
                """,
                mulch_type,
                user_id,
                slot_number,
            )
        pretty_log(
            "db",
            f"Updated mulch type to {mulch_type} for user_id {user_id} in slot {slot_number}",
        )
    except Exception as e:
        pretty_log(
            "warn",
            f"Failed to update mulch type for user {user_id} in slot {slot_number}: {e}",
        )


async def get_user_berry_reminder_slot(
    bot: discord.Client, user_id: int, slot_number: int
):
    """Fetches a specific berry reminder for the given user_id and slot_number."""
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT *
                FROM berry_reminder
                WHERE user_id = $1 AND slot_number = $2;
                """,
                user_id,
                slot_number,
            )
            return dict(row) if row else None
    except Exception as e:
        pretty_log(
            "warn",
            f"Failed to fetch berry reminder for user {user_id} in slot {slot_number}: {e}",
        )
        return None


async def update_growth_stage(
    bot: discord.Client, user_id: int, slot_number: int, stage: str, grows_on: int
):
    """Updates the growth stage and grows_on time for a specific berry reminder."""
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE berry_reminder
                SET stage = $1, grows_on = $2
                WHERE user_id = $3 AND slot_number = $4
                """,
                stage,
                grows_on,
                user_id,
                slot_number,
            )
        pretty_log(
            "db",
            f"Updated growth stage to {stage} and grows_on to {grows_on} for user_id {user_id} in slot {slot_number}",
        )
    except Exception as e:
        pretty_log(
            "warn",
            f"Failed to update growth stage for user {user_id} in slot {slot_number}: {e}",
        )


async def fetch_user_all_berry_reminder(bot: discord.Client, user_id: int):
    """
    Fetches all berry reminders for the given user_id.
    Returns a list of dictionaries with keys: user_id, user_name, slot_number, grows_on, stage, channel_id, channel_name, berry_name.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT *
                FROM berry_reminder
                WHERE user_id = $1
                ORDER BY slot_number ASC;
                """,
                user_id,
            )
            return [dict(row) for row in rows]
    except Exception as e:
        pretty_log("warn", f"Failed to fetch berry reminders for user {user_id}: {e}")
        return []


async def update_water_can_type_for_slot(
    bot: discord.Client, user_id: int, slot_number: int, water_can_type: str
):
    """Updates the water can type for a specific berry reminder."""
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE berry_reminder
                SET water_can_type = $1
                WHERE user_id = $2 AND slot_number = $3
                """,
                water_can_type,
                user_id,
                slot_number,
            )
        pretty_log(
            "db",
            f"Updated water can type to {water_can_type} for user_id {user_id} in slot {slot_number}",
        )
    except Exception as e:
        pretty_log(
            "warn",
            f"Failed to update water can type for user {user_id} in slot {slot_number}: {e}",
        )


async def fetch_user_water_can_type(bot: discord.Client, user_id: int):
    """Fetches the water can type for the given user_id. Returns the water_can_type or None if not found."""
    try:
        async with bot.pg_pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT water_can_type
                FROM berry_reminder
                WHERE user_id = $1
                ORDER BY remind_on DESC
                LIMIT 1;
                """,
                user_id,
            )
            return row["water_can_type"] if row else None
    except Exception as e:
        pretty_log("warn", f"Failed to fetch water can type for user {user_id}: {e}")
        return None


async def remove_berry_reminder(
    bot: discord.Client,
    user_id: int,
    slot_number: int,
):
    """
    Removes a berry reminder for the given user_id and slot_number.
    """
    async with bot.pg_pool.acquire() as conn:
        await conn.execute(
            """
            DELETE FROM berry_reminder
            WHERE user_id = $1 AND slot_number = $2
            """,
            user_id,
            slot_number,
        )
    pretty_log(
        "db",
        f"Removed berry reminder for user_id {user_id} in slot {slot_number}",
    )


async def fetch_all_due_berry_reminders(bot: discord.Client):
    """
    Fetches all berry reminders that are due within the next minute (grows_on <= now + 60s).
    Returns a list of dictionaries with all columns from the berry_reminder table.
    """
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT DISTINCT ON (user_id, slot_number) *
                FROM berry_reminder
                WHERE grows_on <= EXTRACT(EPOCH FROM NOW())::BIGINT
                ORDER BY user_id, slot_number, grows_on ASC;
                """
            )

            return [dict(row) for row in rows]
    except Exception as e:
        pretty_log("warn", f"Failed to fetch due berry reminders: {e}")
        return []


async def update_moisture_dries_on(
    bot: discord.Client, user_id: int, slot_number: int, moisture_dries_on: int
):
    """Updates the moisture_dries_on time for a specific berry reminder."""
    try:
        async with bot.pg_pool.acquire() as conn:
            await conn.execute(
                """
                UPDATE berry_reminder
                SET moisture_dries_on = $1
                WHERE user_id = $2 AND slot_number = $3
                """,
                moisture_dries_on,
                user_id,
                slot_number,
            )
        pretty_log(
            "db",
            f"Updated moisture_dries_on to {moisture_dries_on} for user_id {user_id} in slot {slot_number}",
        )
    except Exception as e:
        pretty_log(
            "warn",
            f"Failed to update moisture_dries_on for user {user_id} in slot {slot_number}: {e}",
        )


async def fetch_all_due_moisture_dries_on(bot: discord.Client):
    """
    Fetches all berry reminders where moisture_dries_on is due"""
    try:
        async with bot.pg_pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT DISTINCT ON (user_id, slot_number) *
                FROM berry_reminder
                WHERE moisture_dries_on <= EXTRACT(EPOCH FROM NOW())::BIGINT
                ORDER BY user_id, slot_number, moisture_dries_on ASC;
                """
            )

            return [dict(row) for row in rows]
    except Exception as e:
        pretty_log("warn", f"Failed to fetch due moisture_dries_on reminders: {e}")
        return []


async def update_moisture_dries_on_func(
    bot: discord.Client, user_id: int, slot_number: int, berry_name: str
):
    """Updates the moisture_dries_on time for a specific berry reminder based on the watering time."""
    try:
        berry_info = berry_map.get(berry_name.lower())
        if not berry_info:
            pretty_log("warn", f"Berry name '{berry_name}' not found in berry_map.")
            return

        moisture_dry_out_duration = berry_info["moisture_dry_out_duration"]
        new_moisture_dries_on = int(time.time()) + moisture_dry_out_duration
        await update_moisture_dries_on(bot, user_id, slot_number, new_moisture_dries_on)
    except Exception as e:
        pretty_log(
            "warn",
            f"Failed to update moisture_dries_on for user {user_id} in slot {slot_number} with berry '{berry_name}': {e}",
        )
