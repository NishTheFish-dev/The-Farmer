import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from config.rate_limiter import RateLimiter

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

# Initialize rate limiter
rate_limiter = RateLimiter(max_commands=10, time_window=8, timeout_duration=30)

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        await ctx.send(f"⏰ This command is on cooldown. Try again in {error.retry_after:.2f}s")
    elif isinstance(error, commands.CommandNotFound):
        pass  # Ignore command not found errors
    else:
        print(f"Command error: {error}")

@bot.check
async def check_rate_limit(ctx):
    if rate_limiter.is_rate_limited(ctx.author.id):
        remaining = rate_limiter.get_timeout_remaining(ctx.author.id)
        await ctx.send(f"⚠️ You are being rate limited. Please wait {int(remaining)} seconds before using commands again.")
        return False
    return True

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