import discord
from discord.errors import NotFound
from utils.loggers.pretty_logs import pretty_log


async def safe_respond(
    interaction: discord.Interaction,
    *,
    content: str | None = None,
    embed=None,
    view=None,
    ephemeral: bool = True,
    method: str = "auto",  # "send", "edit", "followup", "auto"
):
    """
    Safely respond to a Discord interaction without causing errors if the
    interaction or its webhook has expired. Falls back to channel.send when possible.
    """
    # ✅ Build kwargs without None values
    kwargs = {}
    if content is not None:
        kwargs["content"] = content
    if embed is not None:
        kwargs["embed"] = embed
    if view is not None:
        kwargs["view"] = view

    try:
        # 🚦 Early exit if interaction is expired
        if interaction.is_expired():
            pretty_log(
                "warn",
                f"[SafeRespond] Interaction expired for user {interaction.user} ({interaction.user.id}) "
                f"in channel {interaction.channel}.",
            )
            if not ephemeral and interaction.channel:
                return await interaction.channel.send(**kwargs)
            return None

        # 🌀 AUTO mode picks safest option
        if method == "auto":
            if not interaction.response.is_done():
                return await interaction.response.send_message(
                    **kwargs, ephemeral=ephemeral
                )
            try:
                return await interaction.edit_original_response(**kwargs)
            except NotFound as e:
                if e.code == 10015:  # Unknown Webhook
                    if not ephemeral and interaction.channel:
                        return await interaction.channel.send(**kwargs)
                    return None
                raise

        # 📨 FORCE send (only works if not already responded)
        elif method == "send":
            return await interaction.response.send_message(
                **kwargs, ephemeral=ephemeral
            )

        # 📝 Edit the deferred/original response or current message
        elif method == "edit":
            if not interaction.response.is_done():
                return await interaction.response.edit_message(**kwargs)
            return await interaction.edit_original_response(**kwargs)

        # 🔁 Followup message
        elif method == "followup":
            return await interaction.followup.send(**kwargs, ephemeral=ephemeral)

    except NotFound as e:
        # Handle Unknown Interaction (10062) or Unknown Webhook (10015)
        if e.code in (10062, 10015):
            # ✅ Change from "warn" to "info" to reduce spam
            pretty_log(
                "info",  # Changed from "warn"
                f"[SafeRespond] Interaction invalid for {interaction.user} ({interaction.user.id}) - connection issues, ignoring",
            )
            if not ephemeral and interaction.channel:
                return await interaction.channel.send(**kwargs)
            return None
        raise
