import discord
from discord import app_commands
from discord.ext import commands, tasks
import aiosqlite
import random
import asyncio

TOKEN = "PUT_YOUR_TOKEN_HERE"

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

# ================= DATABASE =================

async def setup_db():
    async with aiosqlite.connect("database.db") as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY,
            xp INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            money INTEGER DEFAULT 0,
            daily INTEGER DEFAULT 0,
            weekly INTEGER DEFAULT 0
        )
        """)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS inventory(
            user_id INTEGER,
            item TEXT,
            amount INTEGER
        )
        """)
        await db.commit()

async def get_user(user_id):
    async with aiosqlite.connect("database.db") as db:
        async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
            user = await cursor.fetchone()
            if not user:
                await db.execute("INSERT INTO users(user_id) VALUES(?)", (user_id,))
                await db.commit()
                return await get_user(user_id)
            return user

# ================= XP SYSTEM =================

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    await get_user(message.author.id)
    async with aiosqlite.connect("database.db") as db:
        xp_gain = random.randint(5, 15)
        await db.execute("UPDATE users SET xp = xp + ? WHERE user_id = ?", (xp_gain, message.author.id))
        await db.commit()
        async with db.execute("SELECT xp, level FROM users WHERE user_id = ?", (message.author.id,)) as cursor:
            data = await cursor.fetchone()
            xp, level = data
            if xp >= level * 100:
                await db.execute("UPDATE users SET level = level + 1, xp = 0 WHERE user_id = ?", (message.author.id,))
                await db.commit()
                await message.channel.send(f"🎉 {message.author.mention} leveled up!")

    await bot.process_commands(message)

# ================= SLASH COMMANDS =================

@bot.tree.command(name="rank")
async def rank(interaction: discord.Interaction):
    user = await get_user(interaction.user.id)
    embed = discord.Embed(title="📊 Rank")
    embed.add_field(name="Level", value=user[2])
    embed.add_field(name="XP", value=user[1])
    embed.add_field(name="Money", value=user[3])
    await interaction.response.send_message(embed=embed)

# ================= ECONOMY =================

@bot.tree.command(name="daily")
async def daily(interaction: discord.Interaction):
    async with aiosqlite.connect("database.db") as db:
        await db.execute("UPDATE users SET money = money + 500 WHERE user_id = ?", (interaction.user.id,))
        await db.commit()
    await interaction.response.send_message("💰 You got 500 coins!")

@bot.tree.command(name="weekly")
async def weekly(interaction: discord.Interaction):
    async with aiosqlite.connect("database.db") as db:
        await db.execute("UPDATE users SET money = money + 2000 WHERE user_id = ?", (interaction.user.id,))
        await db.commit()
    await interaction.response.send_message("💎 You got 2000 coins!")

# ================= SHOP =================

shop_items = {
    "sword": 1000,
    "shield": 800
}

@bot.tree.command(name="shop")
async def shop(interaction: discord.Interaction):
    desc = "\n".join([f"{item} - {price}$" for item, price in shop_items.items()])
    await interaction.response.send_message(f"🛒 Shop:\n{desc}")

@bot.tree.command(name="buy")
async def buy(interaction: discord.Interaction, item: str):
    if item not in shop_items:
        return await interaction.response.send_message("❌ Item not found")

    async with aiosqlite.connect("database.db") as db:
        async with db.execute("SELECT money FROM users WHERE user_id = ?", (interaction.user.id,)) as cursor:
            money = (await cursor.fetchone())[0]
        if money < shop_items[item]:
            return await interaction.response.send_message("❌ Not enough money")
        await db.execute("UPDATE users SET money = money - ? WHERE user_id = ?", (shop_items[item], interaction.user.id))
        await db.execute("INSERT INTO inventory VALUES(?, ?, 1)", (interaction.user.id, item))
        await db.commit()

    await interaction.response.send_message(f"✅ You bought {item}")

# ================= LEADERBOARD =================

@bot.tree.command(name="leaderboard")
async def leaderboard(interaction: discord.Interaction):
    async with aiosqlite.connect("database.db") as db:
        async with db.execute("SELECT user_id, level FROM users ORDER BY level DESC LIMIT 5") as cursor:
            top = await cursor.fetchall()

    text = ""
    for i, user in enumerate(top, start=1):
        member = bot.get_user(user[0])
        text += f"{i}. {member} - Level {user[1]}\n"

    await interaction.response.send_message(f"🏆 Top Players:\n{text}")

# ================= VOICE JOIN =================

@bot.tree.command(name="join")
async def join(interaction: discord.Interaction):
    if interaction.user.voice:
        channel = interaction.user.voice.channel
        await channel.connect()
        await interaction.response.send_message("🔊 Joined voice channel")
    else:
        await interaction.response.send_message("❌ Join a voice channel first")

# ================= GAME =================

@bot.tree.command(name="guess")
async def guess(interaction: discord.Interaction):
    number = random.randint(1, 10)
    await interaction.response.send_message("🎲 Guess number (1-10)")

    def check(m):
        return m.author == interaction.user and m.channel == interaction.channel

    try:
        msg = await bot.wait_for("message", timeout=15.0, check=check)
        if int(msg.content) == number:
            await interaction.channel.send("🎉 Correct! +500$")
            async with aiosqlite.connect("database.db") as db:
                await db.execute("UPDATE users SET money = money + 500 WHERE user_id = ?", (interaction.user.id,))
                await db.commit()
        else:
            await interaction.channel.send(f"❌ Wrong! Number was {number}")
    except:
        await interaction.channel.send("⏳ Time's up!")

# ================= READY =================

@bot.event
async def on_ready():
    await setup_db()
    await bot.tree.sync()
    print(f"Logged in as {bot.user}")

bot.run(os.environ["TOKEN"])
