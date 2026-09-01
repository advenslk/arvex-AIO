import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from groq_ai import ask_ai

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN is not set")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"ArveX AI online as {bot.user} | Owner ID: {OWNER_ID}")

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    is_dm = isinstance(message.channel, discord.DMChannel)
    mentioned = bot.user is not None and bot.user.mentioned_in(message)
    if is_dm or mentioned:
        prompt = message.content
        if bot.user:
            prompt = prompt.replace(f"<@{bot.user.id}>", "").replace(f"<@!{bot.user.id}>", "").strip()
        if not prompt:
            prompt = "Hello"
        try:
            async with message.channel.typing():
                answer = await ask_ai(prompt)
            await message.reply(answer[:2000], mention_author=False)
        except Exception as exc:
            print(f"AI error: {exc}")
            await message.reply("I'm having trouble reaching my AI service right now. Please try again shortly.", mention_author=False)
    await bot.process_commands(message)

@bot.command()
async def owner(ctx: commands.Context):
    if ctx.author.id == OWNER_ID:
        await ctx.reply("👑 You are my configured ArveX owner.")
    else:
        await ctx.reply("I only recognize the configured owner through the bot's secure owner ID.")

bot.run(TOKEN)
