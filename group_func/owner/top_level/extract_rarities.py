import re
import discord
from discord import app_commands
from discord.ext import commands

RARITY_FILE = "rarities.py"


async def extract_rarities_func(
    bot: commands.Bot, interaction: discord.Interaction, message_link: str
):
    await interaction.response.defer(thinking=True)

    # --- Parse message link ---
    try:
        parts = message_link.strip().split("/")
        guild_id, channel_id, message_id = (
            int(parts[-3]),
            int(parts[-2]),
            int(parts[-1]),
        )
    except Exception:
        await interaction.followup.send("❌ Invalid message link format.")
        return

    # --- Fetch the message ---
    try:
        channel = bot.get_channel(channel_id) or await bot.fetch_channel(channel_id)
        if not channel:
            await interaction.followup.send("❌ Could not fetch the channel.")
            return
        message = await channel.fetch_message(message_id)
    except Exception:
        await interaction.followup.send("❌ Could not fetch the message.")
        return

    # --- Ensure message has an embed ---
    if not message.embeds:
        await interaction.followup.send("❌ That message has no embeds to parse.")
        return

    embed = message.embeds[0]

    # --- Detect rarity from embed author name ---
    header_text = embed.author.name if embed.author and embed.author.name else ""
    header_match = re.search(
        r"List of (.+?) Pokemon Ingame", header_text, re.IGNORECASE
    )
    if not header_match:
        await interaction.followup.send(
            "❌ Could not detect rarity in the embed author name."
        )
        return

    rarity = header_match.group(1).strip().upper().replace(" ", "_")
    dict_name = f"{rarity}_RARITY"

    # --- Extract dex + pokemon names from embed description ---
    raw_text = embed.description or ""
    entries = re.findall(r"`(\d+)`\s+<:.*?:\d+>\s+([A-Za-z]+)", raw_text)

    if not entries:
        await interaction.followup.send("❌ No Pokemon found in the embed description.")
        return

    # --- Build a properly formatted dictionary ---
    rarity_dict = {name.lower(): {"dex": int(dex)} for dex, name in entries}

    # --- Load old file contents ---
    try:
        with open(RARITY_FILE, "r", encoding="utf-8") as f:
            old_content = f.read()
    except FileNotFoundError:
        old_content = ""

    # --- Replace or append dict ---
    pattern = re.compile(rf"^{dict_name}\s*=\s*{{.*?}}", re.DOTALL | re.MULTILINE)
    new_dict_str = f"{dict_name} = {rarity_dict}"

    if pattern.search(old_content):
        updated_content = pattern.sub(new_dict_str, old_content)
    else:
        updated_content = old_content + ("\n\n" if old_content else "") + new_dict_str

    # --- Save updated file ---
    with open(RARITY_FILE, "w", encoding="utf-8") as f:
        f.write(updated_content)

    await interaction.followup.send(
        f"✅ Updated `{dict_name}` with {len(rarity_dict)} Pokemon from the embed."
    )
