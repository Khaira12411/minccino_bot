import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View

from config.straymons_constants import STRAYMONS__ROLES
from utils.embeds.design_embed import design_embed
from utils.essentials.loader.pretty_defer import *
from utils.loggers.pretty_logs import pretty_log


# 🌸───────────────────────────────────────────────🌸
# 🩷 ⏰ Weekly Goal View Paginator                  🩷
# 🌸───────────────────────────────────────────────🌸
class WeeklyGoalPaginator(View):
    def __init__(self, bot, user, goals, per_page=25, timeout=120):
        super().__init__(timeout=timeout)
        self.bot = bot
        self.user = user
        self.goals = goals
        self.per_page = per_page
        self.page = 0
        self.max_page = (len(goals) - 1) // per_page
        self.message: discord.Message | None = None

        if self.max_page == 0:
            self.clear_items()

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.primary)
    async def prev_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(
                "This is not your paginator.", ephemeral=True
            )
            return
        self.page = (self.page - 1) % (self.max_page + 1)
        await interaction.response.edit_message(embed=(await self.get_embed()))

    @discord.ui.button(label="Next", style=discord.ButtonStyle.primary)
    async def next_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(
                "This is not your paginator.", ephemeral=True
            )
            return
        self.page = (self.page + 1) % (self.max_page + 1)
        await interaction.response.edit_message(embed=(await self.get_embed()))

    async def get_embed(self):
        start = self.page * self.per_page
        end = start + self.per_page
        page_goals = self.goals[start:end]
        member_count = len(self.goals)

        embed = discord.Embed(title="🎯 Weekly Goal Progress")

        for r in page_goals:
            user_id = r["user_id"]
            user = self.bot.get_user(user_id)

            user_pokemon_caught = r.get("pokemon_caught", 0)
            user_fish_caught = r.get("fish_caught", 0)
            user_battles_won = r.get("battles_won", 0)

            field_value = (
                f"\n"
                f"> - Pokémon Caught: **{user_pokemon_caught}**\n"
                f"> - Fish Caught: **{user_fish_caught}**\n"
                f"> - Battles Won: **{user_battles_won}**\n"
            )
            if user_id == self.user.id:
                embed.add_field(
                    name="\u200b", value=f"⭐{user.mention}{field_value}", inline=False
                )
            else:
                embed.add_field(name="\u200b", value=f"{user.mention}{field_value}", inline=False)

        footer_text = f"Page {self.page + 1}/{self.max_page + 1} • Members: {member_count} • Weekly Goals reset every Sunday at midnight EST"
        design_embed(user=self.user, embed=embed)
        embed.set_footer(text=footer_text)

        return embed

    async def on_timeout(self):
        for child in self.children:
            if isinstance(child, Button):
                child.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception as e:
                pretty_log("error", f"Failed to disable paginator buttons: {e}")


# 🍰──────────────────────────────
#   🎀 Cog: WeeklyGoalView
# 🍰─────────────────────────────
class WeeklyGoalView(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="goal-view",
        description="View your goal progress",
    )
    async def weekly_goal_view(self, interaction: discord.Interaction):
        from utils.cache.weekly_goal_tracker_cache import (
            fetch_all_weekly_goal_cache,
            weekly_goal_cache,
        )

        handler = await pretty_defer(
            interaction=interaction, content="Fetching weekly goals...", ephemeral=False
        )
        user_id = interaction.user.id
        guild = interaction.guild

        staff_role = guild.get_role(STRAYMONS__ROLES.clan_staff)

        # Non-staff: only their own stats
        if staff_role not in interaction.user.roles:
            member_stats = weekly_goal_cache.get(user_id, {})
            member_pokemon_caught = member_stats.get("pokemon_caught", 0)
            member_fish_caught = member_stats.get("fish_caught", 0)
            member_battles_won = member_stats.get("battles_won", 0)

            desc = (
                f"> - Pokémon Caught: **{member_pokemon_caught}**\n"
                f"> - Fish Caught: **{member_fish_caught}**\n"
                f"> - Battles Won: **{member_battles_won}**\n\n"
            )
            embed = discord.Embed(
                title="🎯 Your Weekly Goal Progress",
                description=desc,
            )
            footer_text = "Weekly Goals reset every Sunday at midnight EST"

            embed =  design_embed(
                embed=embed, user=interaction.user, footer_text=footer_text
            )

            await handler.success(embed=embed, content="")
            return

        # Staff: show all goals
        goals = fetch_all_weekly_goal_cache()
        if not goals:
            await handler.error("No weekly goals found.")
            return

        # Ensure requesting user's stats are first
        goals.sort(key=lambda g: g["user_id"] != interaction.user.id)

        # Wrap paginator in try/except
        try:
            paginator = WeeklyGoalPaginator(self.bot, interaction.user, goals)
            embed = await paginator.get_embed()
            sent = await handler.success(embed=embed, view=paginator, content="")
            paginator.message = sent
        except Exception as e:
            pretty_log("error", f"Failed to load paginator: {e}")
            # fallback: show all goals in a single embed
            embed = discord.Embed(title="🎯 Weekly Goal Progress")
            for r in goals[:25]:  # first 25 as fallback
                user = self.bot.get_user(r["user_id"])
                field_value = (
                    f"{user.mention}\n"
                    f"> - Pokémon Caught: **{r.get('pokemon_caught', 0)}**\n"
                    f"> - Fish Caught: **{r.get('fish_caught', 0)}**\n"
                    f"> - Battles Won: **{r.get('battles_won', 0)}**\n"
                )
                embed.add_field(name="\u200b", value=field_value, inline=False)

            footer_text = f"Showing first 25 entries • Weekly Goals reset every Sunday at midnight EST"
            embed.set_footer(text=footer_text)
            await handler.success(
                embed= design_embed(user=interaction.user, embed=embed), content=""
            )


# -------------------- Setup --------------------
async def setup(bot: commands.Bot):
    await bot.add_cog(WeeklyGoalView(bot))
