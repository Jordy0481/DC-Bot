# Boot message
print("Booting up...")

import discord
from discord.ext import commands
import os

from flask import Flask
from threading import Thread

# ------------------- Keep Alive Webserver -------------------
app = Flask('')

@app.route('/')
def home():
    return "✅ Bot is alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()


# ------------------- Discord Bot -------------------
# Vul hier je server-ID in (voor slash commands in 1 server)
GUILD_ID = 1342974632524775526

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True

bot = commands.Bot(command_prefix="/", intents=intents)
bot.role_embed_data = {}  # opslag voor role embeds


# Event: bot ready
@bot.event
async def on_ready():
    print(f"✅ Bot ingelogd als {bot.user}")
    try:
        # Alleen in 1 server syncen (snelste)
        synced = await bot.tree.sync(guild=discord.Object(id=GUILD_ID))
        print(f"🌐 Slash commands gesynchroniseerd: {len(synced)}")
    except Exception as e:
        print(f"❌ Fout bij sync: {e}")


# ------------------- Commands -------------------
@bot.tree.command(
    name="ping",
    description="Check de latency van de bot",
    guild=discord.Object(id=GUILD_ID)
)
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(
        f"Pong! `{bot.latency*1000:.2f}ms`", ephemeral=True
    )


# (EmbedModal, RoleEmbedModal en role reaction code laat ik zoals jij had, 
# die waren verder goed!)


# ------------------- Start Bot -------------------
keep_alive()

TOKEN = os.getenv("DISCORD_TOKEN")  # gebruik "TOKEN" als env variable in Koyeb
if not TOKEN:
    print("❌ Geen Discord TOKEN gevonden in environment variables!")
else:
    bot.run(TOKEN)
