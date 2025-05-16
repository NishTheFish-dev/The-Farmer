import discord
from discord import Embed, ButtonStyle
from discord.ext import commands
from discord.ui import Button, View
import json
import time
import random
import os
from dotenv import load_dotenv
from config import (
    Colors,
    GameConstants,
    ShopConfig,
    BiomeConfig,
    SeedConfig,
    CropConfig,
    MutationConfig,
    EmojiConfig,
    DataConfig
)
from utils.database import load_data, save_data, get_user_data

# Load environment variables
load_dotenv()

# Get token directly from .env file
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
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)  # Disable default help command

# Event: Bot is ready
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    print('------')

def get_random_seed():
    roll = random.uniform(0, 100)
    cumulative = 0
    selected_tier = None
    
    for tier, values in SeedConfig.SEEDS.items():
        cumulative += values["chance"]
        if roll <= cumulative:
            selected_tier = tier
            break
    
    seed = random.choice(SeedConfig.SEEDS[selected_tier]["seeds"])
    return seed, 1, selected_tier

async def harvest_from_biome(user, biome, now):
    harvested = []
    
    # Sort plantings by start time to ensure we harvest earliest first
    sorted_plantings = sorted(
        user["plantings"][biome].items(),
        key=lambda x: x[1]["start_time"]
    )
    
    for planting_id, details in sorted_plantings:
        if now - details["start_time"] >= details["duration"]:
            seed_type = details["seed_type"]
            crop_name = seed_type.replace("_seed", "")
            
            # Find crop rarity
            crop_tier = next(
                (tier for tier, values in CropConfig.CROPS.items() 
                 if crop_name in values["crops"]),
                "common"
            )
            
            # Calculate yield
            tier_data = CropConfig.CROPS[crop_tier]
            base = tier_data["base_yield"]
            extra = random.randint(0, tier_data["max_extra"])
            total_yield = (base + extra) * details["amount"]
            
            # Check for mutations
            mutation = None
            mutation_roll = random.uniform(0, 100)
            cumulative_chance = 0
            
            for mut_type, mut_data in MutationConfig.MUTATIONS.items():
                cumulative_chance += mut_data["chance"]
                if mutation_roll <= cumulative_chance:
                    mutation = mut_type
                    break
            
            # Initialize inventory structure if needed
            if crop_name not in user["inventory"]:
                user["inventory"][crop_name] = 0
            
            # Convert old integer structure to new dict structure if needed
            if isinstance(user["inventory"][crop_name], int):
                old_amount = user["inventory"][crop_name]
                user["inventory"][crop_name] = {
                    "amount": old_amount,
                    "mutations": {}
                }
            
            # Update inventory with mutation information
            if mutation:
                if "mutations" not in user["inventory"][crop_name]:
                    user["inventory"][crop_name]["mutations"] = {}
                if mutation not in user["inventory"][crop_name]["mutations"]:
                    user["inventory"][crop_name]["mutations"][mutation] = 0
                user["inventory"][crop_name]["mutations"][mutation] += total_yield
                harvested.append(
                    f"{MutationConfig.MUTATIONS[mutation]['emoji']} {mutation.title()} {crop_name.title()} x{total_yield}"
                )
            else:
                if isinstance(user["inventory"][crop_name], dict):
                    user["inventory"][crop_name]["amount"] += total_yield
                else:
                    user["inventory"][crop_name] = {
                        "amount": total_yield,
                        "mutations": {}
                    }
                harvested.append(
                    f"{EmojiConfig.EMOJI_MAP[crop_name]} {crop_name.title()} x{total_yield}"
                )
            
            del user["plantings"][biome][planting_id]
    
    return harvested

# Run the bot
token = get_token()
if token is None:
    print("Error: Could not read token from .env file")
else:
    bot.run(token) 