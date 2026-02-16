import discord
from discord.ext import commands
import sqlite3
import os
import random
import asyncio

# ========= INTENTS =========
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# ========= DATABASE =========
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

# ========= GAMES =========
GAMES = ["amongus", "stumble", "efootball", "freefire", "sporcle", "bloodstrike", "minecraft"]

# ========= RANK SYSTEM =========
def get_rank(xp):
    if xp >= 5000:
        return "🏆 Legend"
    elif xp >= 3000:
        return "🔥 Elite"
    elif xp >= 1500:
        return "💎 Pro Player"
    else:
        return "🎮 Gamer"

# ========= READY =========
@bot.event
async def on_ready():
    print(f"🔥 Bot Online as {bot.user}")

# ========= AUTO XP =========
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    game = "minecraft"  # تقدر تبدلها حسب روم اللعبة

    cursor.execute("INSERT OR IGNORE INTO users (user_id, game) VALUES (?, ?)",
                   (str(message.author.id), game))

    cursor.execute("UPDATE users SET xp = xp + ? WHERE user_id = ? AND game = ?",
                   (random.randint(5, 15), str(message.author.id), game))

    conn.commit()

    await bot.process_commands(message)

# ========= PROFILE =========
@bot.command()
async def profile(ctx, game: str):
    game = game.lower()

    if game not in GAMES:
        await ctx.send("❌ Game not found.")
        return

    cursor.execute("SELECT xp, money FROM users WHERE user_id = ? AND game = ?",
                   (str(ctx.author.id), game))
    data = cursor.fetchone()

    if not data:
        await ctx.send("❌ No data yet.")
        return

    xp, money = data
    rank = get_rank(xp)

    embed = discord.Embed(title=f"{ctx.author.name} - {game.upper()}",
                          color=discord.Color.blue())
    embed.add_field(name="XP", value=xp)
    embed.add_field(name="Money", value=money)
    embed.add_field(name="Rank", value=rank)

    await ctx.send(embed=embed)

# ========= DAILY =========
@bot.command()
async def daily(ctx, game: str):
    game = game.lower()

    if game not in GAMES:
        await ctx.send("❌ Game not found.")
        return

    amount = random.randint(100, 300)

    cursor.execute("INSERT OR IGNORE INTO users (user_id, game) VALUES (?, ?)",
                   (str(ctx.author.id), game))

    cursor.execute("UPDATE users SET money = money + ? WHERE user_id = ? AND game = ?",
                   (amount, str(ctx.author.id), game))

    conn.commit()

    await ctx.send(f"💰 You received {amount} coins!")

# ========= LEADERBOARD =========
@bot.command()
async def top(ctx, game: str):
    game = game.lower()

    if game not in GAMES:
        await ctx.send("❌ Game not found.")
        return

    cursor.execute("SELECT user_id, xp FROM users WHERE game = ? ORDER BY xp DESC LIMIT 10",
                   (game,))
    data = cursor.fetchall()

    if not data:
        await ctx.send("No players yet.")
        return

    embed = discord.Embed(title=f"🏆 Top Players - {game.upper()}",
                          color=discord.Color.gold())

    for i, (user_id, xp) in enumerate(data, start=1):
        user = await bot.fetch_user(int(user_id))
        embed.add_field(name=f"{i}. {user.name}", value=f"{xp} XP", inline=False)

    await ctx.send(embed=embed)

# ========= HELP =========
@bot.command()
async def help(ctx):
    embed = discord.Embed(title="🎮 Gaming Bot Commands",
                          color=discord.Color.green())

    embed.add_field(name="!profile <game>", value="Show your stats", inline=False)
    embed.add_field(name="!daily <game>", value="Claim daily coins", inline=False)
    embed.add_field(name="!top <game>", value="Leaderboard", inline=False)

    embed.add_field(name="Games",
                    value=", ".join(GAMES),
                    inline=False)

    await ctx.send(embed=embed)

# ========= RUN =========
bot.run(os.environ["TOKEN"])
