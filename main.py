import discord
from discord.ext import commands
import os

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

TOKEN = os.getenv("DISCORD_TOKEN")

@bot.event
async def on_ready():
    print(f"Meta Al شغال: {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("Meta Al شغال حبي ✅")

bot.run(TOKEN)
