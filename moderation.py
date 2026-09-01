"""Explicit, permission-checked moderation actions. AI never executes these implicitly."""
import discord
from database import add_warning, warning_count

async def warn_member(interaction: discord.Interaction, member: discord.Member, reason: str):
    if not interaction.user.guild_permissions.moderate_members:
        return False, "You need Moderate Members permission."
    count = add_warning(interaction.guild_id, member.id, interaction.user.id, reason)
    try:
        await member.send(f"You received a warning in {interaction.guild.name}.\nReason: {reason}\nTotal warnings: {count}")
    except discord.HTTPException:
        pass
    return True, f"Warning #{count} issued to {member.mention}."

async def timeout_member(interaction: discord.Interaction, member: discord.Member, minutes: int, reason: str):
    if not interaction.user.guild_permissions.moderate_members:
        return False, "You need Moderate Members permission."
    if minutes < 1 or minutes > 40320:
        return False, "Timeout must be between 1 minute and 28 days."
    await member.timeout(discord.utils.utcnow() + discord.timedelta(minutes=minutes), reason=reason)
    return True, f"{member.mention} timed out for {minutes} minutes."
