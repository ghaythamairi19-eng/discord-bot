import discord
from discord import app_commands
from discord.ext import commands, tasks
import random
import json
import os
import datetime

TOKEN = "YOUR_BOT_TOKEN"

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

DATA_FILE = "data.json"

# ================= DATA =================

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)

def load_data():
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_user(data, user_id):
    if str(user_id) not in data:
        data[str(user_id)] = {
            "xp": 0,
            "coins": 0,
            "level": 1,
            "games": {},
            "badges": [],
            "last_daily": ""
        }
    return data[str(user_id)]

# ================= LEVEL SYSTEM =================

def calculate_level(xp):
    return int((xp // 100) + 1)

# ================= EVENTS =================

@bot.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {bot.user}")

@bot.event
async def on_member_join(member):
    channel = discord.utils.get(member.guild.text_channels, name="welcome")
    if channel:
        await channel.send(f"🎉 Welcome {member.mention} to the server!")

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    data = load_data()
    user = get_user(data, message.author.id)

    user["xp"] += random.randint(5, 15)

    new_level = calculate_level(user["xp"])
    if new_level > user["level"]:
        user["level"] = new_level
        await message.channel.send(f"🎉 {message.author.mention} leveled up to {new_level}!")

    save_data(data)
    await bot.process_commands(message)

# ================= PROFILE =================

@tree.command(name="profile", description="View your profile")
async def profile(interaction: discord.Interaction):
    data = load_data()
    user = get_user(data, interaction.user.id)

    embed = discord.Embed(title=f"{interaction.user.name} Profile", color=discord.Color.blue())
    embed.add_field(name="Level", value=user["level"])
    embed.add_field(name="XP", value=user["xp"])
    embed.add_field(name="Coins", value=user["coins"])
    embed.add_field(name="Badges", value=", ".join(user["badges"]) or "None")
    embed.set_thumbnail(url=interaction.user.avatar.url if interaction.user.avatar else None)

    await interaction.response.send_message(embed=embed)
@bot.command(name="u")
async def user_prefix(ctx, member: discord.Member = None):

    if member is None:
        member = ctx.author

    data = load_data()
    user_id = str(member.id)

    level = 0
    xp = 0

    if user_id in data:
        level = data[user_id]["level"]
        xp = data[user_id]["xp"]

    embed = discord.Embed(
        title=f"👤 معلومات {member.name}",
        color=member.color
    

    embed.set_thumbnail(url=member.display_avatar.url)

    embed.add_field(name="🆔 ID", value=member.id, inline=False)
    embed.add_field(name="📊 Level", value=level, inline=True)
    embed.add_field(name="⭐ XP", value=xp, inline=True)
    embed.add_field(name="📅 انضم للسيرفر", value=member.joined_at.strftime("%Y-%m-%d"), inline=False)
    embed.add_field(name="🗓️ تاريخ إنشاء الحساب", value=member.created_at.strftime("%Y-%m-%d"), inline=False)

    await ctx.send(embed=embed)
    @bot.tree.command(name="slots", description="جرب حظك في السلوت")
async def slots(interaction: discord.Interaction):

    emojis = ["🍎", "🍌", "🍇", "🍒"]
    result = [random.choice(emojis) for _ in range(3)]

    if result[0] == result[1] == result[2]:
        msg = "🔥 JACKPOT! فزت!"
    else:
        msg = "حظ أوفر المرة الجاية 😅"

    embed = discord.Embed(title="🎰 Slot Machine", color=discord.Color.gold())
    embed.add_field(name="النتيجة", value=" | ".join(result), inline=False)
    embed.add_field(name="الحكم", value=msg)

    await interaction.response.send_message(embed=embed)
    
# ================= DAILY =================

@tree.command(name="daily", description="Claim daily reward")
async def daily(interaction: discord.Interaction):
    data = load_data()
    user = get_user(data, interaction.user.id)

    today = str(datetime.date.today())

    if user["last_daily"] == today:
        await interaction.response.send_message("⏳ You already claimed today!")
        return

    reward = random.randint(50, 150)
    user["coins"] += reward
    user["last_daily"] = today
    save_data(data)

    await interaction.response.send_message(f"💰 You received {reward} coins!")

# ================= BALANCE =================

@tree.command(name="balance", description="Check your balance")
async def balance(interaction: discord.Interaction):
    data = load_data()
    user = get_user(data, interaction.user.id)
    await interaction.response.send_message(f"💰 Coins: {user['coins']}")

# ================= SHOP =================

SHOP_ITEMS = {
    "Red Name": 1000,
    "Blue Name": 1000,
    "VIP Role": 20000
}

@tree.command(name="shop", description="View shop items")
async def shop(interaction: discord.Interaction):
    embed = discord.Embed(title="🛒 Shop")
    for item, price in SHOP_ITEMS.items():
        embed.add_field(name=item, value=f"{price} coins")
    await interaction.response.send_message(embed=embed)

@tree.command(name="buy", description="Buy item")
@app_commands.describe(item="Item name")
async def buy(interaction: discord.Interaction, item: str):
    data = load_data()
    user = get_user(data, interaction.user.id)

    if item not in SHOP_ITEMS:
        await interaction.response.send_message("❌ Item not found.")
        return

    price = SHOP_ITEMS[item]

    if user["coins"] < price:
        await interaction.response.send_message("❌ Not enough coins.")
        return

    user["coins"] -= price
    user["badges"].append(item)
    save_data(data)

    await interaction.response.send_message(f"✅ You bought {item}!")

# ================= GAME XP =================

@tree.command(name="addxp", description="Add XP to a game")
@app_commands.describe(game="Game name", amount="XP amount")
async def addxp(interaction: discord.Interaction, game: str, amount: int):
    data = load_data()
    user = get_user(data, interaction.user.id)

    if game not in user["games"]:
        user["games"][game] = 0

    user["games"][game] += amount
    save_data(data)

    await interaction.response.send_message(f"🎮 Added {amount} XP to {game}")

# ================= TOP =================

@tree.command(name="top", description="Global leaderboard")
async def top(interaction: discord.Interaction):
    data = load_data()
    sorted_users = sorted(data.items(), key=lambda x: x[1]["xp"], reverse=True)

    text = ""
    for i, (uid, info) in enumerate(sorted_users[:10], start=1):
        text += f"{i}. <@{uid}> - {info['xp']} XP\n"

    await interaction.response.send_message(f"🏆 Leaderboard:\n{text}")

# ================= TOURNAMENT =================

current_tournament = {"active": False, "players": []}

@tree.command(name="tournament_create", description="Create tournament")
async def tournament_create(interaction: discord.Interaction):
    if current_tournament["active"]:
        await interaction.response.send_message("⚠ Tournament already active.")
        return

    current_tournament["active"] = True
    current_tournament["players"] = []
    await interaction.response.send_message("🏆 Tournament started! Use /join")

@tree.command(name="join", description="Join tournament")
async def join(interaction: discord.Interaction):
    if not current_tournament["active"]:
        await interaction.response.send_message("❌ No active tournament.")
        return

    current_tournament["players"].append(interaction.user)
    await interaction.response.send_message("✅ Joined tournament!")

@tree.command(name="tournament_end", description="End tournament")
async def tournament_end(interaction: discord.Interaction):
    if not current_tournament["active"]:
        await interaction.response.send_message("❌ No active tournament.")
        return

    if not current_tournament["players"]:
        await interaction.response.send_message("No players.")
        return

    winner = random.choice(current_tournament["players"])
    data = load_data()
    user = get_user(data, winner.id)

    user["coins"] += 1000
    user["xp"] += 500
    user["badges"].append("🏆 Champion")
    save_data(data)

    current_tournament["active"] = False

    await interaction.response.send_message(f"🏆 Winner: {winner.mention}")

# ================= SEASON =================

@tree.command(name="season_reset", description="Reset season")
async def season_reset(interaction: discord.Interaction):
    data = load_data()
    sorted_users = sorted(data.items(), key=lambda x: x[1]["xp"], reverse=True)

    if sorted_users:
        winner_id = sorted_users[0][0]
        data[winner_id]["badges"].append("👑 Season Winner")

    for uid in data:
        data[uid]["xp"] = 0

    save_data(data)
    await interaction.response.send_message("🔄 Season Reset Done!")

bot.run(os.environ["TOKEN"])
