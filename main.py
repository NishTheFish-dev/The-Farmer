import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get token from .env file
def get_token():
    try:
        with open('.env', 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if '=' in content:
                return content.split('=')[1].strip()
    except Exception as e:
        print(f"Error reading token: {e}")
    return None

# Initialize bot with proper permissions
intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# Load all cogs
async def load_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py") and not filename.startswith("__"):
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"Loaded {filename}")
            except Exception as e:
                print(f"Failed to load {filename}: {e}")

@bot.event
async def on_ready():
    await load_cogs()
    print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    print('------')

# Run the bot
if __name__ == "__main__":
    token = get_token()
    if token is None:
        print("Error: Could not read token from .env file")
    else:
        bot.run(token) 