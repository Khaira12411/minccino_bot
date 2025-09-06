import re
from pathlib import Path
from typing import Optional

import aiohttp
import discord

from config.aesthetic import Emojis
from utils.loggers.pretty_logs import pretty_log


# 💠────────────────────────────────────────────
# [🟣 HELPER] Fetch message from link • do all the thinking + respond
# ─────────────────────────────────────────────
async def fetch_message_from_link_func(
    bot: discord.Client,
    interaction: discord.Interaction,
    message_link: str,
    ephemeral: bool = True,
) -> None:
    """
    End-to-end:
      - shows loader (uses pretty_defer if available, else normal defer)
      - validates link, fetches via API
      - formats readable dump (text, embeds, attachments)
      - sends inline if short, otherwise as .txt file (or if save_to_file=True)
      - cleans up any temp file
    """
    save_to_file = True
    loader = None
    temp_file: Optional[Path] = None

    # [💙 READY] Start loader
    try:
        try:
            # If you keep pretty_defer in another path, adjust import
            from utils.essentials.loader import pretty_defer  # optional
        except Exception:
            pretty_defer = None

        if pretty_defer:
            loader = await pretty_defer(
                interaction,
                content="Fetching message…",
                ephemeral=ephemeral,
            )
        else:
            if not interaction.response.is_done():
                await interaction.response.defer(thinking=True, ephemeral=ephemeral)
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"[fetch_message] Loader setup failed: {e}",
        )

    # [💙 READY] Helper to send a final text
    async def send_text(text: str):
        as_block = f"```{text}```" if len(text) <= 1900 else text
        if loader:
            try:
                # If too long for a code block, just send as followup.
                if len(as_block) <= 2000:
                    await loader.stop(content=as_block)
                else:
                    await interaction.followup.send(
                        content="📄 Output is large — sending as file…",
                        ephemeral=ephemeral,
                    )
            except Exception as e:
                pretty_log(
                    "❌ ERROR",
                    f"[fetch_message] Loader stop (text) failed: {e}",
                )
                await interaction.followup.send(as_block[:1990], ephemeral=ephemeral)
        else:
            await interaction.followup.send(as_block[:2000], ephemeral=ephemeral)

    # [💙 READY] Helper to send a file then close loader
    async def send_file(path: Path, notice: str = "📄 Message contents saved to file:"):
        try:
            await interaction.followup.send(
                content=notice, file=discord.File(path), ephemeral=ephemeral
            )
        finally:
            # Best-effort file cleanup
            try:
                path.unlink(missing_ok=True)
            except Exception as e:
                pretty_log(
                    "❌ ERROR",
                    f"[fetch_message] Temp file cleanup failed: {e}",
                )
            if loader:
                try:
                    await loader.stop(delete=True)
                except Exception:
                    pass

    # [💙 READY] Parse link → channel_id + message_id
    try:
        channel_id = message_id = None

        # Standard message link: /channels/{guild}/{channel}/{message}
        m = re.search(r"/channels/(\d+)/(\d+)/(\d+)$", message_link)
        if m:
            channel_id, message_id = m.group(2), m.group(3)
        else:
            # API link: /api/vX/channels/{channel}/messages/{message}
            m2 = re.search(r"/channels/(\d+)/messages/(\d+)$", message_link)
            if m2:
                channel_id, message_id = m2.group(1), m2.group(2)

        if not channel_id or not message_id:
            await send_text(
                "❌ Invalid message link. Expected:\n- https://discord.com/channels/<guild>/<channel>/<message>\n- https://discord.com/api/v10/channels/<channel>/messages/<message>"
            )
            return
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"[fetch_message] Link parse failed: {e}",
        )
        await send_text("❌ Could not parse the message link.")
        return

    # [💙 READY] Fetch via REST
    try:
        url = f"https://discord.com/api/v10/channels/{channel_id}/messages/{message_id}"
        headers = {"Authorization": f"Bot {bot.http.token}"}

        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as resp:
                if resp.status != 200:
                    await send_text(f"❌ Failed to fetch message: HTTP {resp.status}")
                    return
                data = await resp.json()
    except Exception as e:
        pretty_log(
            tag="error",
            message=f"[fetch_message] HTTP fetch failed: {e}",
        )
        await send_text("❌ Network error while fetching the message.")
        return

    # [💙 READY] Build readable dump
    try:
        parts = []
        parts.append("━━━━━━━━━━━━━━━━━━━━━━━")
        author_tag = (
            f"{data['author']['username']}#{data['author'].get('discriminator','0')}"
        )
        parts.append(f"👤 Author   : {author_tag}")
        parts.append(f"🆔 MessageID: {data['id']}")
        parts.append(f"💬 ChannelID: {data['channel_id']}")
        parts.append(f"🕒 Created  : {data['timestamp']}")
        parts.append("━━━━━━━━━━━━━━━━━━━━━━━\n")

        content = data.get("content", "")
        if content.strip():
            parts.append("💬 Message Content:")
            parts.append(content)
            parts.append("")
        else:
            parts.append("💬 Message Content: [No text]\n")

        # Replies / references (optional nice touch)
        ref = data.get("referenced_message")
        if ref:
            ref_author = (
                f"{ref['author']['username']}#{ref['author'].get('discriminator','0')}"
            )
            parts.append("↩️ Replying To:")
            parts.append(f"- Author: {ref_author}")
            if ref.get("content"):
                parts.append(f"- Snippet: {ref['content'][:200]}")
            parts.append("")

        # Attachments
        atts = data.get("attachments") or []
        if atts:
            parts.append("📎 Attachments:")
            for att in atts:
                parts.append(f"- {att.get('filename','file')} → {att.get('url','')}")
            parts.append("")

        # Embeds (pretty)
        embeds = data.get("embeds") or []
        if embeds:
            parts.append("🖼 Embeds:")
            for idx, emb in enumerate(embeds, start=1):
                parts.append(f"- Embed {idx}")

                if emb.get("title"):
                    parts.append(f"   • Title: {emb['title']}")

                if emb.get("url"):
                    parts.append(f"   • URL: {emb['url']}")

                if emb.get("author") and emb["author"].get("name"):
                    author_line = emb["author"]["name"]
                    if emb["author"].get("url"):
                        author_line += f" ({emb['author']['url']})"
                    parts.append(f"   • Author: {author_line}")

                if emb.get("description"):
                    parts.append("   • Description:")
                    for line in emb["description"].splitlines():
                        parts.append(f"     {line}")

                if emb.get("fields"):
                    for f in emb["fields"]:
                        name = f.get("name", "Field")
                        val = f.get("value", "")
                        inline = f.get("inline", False)
                        parts.append(f"   • {name} [{'inline' if inline else 'block'}]:")
                        for line in val.splitlines():
                            parts.append(f"     {line}")

                if emb.get("footer") and emb["footer"].get("text"):
                    parts.append("   • Footer:")
                    for line in emb["footer"]["text"].splitlines():
                        parts.append(f"     {line}")

                if emb.get("image") and emb["image"].get("url"):
                    parts.append(f"   • Image: {emb['image']['url']}")

                if emb.get("thumbnail") and emb["thumbnail"].get("url"):
                    parts.append(f"   • Thumbnail: {emb['thumbnail']['url']}")

                parts.append("")


        result_text = "\n".join(parts).strip()
    except Exception as e:
        pretty_log(
            "error",
            f"[fetch_message] Build dump failed: {e}",
        )
        await send_text("❌ Failed to format the message contents.")
        return

    # [💙 READY] Decide: inline vs file, send, cleanup
    try:
        if save_to_file or len(result_text) > 1800:
            temp_file = Path(f"message_{message_id}.txt")
            temp_file.write_text(result_text, encoding="utf-8")
            await send_file(temp_file, "📄 Message dump attached:")
            return
        else:
            await send_text(result_text)
            if loader:
                try:
                    await loader.stop()  # keep the final text visible
                except Exception:
                    pass
            return
    except Exception as e:
        pretty_log(
            tag=" ERROR",
            message=f"[fetch_message] Send failed: {e}",
        )
        await send_text("❌ Failed to send the output.")
        return
