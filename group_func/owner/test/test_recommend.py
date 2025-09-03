# 🍃───────────────────────────────────────
#              Test Recommend Cog
# 🍃───────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands

from config.aesthetic import Emojis_Balls
from utils.cache.ball_reco_cache import ball_reco_cache
from utils.listener_func.ball_reco_ping import recommend_ball
from utils.listener_func.fish_reco_ping import recommend_fishing_ball


async def test_recommend_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
    spawn_type: str,
    pokemon: str,
    rarity: str,
    catch_rate_bonus: int = 0,
    is_patreon: bool = False,
    is_exclusive: bool = False,
    water_state: str = "calm",
):
    spawn_type = spawn_type.lower()
    rarity = rarity.lower()
    water_state = water_state.lower()
    
    user_name = interaction.user.name

    # Map water state string to numeric for the recommender
    water_state_map = {
        "calm": 1,
        "moderate": 2,
        "strong": 3,
        "intense": 4,
        "special": 5,
    }
    numeric_water_state = water_state_map.get(water_state, 1)

    # Build a fake embed
    embed_color = 0xFFFFFF  # default white
    if spawn_type in ["pokemon", "held_item"] and is_exclusive:
        embed_color = 15345163  # Masterball bypass color
    elif spawn_type == "fishing":
        embed_color = 0x87CEFA  # fishing color

    desc = f"**{user_name}** found a wild **{pokemon}**!"
    embed = discord.Embed(description=desc, color=embed_color)

    # ✅ Add footer so recommend_ball can parse rarity
    if spawn_type in ["pokemon", "held_item"]:
        embed.set_footer(text=rarity.capitalize())
    elif spawn_type == "fishing":
        embed.set_footer(text=f"Water State: {numeric_water_state}")

    # Build FakeMessage with reference to interaction user
    class FakeMessage:
        def __init__(self):
            self.id = 0
            self.channel = interaction.channel
            self.embeds = [embed]
            self.reference = type(
                "Ref",
                (),
                {"resolved": type("Orig", (), {"author": interaction.user})()},
            )()
            self.water_state = numeric_water_state

    fake_msg = FakeMessage()

    # Inject user settings into cache
    cache_key = interaction.user.id if spawn_type != "fishing" else user_name
    ball_reco_cache[cache_key] = {
        "user_name": user_name,
        "catch_rate_bonus": catch_rate_bonus,
        "is_patreon": is_patreon,
        "pokemon": {rarity: True},
        "held_items": {rarity: True},
    }

    # Call the correct recommender
    if spawn_type in ["pokemon", "held_item"]:
        await recommend_ball(fake_msg, bot)
    elif spawn_type == "fishing":
        await recommend_fishing_ball(fake_msg, bot)
    else:
        await interaction.response.send_message(
            f"Invalid spawn_type: {spawn_type}", ephemeral=True
        )
        return

    await interaction.response.send_message(
        f"Mock recommendation triggered for {pokemon} ({spawn_type})",
        ephemeral=True,
    )
