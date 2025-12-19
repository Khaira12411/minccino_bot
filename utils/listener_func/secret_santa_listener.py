import discord

from utils.database.misc_pokemeow_reminders_db import upsert_secret_santa_reminder
from utils.essentials.pokemeow_helpers import get_pokemeow_reply_member
from utils.loggers.pretty_logs import pretty_log
from config.aesthetic import Emojis

# 🍭 Listener for Secret Santa participation
async def secret_santa_listener(bot: discord.Client, message: discord.Message):
    """
    Listener that triggers when a user participates in Secret Santa.
    Sets a reminder for 4 hours later.
    """

    member = await get_pokemeow_reply_member(message)
    if not member:
        return
    user_id = member.id
    user_name = member.name
    channel_id = message.channel.id

    # Upsert Secret Santa reminder for 4 hours later
    await upsert_secret_santa_reminder(bot, user_id, user_name, channel_id)
    await message.add_reaction(Emojis.santa_mouse)  # React with Santa emoji to confirm participation
