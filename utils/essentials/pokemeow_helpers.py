# ─────────────────────────────
# 🔹 Helper: Check if message is a PokéMeow reply
# ─────────────────────────────
import discord

def is_pokemeow_reply(message: discord.Message) -> discord.Member | bool:
    """
    Check if a message is from PokéMeow and is a reply to a user.

    Parameters
    ----------
    message : discord.Message
        The message to check.

    Returns
    -------
    discord.Member | bool
        Returns the member the message is replying to if valid, else False.
    """
    author_str = str(message.author).lower()
    if "pokémeow" not in author_str and "pokemeow" not in author_str:
        return False

    if not getattr(message, "reference", None):
        return False

    replied_msg = getattr(message.reference, "resolved", None)
    if not isinstance(replied_msg, discord.Message):
        return False

    return (
        replied_msg.author if isinstance(replied_msg.author, discord.Member) else False
    )
