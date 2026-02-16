import discord
from discord.ext import commands
import os
import sqlite3
import random
import time

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ================= DATABASE =================
conn = sqlite3.connect("gaming.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT,
    game TEXT,
    xp INTEGER DEFAULT 0,
    money INTEGER DEFAULT 0,
    PRIMARY KEY (user_id, game)
)
""")
conn.commit()

cooldown = {}

# ================= HELP =================
@bot.command()
async def help(ctx):
    await ctx.send("""
🎮 **Gaming Bot Commands**

💰 Economy:
!balance
!daily
!work

🎮 Games:
!game amongus/minecraft/freefire/stumble
!rank amongus
!top amongus
!lfg minecraft

👑 Profile:
!profile

🛡 Admin:
!clear 5
""")

# ================= READY =================
@bot.event
async def on_ready():
    print(f"🔥 Bot Online as {bot.user}")

# ================= WELCOME =================
@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name="general")
    role = discord.utils.get(member.guild.roles, name="Member")

    if role:
        await member.add_roles(role)

    if channel:
        await channel.send(f"🎉 مرحبا {member.mention} في السيرفر 🔥")

    try:
        await member.send("👑 مرحبا بك في Gaming Hub!")
    except:
        pass

# ================= XP SYSTEM =================
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    user = str(message.author.id)

    if user not in cooldown or time.time() - cooldown[user] > 10:
        cooldown[user] = time.time()

        game = "global"

        cursor.execute("INSERT OR IGNORE INTO users (user_id, game, xp, money) VALUES (?, ?, 0, 0)", (user, game))
        cursor.execute("UPDATE users SET xp = xp + 5 WHERE user_id = ? AND game = ?", (user, game))
        conn.commit()

        cursor.execute("SELECT xp FROM users WHERE user_id = ? AND game = ?", (user, game))
        xp = cursor.fetchone()[0]

        level = xp // 100

        if xp % 500 == 0:
            await message.channel.send(f"🎉 {message.author.mention} وصل Level {level}")

    await bot.process_commands(message)

# ================= PROFILE =================
@bot.command()
async def profile(ctx):
    user = str(ctx.author.id)

    cursor.execute("INSERT OR IGNORE INTO users (user_id, game, xp, money) VALUES (?, 'global', 0, 0)", (user,))
    cursor.execute("SELECT xp, money FROM users WHERE user_id = ? AND game = 'global'", (user,))
    data = cursor.fetchone()

    xp, money = data
    level = xp // 100

    embed = discord.Embed(title="👑 Profile", color=discord.Color.blue())
    embed.add_field(name="Level", value=level)
    embed.add_field(name="XP", value=xp)
    embed.add_field(name="Money", value=money)

    await ctx.send(embed=embed)

# ================= ECONOMY =================
@bot.command()
async def balance(ctx):
    await profile(ctx)

@bot.command()
async def daily(ctx):
    user = str(ctx.author.id)
    reward = random.randint(100,300)

    cursor.execute("UPDATE users SET money = money + ? WHERE user_id = ? AND game = 'global'", (reward, user))
    conn.commit()

    await ctx.send(f"🎁 ربحت {reward} 💰")

@bot.command()
async def work(ctx):
    user = str(ctx.author.id)
    reward = random.randint(50,150)

    cursor.execute("UPDATE users SET money = money + ? WHERE user_id = ? AND game = 'global'", (reward, user))
    conn.commit()

    await ctx.send(f"💼 خدمت وربحت {reward} 💰")

# ================= GAME ROLE =================
@bot.command()
async def game(ctx, game_name):
    role = discord.utils.get(ctx.guild.roles, name=game_name.capitalize())
    if role:
        await ctx.author.add_roles(role)
        await ctx.send(f"🎮 تم إعطاؤك رول {role.name}")
    else:
        await ctx.send("❌ اللعبة غير موجودة")

# ================= RANK PER GAME =================
@bot.command()
async def rank(ctx, game_name):
    user = str(ctx.author.id)

    cursor.execute("INSERT OR IGNORE INTO users (user_id, game, xp, money) VALUES (?, ?, 0, 0)", (user, game_name))
    cursor.execute("SELECT xp FROM users WHERE user_id = ? AND game = ?", (user, game_name))
    xp = cursor.fetchone()[0]

    level = xp // 100

    await ctx.send(f"🎮 Rank in {game_name}: Level {level} | XP {xp}")

# ================= TOP =================
@bot.command()
async def top(ctx, game_name):
    cursor.execute("SELECT user_id, xp FROM users WHERE game = ? ORDER BY xp DESC LIMIT 5", (game_name,))
    data = cursor.fetchall()

    msg = "🏆 Top Players:\n"
    for i, row in enumerate(data, start=1):
        user = await bot.fetch_user(int(row[0]))
        msg += f"{i}. {user.name} - {row[1]} XP\n"

    await ctx.send(msg)

# ================= LFG =================
@bot.command()
async def lfg(ctx, game_name):
    role = discord.utils.get(ctx.guild.roles, name=game_name.capitalize())
    if role:
        await ctx.send(f"🔥 {ctx.author.mention} يبحث عن لاعبين {role.mention}")

# ================= CLEAR =================
@bot.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    await ctx.channel.purge(limit=amount + 1)

bot.run(os.environ["TOKEN"])
