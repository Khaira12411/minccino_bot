# cogs/reminders.py
import discord
from discord import app_commands
from discord.ext import commands

from config.aesthetic import *
from group_func.toggle.reminders.reminders_sched_db_func import fetch_user_schedules
from utils.embeds.design_embed import design_embed
from utils.essentials.loader.loader import *

# ─────────────── Reminder Emoji Mapping ───────────────
REMINDER_EMOJI_MAP = {
    "relics": Emojis.relic,
    "catchbot": Emojis.robot,
    "default": "🔹",
}


class RemindersCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="reminders", description="View your scheduled reminders")
    async def reminders(self, interaction: discord.Interaction):
        handler = await minccino_defer(
            interaction=interaction, content="Fetching your reminders..."
        )
        user_id = interaction.user.id
        reminders = await fetch_user_schedules(self.bot, user_id)

        if not reminders:
            await handler.stop(content="❌ You have no scheduled reminders.")
            return

        lines = []
        for row in reminders:
            type_ = row.get("type", "unknown").title()
            type_key = (row.get("type") or "default").lower()
            ends_on = row.get("ends_on")
            remind_next_on = row.get("remind_next_on")
            sent = row.get("reminder_sent", False)

            emoji = REMINDER_EMOJI_MAP.get(type_key, REMINDER_EMOJI_MAP["default"])
            line = f"{emoji} **{type_}**"

            if type_key == "catchbot":
                if ends_on:
                    line += f"\n**Arrives On:** <t:{ends_on}:f>"
                if remind_next_on:
                    line += f"\n**Sent Next Reminder:** {'✅' if sent else '❌'}"
            else:
                sub_lines = []
                if ends_on:
                    sub_lines.append(f"**Ends On:** <t:{ends_on}:f>")
                if remind_next_on:
                    sub_lines.append(f"**Next Remind:** <t:{remind_next_on}:f>")
                    sub_lines.append(
                        f"**Sent Next Reminder:** {'✅' if sent else '❌'}"
                    )
                elif sent:
                    # If no next reminder, don't show sent
                    pass

                if sub_lines:
                    line += " | " + " | ".join(sub_lines)

            lines.append(line)

        desc = "\n".join(lines)

        embed = discord.Embed(
            title="📋 Your Scheduled Reminders",
            description=desc,
            color=0x8A2BE2,
        )

        embed = design_embed(
            user=interaction.user,
            embed=embed,
            thumbnail_url=MINC_Thumbnails.reminders,
            footer_text="⏰ Manage your reminders wisely!",
            image_url=None,
            color="purple",
        )

        await handler.success(embed=embed, override_public=True, content="")


async def setup(bot: commands.Bot):
    await bot.add_cog(RemindersCog(bot))
