import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from groq_ai import ask_ai
from database import init_db, add_message, history, add_memory, get_memories, forget_memories, upsert_user, add_warning, warning_count

load_dotenv(override=True)
TOKEN = os.getenv("DISCORD_TOKEN", "")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
PREFIX = os.getenv("PREFIX", "!")
if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN is not set")
if not OWNER_ID:
    raise RuntimeError("OWNER_ID is not set")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)


def is_owner(user):
    return user.id == OWNER_ID


async def dm_user(member, text):
    try:
        await member.send(text)
        return True
    except (discord.Forbidden, discord.HTTPException):
        return False


@bot.event
async def on_ready():
    init_db()
    print(f"ArveX AI online as {bot.user} | Owner ID: {OWNER_ID} | Guilds: {len(bot.guilds)}")


@bot.event
async def on_message(message):
    if message.author.bot:
        return
    upsert_user(message.author.id, str(message.author))
    is_dm = isinstance(message.channel, discord.DMChannel)
    mentioned = bot.user is not None and bot.user.mentioned_in(message)
    if is_dm or mentioned:
        prompt = message.content
        if bot.user:
            prompt = prompt.replace(f"<@{bot.user.id}>", "").replace(f"<@!{bot.user.id}>", "").strip()
        prompt = prompt or "Hello"
        old = [{"role": r, "content": c} for r, c in history(message.author.id)]
        memories = get_memories(message.author.id)
        user_context = f"Discord user: {message.author} | User ID: {message.author.id} | Owner: {is_owner(message.author)}"
        try:
            async with message.channel.typing():
                answer = await ask_ai(prompt, old, memories, user_context)
            add_message(message.author.id, "user", prompt)
            add_message(message.author.id, "assistant", answer)
            for start in range(0, len(answer), 1900):
                chunk = answer[start:start + 1900]
                if start == 0:
                    await message.reply(chunk, mention_author=False)
                else:
                    await message.channel.send(chunk)
        except Exception as exc:
            print(f"AI error: {exc}")
            await message.reply("I'm having trouble reaching my AI service right now. Please try again shortly.", mention_author=False)
    await bot.process_commands(message)


@bot.command()
async def owner(ctx):
    if is_owner(ctx.author):
        await ctx.reply("👑 You are my configured ArveX owner.")
    else:
        await ctx.reply("Owner status is controlled by secure bot configuration.")


@bot.command()
async def remember(ctx, *, text: str):
    """Save a user-approved memory for the caller."""
    add_memory(ctx.author.id, text, "user_command")
    await ctx.reply("🧠 Got it — I'll remember that for future conversations.")


@bot.command(name="forget")
async def forget(ctx):
    forget_memories(ctx.author.id)
    await ctx.reply("🧹 Done. I removed your saved AI memories.")


@bot.command(name="memories")
async def memories(ctx):
    saved = get_memories(ctx.author.id)
    if not saved:
        return await ctx.reply("🧠 I don't have any saved memories for you.")
    text = "\n".join(f"• {m}" for m in saved)
    await ctx.reply(f"**Your saved memories**\n{text}")


@bot.command()
@commands.guild_only()
@commands.has_permissions(moderate_members=True)
async def warn(ctx, member: discord.Member, *, reason="No reason provided"):
    count = add_warning(ctx.guild.id, member.id, ctx.author.id, reason)
    sent = await dm_user(member, f"⚠️ You received a warning in **{ctx.guild.name}**.\nReason: {reason}\nTotal warnings: {count}")
    await ctx.reply(f"⚠️ {member.mention} warned. Warning #{count}." + (" DM sent." if sent else " DM could not be sent."))


@bot.command()
@commands.guild_only()
@commands.has_permissions(moderate_members=True)
async def warnings(ctx, member: discord.Member):
    await ctx.reply(f"{member.mention} has **{warning_count(ctx.guild.id, member.id)}** warning(s).")


@bot.command()
@commands.guild_only()
@commands.has_permissions(moderate_members=True)
async def timeout(ctx, member: discord.Member, minutes: int, *, reason="No reason provided"):
    if minutes < 1 or minutes > 40320:
        return await ctx.reply("Minutes must be between 1 and 40320 (28 days).")
    from datetime import timedelta
    await member.timeout(discord.utils.utcnow() + timedelta(minutes=minutes), reason=reason)
    await dm_user(member, f"⏱️ You were timed out in **{ctx.guild.name}** for {minutes} minute(s).\nReason: {reason}")
    await ctx.reply(f"⏱️ {member.mention} timed out for {minutes} minute(s).")


@bot.command()
@commands.guild_only()
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member, *, reason="No reason provided"):
    await dm_user(member, f"👢 You were kicked from **{ctx.guild.name}**.\nReason: {reason}")
    await member.kick(reason=reason)
    await ctx.reply(f"👢 {member} kicked.")


@bot.command()
@commands.guild_only()
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member, *, reason="No reason provided"):
    await dm_user(member, f"🔨 You were banned from **{ctx.guild.name}**.\nReason: {reason}")
    await member.ban(reason=reason, delete_message_seconds=0)
    await ctx.reply(f"🔨 {member} banned.")


@bot.command()
@commands.guild_only()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    if amount < 1 or amount > 100:
        return await ctx.reply("Choose an amount from 1 to 100.", delete_after=5)
    deleted = await ctx.channel.purge(limit=amount + 1)
    await ctx.send(f"🧹 Deleted {max(0, len(deleted)-1)} message(s).", delete_after=5)


@bot.command()
async def help(ctx):
    await ctx.reply("**ArveX AI** 🤖\nMention me or DM me to chat. Memory: `!remember text`, `!memories`, `!forget`. Staff: `!warn @user reason`, `!warnings @user`, `!timeout @user minutes reason`, `!kick @user reason`, `!ban @user reason`, `!clear amount`.")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    if isinstance(error, commands.MissingPermissions):
        return await ctx.reply("❌ You don't have permission for that command.")
    if isinstance(error, commands.MissingRequiredArgument):
        return await ctx.reply("❌ Missing a required argument. Use `!help`.")
    if isinstance(error, commands.MemberNotFound):
        return await ctx.reply("❌ I couldn't find that member.")
    print(f"Command error: {error}")


bot.run(TOKEN)
