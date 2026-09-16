import discord
from discord.ext import commands
import json, os, random, asyncio
from datetime import datetime
from PIL import Image, ImageDraw
import io

try:
    import yt_dlp
    import google.generativeai as genai
    HAS_EXTRA = True
except:
    HAS_EXTRA = False

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

TOKEN = os.getenv("DISCORD_TOKEN") or os.getenv("TOKEN")
WELCOME_CHANNEL = 0
LOG_CHANNEL = 0
AUTO_ROLE_ID = 0
GEMINI_KEY = os.getenv("GEMINI_KEY") or ""
DB_FILE = "database.json"

if os.path.exists(DB_FILE):
    with open(DB_FILE, "r", encoding="utf-8") as f:
        db = json.load(f)
else:
    db = {"users": {}, "warnings": {}, "words": {"السلام عليكم": "وعليكم السلام ❤️"}, "shop": {"VIP": 5000, "Gamer": 2000}}

def save():
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

def get_user(uid):
    uid = str(uid)
    if uid not in db["users"]:
        db["users"][uid] = {"money": 500, "xp": 0, "level": 1, "bio": "ماكو بايو", "married": None, "rep": 0, "daily": 0}
    return db["users"][uid]

if HAS_EXTRA and GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)
    ai_model = genai.GenerativeModel("gemini-1.5-flash")

async def make_welcome_image(member):
    img = Image.new('RGB', (800, 300), color=(15, 15, 25))
    draw = ImageDraw.Draw(img)
    try:
        avatar_bytes = await member.display_avatar.read()
        avatar = Image.open(io.BytesIO(avatar_bytes)).resize((180, 180))
        mask = Image.new("L", (180, 180), 0)
        ImageDraw.Draw(mask).ellipse((0,0,180,180), fill=255)
        img.paste(avatar, (40, 60), mask)
    except: pass
    draw.text((260, 80), "WELCOME", fill=(0, 200, 255))
    draw.text((260, 130), member.name, fill=(255,255,255))
    draw.text((260, 180), f"Member #{member.guild.member_count}", fill=(150,150,150))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

@bot.event
async def on_member_join(member):
    if AUTO_ROLE_ID!= 0:
        role = member.guild.get_role(AUTO_ROLE_ID)
        if role:
            try: await member.add_roles(role)
            except: pass
    if WELCOME_CHANNEL!= 0:
        ch = bot.get_channel(WELCOME_CHANNEL)
        if ch:
            try:
                image = await make_welcome_image(member)
                file = discord.File(image, filename="welcome.png")
                embed = discord.Embed(title=f"نورت {member.name}!", color=0x00aaff)
                embed.set_image(url="attachment://welcome.png")
                await ch.send(embed=embed, file=file)
            except: pass

@bot.event
async def on_ready():
    print(f"Meta AI V5 شغال: {bot.user}")
    await bot.tree.sync()

@bot.hybrid_command(name="profile", description="بروفايلك")
async def profile(ctx, member: discord.Member = None):
    m = member or ctx.author
    u = get_user(m.id)
    embed = discord.Embed(title=f"بروفايل {m.name}", color=0x00aaff)
    embed.set_thumbnail(url=m.display_avatar.url)
    embed.add_field(name="💰 الفلوس", value=f"{u['money']}$")
    embed.add_field(name="⭐ ليفل", value=f"{u['level']} ({u['xp']} XP)")
    embed.add_field(name="❤️ سمعة", value=u['rep'])
    embed.add_field(name="📝 بايو", value=u['bio'], inline=False)
    await ctx.send(embed=embed)

@bot.hybrid_command(name="daily")
async def daily(ctx):
    u = get_user(ctx.author.id)
    if datetime.now().timestamp() - u['daily'] < 86400:
        await ctx.send("اخذت جائزتك اليوم ⏰", ephemeral=True); return
    r = random.randint(200, 500)
    u['money'] += r
    u['daily'] = datetime.now().timestamp()
    save()
    await ctx.send(f"اخذت {r}$ اليوم 💰")

@bot.hybrid_command(name="work")
async def work(ctx):
    u = get_user(ctx.author.id)
    r = random.randint(50, 150)
    u['money'] += r
    save()
    await ctx.send(f"اشتغلت وحصلت {r}$ 🔨")

@bot.event
async def on_message(message):
    if message.author.bot: return
    u = get_user(message.author.id)
    u['xp'] += random.randint(5, 15)
    if u['xp'] >= u['level']*100:
        u['level'] += 1
        await message.channel.send(f"🎉 {message.author.mention} صعد ليفل {u['level']}!")
    save()
    await bot.process_commands(message)

bot.run(TOKEN)
