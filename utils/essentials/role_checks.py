import discord
from discord import app_commands
from config.current_setup import STAFF_SERVER_GUILD_ID, KHY_USER_ID
from config.straymons_constants import STRAYMONS__ROLES


# 🌸──────────────────────────────────────────────────────
# ✨ Custom Exceptions (Sparkles & Cute!) ✨
# ───────────────────────────────────────────────────────
class ClanStaffCheckFailure(app_commands.CheckFailure):
    pass


class KhyCheckFailure(app_commands.CheckFailure):
    pass


class VIPCheckFailure(app_commands.CheckFailure):
    pass


class ClanMemberCheckFailure(app_commands.CheckFailure):
    pass


class OwnerCheckFailure(app_commands.CheckFailure):
    pass


class OwnerCoownerCheckFailure(app_commands.CheckFailure):
    pass


# 🌸──────────────────────────────────────────────────────
# 🐾💫 Cute Error Messages by Server — Cottagecore Style 💫🌿
# ───────────────────────────────────────────────────────
ERROR_MESSAGES = {
    "straymons": {
        "clan_staff": "❌ You don’t have the 🐾 Clan Staff role! ✨",
        "vip": "✨ You need the VIP role to sparkle here! 💖",
        "clan_member": "🐾 Only Straymon Members can use this command. 🌸",
        "owner": "👑 This command is just for the Clan Owner, sorry! 💜",
        "owner_and_co_owner": "👑 & 🤝 Only Clan Owner and Co-Owner can use this. 🌷",
        "espeon_roles": f"🧀 Access restricted: Only members holding <@&{STRAYMONS__ROLES.ethereal_eclair}>, <@&{STRAYMONS__ROLES.sunrise_scone}>, or <@&{STRAYMONS__ROLES.vip}> are permitted to use this command. ✨",
        "khy_only": "Only Khy can use this ~",
    },
}


# 🌸──────────────────────────────────────────────────────
# 🔹 Helper function
# ───────────────────────────────────────────────────────
def has_role(user_roles, role_id):
    return role_id in [role.id for role in user_roles]


# 🌸──────────────────────────────────────────────────────
# 🔹 Slash command decorators
# ───────────────────────────────────────────────────────
def khy_only():
    async def predicate(interaction: discord.Interaction):
        if interaction.user.id != KHY_USER_ID:
            raise KhyCheckFailure(ERROR_MESSAGES["straymons"]["khy_only"])
        return True

    return app_commands.check(predicate)


def clan_staff_only():
    async def predicate(interaction: discord.Interaction):
        if not has_role(interaction.user.roles, STRAYMONS__ROLES.clan_staff):
            raise ClanStaffCheckFailure(ERROR_MESSAGES["straymons"]["clan_staff"])
        return True

    return app_commands.check(predicate)


def vip_only():
    async def predicate(interaction: discord.Interaction):
        if not has_role(interaction.user.roles, STRAYMONS__ROLES.vip):
            raise VIPCheckFailure(ERROR_MESSAGES["straymons"]["vip"])
        return True

    return app_commands.check(predicate)


def clan_member_only():
    async def predicate(interaction: discord.Interaction):
        if not has_role(interaction.user.roles, STRAYMONS__ROLES.straymon):
            raise ClanMemberCheckFailure(ERROR_MESSAGES["straymons"]["clan_member"])
        return True

    return app_commands.check(predicate)


def owner_only():
    async def predicate(interaction: discord.Interaction):
        if not has_role(interaction.user.roles, STRAYMONS__ROLES.clan_owner):
            raise OwnerCheckFailure(ERROR_MESSAGES["straymons"]["owner"])
        return True

    return app_commands.check(predicate)


def owner_and_co_owner_only():
    async def predicate(interaction: discord.Interaction):
        user_roles = [role.id for role in interaction.user.roles]
        if (
            STRAYMONS__ROLES.clan_owner not in user_roles
            and STRAYMONS__ROLES.clan_co_owner not in user_roles
        ):
            raise OwnerCoownerCheckFailure(
                ERROR_MESSAGES["straymons"]["owner_and_co_owner"]
            )
        return True

    return app_commands.check(predicate)


def espeon_roles_only():
    async def predicate(interaction: discord.Interaction):
        user_roles = [role.id for role in interaction.user.roles]

        # ✅ Bypass for Clan Staff, VIP roles, or staff guild members
        if (
            STRAYMONS__ROLES.clan_staff in user_roles
            or STRAYMONS__ROLES.vip in user_roles
            or interaction.guild.id == STAFF_SERVER_GUILD_ID
        ):
            return True

        # 🔒 Require Espeon roles
        if (
            STRAYMONS__ROLES.sunrise_scone not in user_roles
            and STRAYMONS__ROLES.ethereal_eclair not in user_roles
        ):
            raise OwnerCoownerCheckFailure(ERROR_MESSAGES["straymons"]["espeon_roles"])
        return True

    return app_commands.check(predicate)
