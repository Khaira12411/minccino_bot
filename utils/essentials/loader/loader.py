import asyncio
from typing import Any, Callable, Coroutine, List

import discord

from config.aesthetic import Emojis
from utils.loggers.pretty_logs import pretty_log


async def pretty_defer(
    interaction: discord.Interaction,
    content: str = "Please wait while Minccino thinks...",
    embed: discord.Embed | None = None,
    ephemeral: bool = True,
):
    """
    Defer an interaction with a loading message.
    Returns a handle for safely editing or stopping the message later.
    """

    class PrettyDeferHandle:
        def __init__(self, interaction: discord.Interaction, message: discord.Message):
            self.interaction = interaction
            self.message = message

        async def edit(
            self, content: str | None = None, embed: discord.Embed | None = None
        ):
            """Edit the loader safely."""
            if not self.message:
                return
            try:
                kwargs = {}
                if content is not None:
                    kwargs["content"] = f"{Emojis.heart_loading} {content}"
                if embed is not None:
                    kwargs["embed"] = embed
                if kwargs:
                    await self.message.edit(**kwargs)
            except discord.NotFound:
                await self.interaction.followup.send(
                    content=content, embed=embed, ephemeral=ephemeral
                )

        async def stop(
            self,
            content: str | None = None,
            embed: discord.Embed | None = None,
            delete: bool = False,
        ):
            """Stop the loader: optionally edit final message or delete."""
            if not self.message:
                return
            try:
                if content or embed:
                    await self.message.edit(content=content, embed=embed)
                if delete:
                    await self.message.delete()
            except discord.NotFound:
                pass

    # 💜 Send initial loader
    msg_content = f"{Emojis.heart_loading} {content}"
    if not interaction.response.is_done():
        await interaction.response.send_message(
            content=msg_content, embed=embed, ephemeral=ephemeral
        )
        msg = await interaction.original_response()
    else:
        msg = await interaction.followup.send(
            content=msg_content, embed=embed, ephemeral=ephemeral
        )

    return PrettyDeferHandle(interaction, msg)


async def minccino_defer(
    interaction: discord.Interaction,
    view: discord.ui.View | None = None,
    content: str = "Minccino is tidying up your request...",
    embed: discord.Embed | None = None,
    ephemeral: bool = True,
):
    """
    Fully safe Minccino loader for interactions.
    - Works like pretty_defer but with Minccino-style flavor.
    - Always prefers editing the original response.
    - Sends a public fallback if editing fails.
    """

    class MinccinoDeferHandle:
        def __init__(
            self,
            interaction: discord.Interaction,
            message: discord.Message | None,
            ephemeral: bool,
        ):
            self.interaction = interaction
            self.message = message
            self.message_id = message.id if message else None
            self.stopped = False
            self.ephemeral = ephemeral

        async def _resolve_message(self) -> discord.Message | None:
            if self.message:
                return self.message
            try:
                self.message = await self.interaction.original_response()
                return self.message
            except Exception:
                return None

        async def edit(
            self, content=None, embed=None, view=None, with_emoji: bool = True
        ):
            if self.stopped:
                return
            msg = await self._resolve_message()
            if not msg:
                try:
                    msg = await self.interaction.followup.send(
                        content=(
                            f"{Emojis.Minccino_Loading} {content}"
                            if content and with_emoji
                            else content
                        ),
                        embed=embed,
                        view=view,
                        ephemeral=self.ephemeral,
                    )
                    self.message = msg
                    self.message_id = msg.id
                    return
                except Exception as e:
                    pretty_log(
                        "❌ MINCCINO_ERROR",
                        f"[minccino_defer.edit] followup failed: {e}",
                    )
                    return

            if content and with_emoji:
                content = f"{Emojis.heart_loading} {content}"

            kwargs = {
                k: v
                for k, v in {"content": content, "embed": embed, "view": view}.items()
                if v is not None
            }
            try:
                await msg.edit(**kwargs)
            except Exception as e:
                pretty_log(
                    "❌ MINCCINO_ERROR",
                    f"[minccino_defer.edit] {e}",
                )

        async def stop(self, content=None, embed=None, view=None):
            if self.stopped:
                return
            self.stopped = True
            msg = await self._resolve_message()
            if not msg:
                return
            kwargs = {
                k: v
                for k, v in {"content": content, "embed": embed, "view": view}.items()
                if v is not None
            }
            if kwargs:
                try:
                    await msg.edit(**kwargs)
                except Exception as e:
                    pretty_log(
                        "❌ MINCCINO_ERROR",
                        f"[minccino_defer.stop] {e}",
                    )

        async def success(
            self,
            content: str | None = "All done! 🐾",
            embed: discord.Embed | None = None,
            view: discord.ui.View | None = None,
            ephemeral: bool | None = None,
            override_public: bool = False,
        ):
            if self.stopped:
                return
            self.stopped = True

            final_ephemeral = ephemeral if ephemeral is not None else self.ephemeral
            base_content = content or ""
            content_with_emoji = (
                f"{Emojis.gray_check_animated} {base_content}" if base_content else ""
            )

            msg = await self._resolve_message()

            try:
                if final_ephemeral and (override_public or self.ephemeral):
                    if msg:
                        try:
                            await msg.delete()
                        except Exception:
                            pass
                    if getattr(self.interaction, "channel", None):
                        await self.interaction.channel.send(
                            content=content_with_emoji, embed=embed, view=view
                        )
                else:
                    if msg:
                        try:
                            await msg.edit(
                                content=content_with_emoji, embed=embed, view=view
                            )
                            return
                        except Exception:
                            pass
                    if getattr(self.interaction, "channel", None):
                        await self.interaction.channel.send(
                            content=content_with_emoji, embed=embed, view=view
                        )
            except Exception as e:
                pretty_log(
                    "❌ MINCCINO_ERROR",
                    f"[minccino_defer.success] {e}",
                )

    # ----------------- Send initial loader -----------------
    msg: discord.Message | None = None
    msg_content = f"{Emojis.heart_loading} {content}"

    try:
        if (
            getattr(interaction, "response", None)
            and not interaction.response.is_done()
        ):
            await interaction.response.send_message(
                content=msg_content, embed=embed, view=view, ephemeral=ephemeral
            )
            try:
                msg = await interaction.original_response()
            except Exception:
                pass
        else:
            msg = await interaction.followup.send(
                content=msg_content, embed=embed, view=view, ephemeral=ephemeral
            )
    except Exception:
        pass

    handle = MinccinoDeferHandle(interaction, msg, ephemeral=ephemeral)
    if view:
        setattr(view, "defer_handle", handle)

    return handle


