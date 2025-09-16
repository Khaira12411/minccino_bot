import discord
from config.aesthetic import Emojis
from utils.loggers.pretty_logs import pretty_log  # Minccino-style logging


async def pretty_defer(
    interaction: discord.Interaction,
    content: str = "Please wait while Minccino thinks...",
    embed: discord.Embed | None = None,
    ephemeral: bool = True,
):
    """
    Minccino-style loader for interactions.
    Always tries to edit the original response first.
    Returns a handle with edit / stop / success / error methods.
    """

    class PrettyDeferHandle:
        def __init__(self, interaction: discord.Interaction, message: discord.Message):
            self.interaction = interaction
            self.message = message
            self.stopped = False

        async def _resolve_message(self) -> discord.Message | None:
            if self.message:
                return self.message
            try:
                self.message = await self.interaction.original_response()
                return self.message
            except Exception:
                return None

        async def edit(
            self,
            content: str | None = None,
            embed: discord.Embed | None = None,
            view: discord.ui.View | None = None,
        ):
            if self.stopped:
                return
            msg = await self._resolve_message()
            try:
                if msg:
                    await msg.edit(
                        content=(
                            f"{Emojis.heart_loading} {content}" if content else None
                        ),
                        embed=embed,
                        view=view,
                    )
                    pretty_log("cmd", f"Loader edited → {content or 'embed/view'}")
                else:
                    self.message = await self.interaction.followup.send(
                        content=(
                            f"{Emojis.heart_loading} {content}" if content else None
                        ),
                        embed=embed,
                        view=view,
                        ephemeral=ephemeral,
                    )
            except Exception as e:
                pretty_log("error", f"[pretty_defer.edit] {e}")

        async def stop(
            self,
            content: str | None = None,
            embed: discord.Embed | None = None,
            view: discord.ui.View | None = None,
            delete: bool = False,
        ):
            if self.stopped:
                return
            self.stopped = True
            msg = await self._resolve_message()
            try:
                if msg and (content or embed or view):
                    await msg.edit(content=content, embed=embed, view=view)
                    pretty_log("cmd", f"Loader stopped → {content or 'embed/view'}")
                if delete and msg:
                    await msg.delete()
                    pretty_log("cmd", "Loader message deleted")
            except discord.NotFound:
                pretty_log("warn", "Loader message not found when stopping")
            except Exception as e:
                pretty_log("error", f"[pretty_defer.stop] {e}")

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
            final_ephemeral = ephemeral if ephemeral is not None else True
            content_with_emoji = (
                f"{Emojis.gray_check_animated} {content}" if content else None
            )

            try:
                if delete and msg:
                    await msg.delete()
                    return
                if msg:
                    try:
                        await msg.edit(
                            content=content_with_emoji, embed=embed, view=view
                        )
                        return
                    except Exception:
                        pass  # fallback
                if final_ephemeral and not override_public:
                    await self.interaction.followup.send(
                        content=content_with_emoji,
                        embed=embed,
                        view=view,
                        ephemeral=True,
                    )
                else:
                    if override_public and msg:
                        try:
                            await msg.delete()
                        except Exception:
                            pass
                    if getattr(self.interaction, "channel", None):
                        await self.interaction.channel.send(
                            content=content_with_emoji,
                            embed=embed,
                            view=view,
                        )
            except Exception as e:
                pretty_log("error", f"[pretty_defer.success] {e}")

        async def error(
            self,
            content: str = "An error occurred.",
            embed: discord.Embed | None = None,
        ):
            if self.stopped:
                return
            self.stopped = True
            content_with_emoji = f"{Emojis.error} {content}"
            msg = await self._resolve_message()
            try:
                if msg:
                    await msg.edit(content=content_with_emoji, embed=embed)
                else:
                    await self.interaction.followup.send(
                        content=content_with_emoji, embed=embed, ephemeral=True
                    )
            except Exception as e:
                pretty_log("error", f"[pretty_defer.error] {e}")

    # ----------------- Send initial loader -----------------
    msg_content = f"{Emojis.heart_loading} {content}"
    try:
        if not interaction.response.is_done():
            await interaction.response.send_message(
                content=msg_content, embed=embed, ephemeral=ephemeral
            )
            msg = await interaction.original_response()
        else:
            msg = await interaction.followup.send(
                content=msg_content, embed=embed, ephemeral=ephemeral
            )
        pretty_log("cmd", f"Loader started for {interaction.user}")
    except Exception as e:
        pretty_log("error", f"Failed to start loader: {e}")
        raise

    return PrettyDeferHandle(interaction, msg)


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
        if not interaction.response.is_done():
            await interaction.response.send_message(
                content=content_with_emoji, embed=embed, ephemeral=True
            )
        else:
            await interaction.followup.send(
                content=content_with_emoji, embed=embed, ephemeral=True
            )
    except Exception as e:
        pretty_log("error", f"[pretty_error] Failed to send error: {e}")
