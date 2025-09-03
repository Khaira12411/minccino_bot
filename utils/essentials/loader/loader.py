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