class LoadingMessage:
    """Dynamic loading message for Discord interactions."""

    def __init__(
        self, interaction: discord.Interaction, initial_message: str = "Please wait..."
    ):
        self.interaction = interaction
        self.message: discord.Message | None = None
        self.initial_message = f"{Emojis.heart_loading} {initial_message}"

    async def start(self):
        if not self.interaction.response.is_done():
            await self.interaction.response.send_message(
                self.initial_message, ephemeral=True
            )
            self.message = await self.interaction.original_response()
        else:
            self.message = await self.interaction.followup.send(
                self.initial_message, ephemeral=True
            )
        return self

    async def update(self, new_message: str):
        if self.message:
            try:
                await self.message.edit(content=f"{Emojis.heart_loading} {new_message}")
            except discord.NotFound:
                pass

    async def stop(self, delete: bool = True, final_message: str | None = None):
        if self.message:
            try:
                if final_message:
                    await self.message.edit(content=f"{final_message}")
                if delete:
                    await asyncio.sleep(0.5)
                    await self.message.delete()
            except discord.NotFound:
                pass


async def with_loader(
    interaction: discord.Interaction,
    steps: List[str],
    process_func: Callable[..., Coroutine[Any, Any, Any]],
    *args,
    final_message: str = "✅ Done!",
    keep_final: bool = True,  # <--- NEW
    step_delay: float = 0.2,
    **kwargs,
):
    """
    Simplified loader runner:
    - `steps`: list of messages to show sequentially before running the process
    - `process_func`: async function to run while loader is showing
    - `*args, **kwargs`: passed to process_func
    - `keep_final`: if True, final_message will stay, else it will be deleted
    """
    loader = await LoadingMessage(
        interaction, steps[0] if steps else "Please wait..."
    ).start()

    # Update through steps
    for msg in steps[1:]:
        await asyncio.sleep(step_delay)
        await loader.update(msg)

    # Run the actual process
    result = await process_func(*args, **kwargs)

    # Stop loader
    await loader.stop(delete=not keep_final, final_message=final_message)
    return result
