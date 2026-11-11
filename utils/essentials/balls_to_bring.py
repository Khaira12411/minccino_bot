import discord

from utils.essentials.ball_names import BALL_EMOJIS, normalize_ball_type

COMMAND_LABELS = {";p": ";p", ";fish": ";f"}
_POKEMON_BALL_ORDER = [
    "pokeball", "greatball", "ultraball", "premierball", "masterball",
    "ancientball", "beastball", "luxuryball", "netball", "duskball",
    "moonball", "friendball", "loveball", "fastball", "heavyball", "quickball",
]
_FISH_BALL_ORDER = [
    "pokeball", "greatball", "ultraball", "premierball", "diveball",
    "masterball", "ancientball", "beastball", "luxuryball", "netball",
    "lureball", "duskball", "moonball", "friendball", "loveball",
    "fastball", "heavyball", "quickball",
]
_BALL_ORDERS = {
    label: {ball: index for index, ball in enumerate(order)}
    for label, order in ((";p", _POKEMON_BALL_ORDER), (";f", _FISH_BALL_ORDER))
}


def _sort_key(label: str, ball: str) -> tuple[int, str]:
    order = _BALL_ORDERS[label]
    return order.get(ball, len(order)), ball


def format_balls_to_bring(catch_list_mons: list[dict]) -> dict[str, str]:
    """Map ';p' / ';f' to the unique balls needed, shown as emojis in ball order."""
    balls_by_command: dict[str, set[str]] = {label: set() for label in COMMAND_LABELS.values()}
    for mon in catch_list_mons:
        if mon.get("completion"):
            continue
        label = COMMAND_LABELS.get(mon["catch_type"])
        if label is not None:
            balls_by_command[label].add(normalize_ball_type(mon["ball_type"]))

    return {
        label: " ".join(BALL_EMOJIS.get(ball) or ball for ball in sorted(balls, key=lambda b: _sort_key(label, b)))
        for label, balls in balls_by_command.items()
        if balls
    }


def build_balls_to_bring_embed(catch_list_mons: list[dict]) -> discord.Embed | None:
    balls_by_command = format_balls_to_bring(catch_list_mons)
    if not balls_by_command:
        return None
    embed = discord.Embed(title="Balls to Bring", color=discord.Color.green())
    for label, balls in balls_by_command.items():
        embed.add_field(name=label, value=balls[:1024], inline=False)
    return embed
