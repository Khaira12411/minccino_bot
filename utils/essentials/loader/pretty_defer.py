import discord
from config.aesthetic import *
from utils.loggers.pretty_logs import pretty_log  # <- now Minccino style


async def pretty_defer(
    interaction: discord.Interaction,
    view: discord.ui.View | None = None,
    content: str = "Please wait while Minccino thinks...",
    embed: discord.Embed | None = None,
    ephemeral: bool = True,
):
    """
    Fully safe Minccino loader for interactions.
    - Don't forget to await
    - Always prefers editing the original response.
    - Sends a public fallback message if editing is not possible.
    - Success can override ephemeral by deleting it and sending a public message.
    """
    class PrettyDeferHandle:
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
            self._emoji_added = False
            self.ephemeral = ephemeral
            self.error_emoji = "❌"

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
                            f"{Emojis.heart_loading} {content}"
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
                        tag="error",
                        message=f"[pretty_defer.edit] followup failed: {e}",
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
                pretty_log(tag="error", message=f"[pretty_defer.edit] {e}")

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
                    pretty_log(tag="error", message=f"[pretty_defer.stop] {e}")

        async def success(
            self,
            content: str | None = "Done!",
            embed: discord.Embed | None = None,
            view: discord.ui.View | None = None,
            ephemeral: bool | None = None,
            override_public: bool = False,
            delete: bool = False,
        ):
            if self.stopped:
                return
            self.stopped = True
            msg = await self._resolve_message()

            if delete and msg:
                try:
                    await msg.delete()
                except Exception as e:
                    pretty_log(
                        tag="error",
                        message=f"[pretty_defer.success] delete failed: {e}",
                    )
                return

            final_ephemeral = ephemeral if ephemeral is not None else self.ephemeral
            base_content = content or ""
            content_with_emoji = (
                f"{Emojis.gray_check_animated} {base_content}" if base_content else ""
            )

            try:
                if final_ephemeral and not override_public:
                    if msg:
                        try:
                            await msg.edit(
                                content=content_with_emoji, embed=embed, view=view
                            )
                            return
                        except Exception:
                            pass
                    await self.interaction.followup.send(
                        content=content_with_emoji,
                        embed=embed,
                        view=view,
                        ephemeral=True,
                    )
                else:
                    if override_public and self.ephemeral:
                        if msg:
                            try:
                                await msg.delete()
                            except Exception:
                                pass
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
                pretty_log(tag="error", message=f"[pretty_defer.success] {e}")

        async def error(
            self,
            content: str = "An error occurred.",
            embed: discord.Embed | None = None,
        ):
            if self.stopped:
                return
            self.stopped = True
            msg = await self._resolve_message()
            content_with_emoji = f"{Emojis.error} {content}"

            try:
                if msg:
                    if self.ephemeral:
                        await msg.edit(content=content_with_emoji, embed=embed)
                    else:
                        await self.interaction.followup.send(
                            content=content_with_emoji, embed=embed, ephemeral=True
                        )
                        try:
                            await msg.delete()
                        except Exception:
                            pass
                else:
                    await self.interaction.followup.send(
                        content=content_with_emoji, embed=embed, ephemeral=True
                    )
            except Exception as e:
                pretty_log(tag="error", message=f"[pretty_defer.error] {e}")
            return

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

    handle = PrettyDeferHandle(interaction, msg, ephemeral=ephemeral)
    if view:
        setattr(view, "defer_handle", handle)

    return handle


# ╭───────────────────────────────╮
#   🌊 Pretty Error Helper
# ╰───────────────────────────────╯
async def pretty_error(
    interaction: discord.Interaction,
    content: str = "An error occurred.",
    embed: discord.Embed | None = None,
):
    """Standalone ephemeral error sender for Minccino."""
    content_with_emoji = f"{Emojis.error} {content}"

    try:
        if (
            getattr(interaction, "response", None)
            and not interaction.response.is_done()
        ):
            await interaction.response.send_message(
                content=content_with_emoji,
                embed=embed,
                ephemeral=True,
            )
        else:
            await interaction.followup.send(
                content=content_with_emoji,
                embed=embed,
                ephemeral=True,
            )
    except Exception as e:
        pretty_log(tag="error", message=f"[pretty_error] Failed to send error: {e}")
