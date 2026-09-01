"""Permission-checked moderation helpers. AI never executes these implicitly."""
from datetime import timedelta
import discord
from database import add_warning

async def warn_member(guild, moderator, member, reason):
    if not moderator.guild_permissions.moderate_members:
        return False, "You need Moderate Members permission."
    count = add_warning(guild.id, member.id, moderator.id, reason)
    try:
        await member.send(f"⚠️ You received a warning in **{guild.name}**.\nReason: {reason}\nTotal warnings: {count}")
    except (discord.Forbidden, discord.HTTPException):
        pass
    return True, f"Warning #{count} issued to {member.mention}."

async def timeout_member(moderator, member, minutes, reason):
    if not moderator.guild_permissions.moderate_members:
        return False, "You need Moderate Members permission."
    if not 1 <= minutes <= 40320:
        return False, "Timeout must be between 1 minute and 28 days."
    await member.timeout(discord.utils.utcnow() + timedelta(minutes=minutes), reason=reason)
    return True, f"{member.mention} timed out for {minutes} minutes."
