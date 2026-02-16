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

# ================= PROFILE ===============
const { joinVoiceChannel } = require('@discordjs/voice');

client.on('interactionCreate', async interaction => {
  if (!interaction.isChatInputCommand()) return;

  if (interaction.commandName === 'join') {
    const channel = interaction.member.voice.channel;

    if (!channel) {
      return interaction.reply('❌ لازم تدخل روم صوتي أولاً');
    }

    joinVoiceChannel({
      channelId: channel.id,
      guildId: channel.guild.id,
      adapterCreator: channel.guild.voiceAdapterCreator,
    });

    interaction.reply('✅ دخلت الروم الصوتي');
  }
});

    
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
import threading
from flask import Flask
import os

app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8000)))

def keep_alive():
    t = threading.Thread(target=run)
    t.start()

keep_alive()
bot.run(os.environ["TOKEN"])
