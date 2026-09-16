import os
import discord
from discord.ext import commands
import asyncio
import sqlite3
import random
from datetime import datetime, timedelta

# --- إعدادات ---
TOKEN = os.getenv("DISCORD_TOKEN")
ENABLE_CONTENT = os.getenv("ENABLE_MESSAGE_CONTENT", "true").lower() == "true"

intents = discord.Intents.default()
intents.members = True
if ENABLE_CONTENT:
    intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# --- قاعدة البيانات ---
db = sqlite3.connect("meta.db")
cur = db.cursor()
cur.execute("""CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    xp INTEGER DEFAULT 0,
    level INTEGER DEFAULT 0,
    coins INTEGER DEFAULT 0,
    last_daily TEXT,
    last_weekly TEXT
)""")
db.commit()

def get_user(user_id):
    cur.execute("SELECT * FROM users WHERE id=?", (str(user_id),))
    row = cur.fetchone()
    if not row:
        cur.execute("INSERT INTO users (id) VALUES (?)", (str(user_id),))
        db.commit()
        return get_user(user_id)
    return {"id": row[0], "xp": row[1], "level": row[2], "coins": row[3], "last_daily": row[4], "last_weekly": row[5]}

def add_xp(user_id, amount=15):
    u = get_user(user_id)
    xp = u["xp"] + amount
    level = xp // 300
    cur.execute("UPDATE users SET xp=?, level=? WHERE id=?", (xp, level, str(user_id)))
    db.commit()
    return level

# --- أحداث ---
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (id {bot.user.id})")
    print("Meta AI V5 شغال ✅")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(e)

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if not message.guild:
        return
    add_xp(message.author.id, random.randint(10, 25))
    await bot.process_commands(message)

# --- أوامر ---
@bot.hybrid_command(name="ping", description="Replies with the round-trip latency")
async def ping(ctx):
    await ctx.send(f"Pong! {round(bot.latency*1000)}ms 🚀")

@bot.hybrid_command(name="hello", description="Replies with a greeting")
async def hello(ctx):
    await ctx.send(f"هلا والله {ctx.author.mention} 👋 نورّت!")

@bot.hybrid_command(name="profile", description="يعرض بروفايلك")
async def profile(ctx, member: discord.Member = None):
    member = member or ctx.author
    u = get_user(member.id)
    embed = discord.Embed(title=f"بروفايل {member.display_name}", color=0x5865F2)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="⭐ لفل", value=u["level"], inline=True)
    embed.add_field(name="✨ XP", value=u["xp"], inline=True)
    embed.add_field(name="💰 كوينز", value=u["coins"], inline=True)
    await ctx.send(embed=embed)

@bot.hybrid_command(name="daily", description="جائزة يومية")
async def daily(ctx):
    u = get_user(ctx.author.id)
    now = datetime.now()
    if u["last_daily"]:
        last = datetime.fromisoformat(u["last_daily"])
        if now - last < timedelta(hours=24):
            remain = timedelta(hours=24) - (now - last)
            return await ctx.send(f"⏳ بعد {str(remain).split('.')[0]} تكدر تاخذها!")
    cur.execute("UPDATE users SET coins=coins+200, last_daily=? WHERE id=?", (now.isoformat(), str(ctx.author.id)))
    db.commit()
    await ctx.send("✅ استلمت 200 كوينز يومية! +daily")

@bot.hybrid_command(name="weekly", description="جائزة اسبوعية")
async def weekly(ctx):
    u = get_user(ctx.author.id)
    now = datetime.now()
    if u["last_weekly"]:
        last = datetime.fromisoformat(u["last_weekly"])
        if now - last < timedelta(days=7):
            return await ctx.send("⏳ الاسبوعية كل 7 ايام!")
    cur.execute("UPDATE users SET coins=coins+1000, last_weekly=? WHERE id=?", (now.isoformat(), str(ctx.author.id)))
    db.commit()
    await ctx.send("🎉 استلمت 1000 كوينز اسبوعية!")

@bot.hybrid_command(name="top", description="توب لفل")
async def top(ctx):
    cur.execute("SELECT id, xp, level FROM users ORDER BY xp DESC LIMIT 10")
    rows = cur.fetchall()
    desc = ""
    for i, (uid, xp, lvl) in enumerate(rows, 1):
        try:
            user = await bot.fetch_user(int(uid))
            name = user.display_name
        except:
            name = uid
        desc += f"**{i}. {name}** - لفل {lvl} ({xp} XP)\n"
    embed = discord.Embed(title="🏆 توب 10", description=desc, color=0xFFD700)
    await ctx.send(embed=embed)

bot.run(TOKEN)
