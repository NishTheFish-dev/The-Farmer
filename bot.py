import discord
from discord import Embed
from discord.ext import commands
import json
import time
import random
import os
from dotenv import load_dotenv

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

# Color constants under crop configuration
EMBED_COLOR = 0x2ecc71  # Green theme
ERROR_COLOR = 0xe74c3c  # Red for errors
INFO_COLOR = 0x3498db   # Blue for info

# Initialize bot with proper permissions
intents = discord.Intents.default()
intents.members = True
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Event: Bot is ready
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} (ID: {bot.user.id})')
    print('------')

# Seed config
SEEDS = {
    "common": {
        "seeds": ["wheat_seed", "potato_seed"],
        "chance": 80
    },
    "uncommon": {
        "seeds": ["carrot_seed", "rice_seed"],
        "chance": 15
    },
    "rare": {
        "seeds": ["apple_seed", "orange_seed"],
        "chance": 3.25
    },
    "epic": {
        "seeds": ["kiwi_seed"],
        "chance": 1.25
    },
    "legendary": {
        "seeds": ["melon_seed"],
        "chance": 0.5
    }
}

# Crop config
CROPS = {
    "common": {
        "crops": ["wheat", "potato"],
        "base_yield": 5,
        "max_extra": 3,
        "chance": 80
    },
    "uncommon": {
        "crops": ["carrot", "rice"],
        "base_yield": 3,
        "max_extra": 3,
        "chance": 15
    },
    "rare": {
        "crops": ["apple", "orange"],
        "base_yield": 1,
        "max_extra": 2,
        "chance": 3.25
    },
    "epic": {
        "crops": ["kiwi"],
        "base_yield": 1,
        "max_extra": 2,
        "chance": 1.25
    },
    "legendary": {
        "crops": ["melon"],
        "base_yield": 1,
        "max_extra": 2,
        "chance": 0.5
    }
}

# Timer config
PLANT_TIMES = {
    "wheat_seed": 30,
    "potato_seed": 40,
    "rice_seed": 50,
    "carrot_seed": 60,
    "apple_seed": 120,
    "orange_seed": 150,
    "kiwi_seed": 240,
    "melon_seed": 360
}

# Planter capacity (increases with upgrades)
MAX_PLANTER_CAPACITY = 3

# Price config
PRICES = {
    "wheat": 2,
    "potato": 3,
    "carrot": 4,
    "rice": 5,
    "apple": 10,
    "orange": 15,
    "kiwi": 25,
    "melon": 50
}

# Emoji map for crops
EMOJI_MAP = {
    # Crops
    "wheat": "🌾",
    "potato": "🥔",
    "carrot": "🥕",
    "rice": "🍚",
    "apple": "🍎",
    "orange": "🍊",
    "kiwi": "🥝",
    "melon": "🍈",

    # Seeds
    "wheat_seed": "🌾",
    "potato_seed": "🥔",
    "carrot_seed": "🥕",
    "rice_seed": "🍚",
    "apple_seed": "🍎",
    "orange_seed": "🍊",
    "kiwi_seed": "🥝",
    "melon_seed": "🍈"
}

# New planting configuration
PLANT_YIELDS = {
    "wheat_seed": ("wheat", 5),
    "potato_seed": ("potato", 5),
    "carrot_seed": ("carrot", 3),
    "rice_seed": ("rice", 3),
    "apple_seed": ("apple", 1),
    "orange_seed": ("orange", 1),
    "kiwi_seed": ("kiwi", 1),
    "melon_seed": ("melon", 1)
}

# Load/save data functions
def load_data():
    try:
        with open("farm_data.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"users": {}}

def save_data(data):
    with open("farm_data.json", "w") as f:
        json.dump(data, f, indent=2)

def get_random_seed():
    roll = random.uniform(0, 100)
    cumulative = 0
    selected_tier = None
    
    for tier, values in SEEDS.items():
        cumulative += values["chance"]
        if roll <= cumulative:
            selected_tier = tier
            break
    
    seed = random.choice(SEEDS[selected_tier]["seeds"])
    return seed, 1, selected_tier  # Always yield 1 seed

# Command: Roll for seeds
@bot.command()
async def roll(ctx):
    user_id = str(ctx.author.id)
    data = load_data()
    now = time.time()

    if user_id not in data["users"]:
        data["users"][user_id] = {
            "last_rolled": 0,
            "inventory": {crop: 0 for tier in CROPS.values() for crop in tier["crops"]}, 
            "seeds": {seed: 0 for seed in PLANT_TIMES.keys()},
            "plantings": {},
            "balance": 0
        }

    user = data["users"][user_id]
    time_since_last = now - user["last_rolled"]

    # 1 minute cooldown (60 seconds)
    if time_since_last < 3:
        remaining = 3 - time_since_last
        embed = Embed(
            title="⏳ Rolling Cooldown",
            description=f"You need to wait {int(remaining)} seconds!",
            color=ERROR_COLOR
        )
        await ctx.send(embed=embed)
        return

    seed, amount, rarity = get_random_seed()
    user["last_rolled"] = now
    user["seeds"][seed] += amount
    save_data(data)

    embed = Embed(
        title=f"{EMOJI_MAP[seed]} {rarity.title()} Seed Roll!",
        description=f"You obtained **{amount}** {seed.replace('_', ' ').title()}!",
        color=EMBED_COLOR
    )
    await ctx.send(embed=embed)

# Command: plant
@bot.command()
async def plant(ctx, seed_type: str = None, amount: int = None):
    user_id = str(ctx.author.id)
    data = load_data()
    now = time.time()

    if user_id not in data["users"]:
        await ctx.send("You need to roll for seeds first! Use `!roll`")
        return

    if not seed_type:
        embed = Embed(
            title="❌ Missing Arguments",
            description="**Usage:** `!plant <seed> [amount]`\nExample: `!plant wheat 2`",
            color=ERROR_COLOR
        )
        await ctx.send(embed=embed)
        return

    user = data["users"][user_id]
    # Initialize plantings if missing
    if "plantings" not in user:
        user["plantings"] = {}
    seed_type = seed_type.lower() + "_seed"  # Auto-append _seed

    # Validation
    if seed_type not in PLANT_TIMES:
        embed = Embed(
            title="❌ Invalid Seed Type",
            description=f"`{seed_type.replace('_seed', '')}` isn't a plantable seed!",
            color=ERROR_COLOR
        )
        embed.add_field(
            name="Available Seeds",
            value="\n".join([f"- {s.replace('_seed', '')}" for s in PLANT_TIMES.keys()]),
            inline=False
        )
        await ctx.send(embed=embed)
        return

    available_seeds = user["seeds"].get(seed_type, 0)
    if available_seeds <= 0:
        embed = Embed(
            title="❌ No Seeds Available",
            description=f"You don't have any {seed_type.replace('_seed', '')} seeds!",
            color=ERROR_COLOR
        )
        await ctx.send(embed=embed)
        return

    # Calculate remaining planter capacity
    used_capacity = len(user["plantings"])  # Now counts individual plantings
    remaining_capacity = MAX_PLANTER_CAPACITY - used_capacity

    # Determine planting amount
    if amount is None:
        plant_amount = min(available_seeds, remaining_capacity)
    else:
        plant_amount = min(amount, available_seeds, remaining_capacity)

    if plant_amount <= 0:
        embed = Embed(
            title="❌ Invalid Planting",
            description="Can't plant 0 or negative seeds!",
            color=ERROR_COLOR
        )
        await ctx.send(embed=embed)
        return

    if plant_amount > remaining_capacity:
        plant_amount = remaining_capacity
        if plant_amount <= 0:
            embed = Embed(
                title="❌ Planter Full",
                description=f"Wait for current plantings to finish! (Max {MAX_PLANTER_CAPACITY})",
                color=ERROR_COLOR
            )
            await ctx.send(embed=embed)
            return

    # Create individual plantings for each seed
    base_id = f"{user_id}-{int(now*1000)}"
    for i in range(plant_amount):
        planting_id = f"{base_id}-{i}"
        user["plantings"][planting_id] = {
            "seed_type": seed_type,
            "start_time": now,
            "duration": PLANT_TIMES[seed_type],
            "amount": 1  # Each planting is 1 seed
        }

    # Update seeds inventory
    user["seeds"][seed_type] -= plant_amount
    save_data(data)

    # Calculate remaining planter capacity
    used_capacity = sum(p["amount"] for p in user["plantings"].values())
    remaining_capacity = MAX_PLANTER_CAPACITY - used_capacity

    embed = Embed(
        title=f"{EMOJI_MAP[seed_type]} Planting Started!",
        description=f"Planting {plant_amount} {seed_type.replace('_seed', '')} seed{'s' if plant_amount > 1 else ''}",
        color=EMBED_COLOR
    )
    embed.add_field(
        name="",
        value="Use `!garden` to track your plantings",
        inline=False
    )
    await ctx.send(embed=embed)

# Command: garden
@bot.command()
async def garden(ctx):
    user_id = str(ctx.author.id)
    data = load_data()
    now = time.time()

    if user_id not in data["users"] or not data["users"][user_id].get("plantings"):
        embed = Embed(
            title="🌱 Your Garden",
            description="No active plantings!",
            color=ERROR_COLOR
        )
        await ctx.send(embed=embed)
        return

    user = data["users"][user_id]
    plantings = []
    
    for planting_id, details in user["plantings"].items():
        seed_type = details["seed_type"]
        crop_name = seed_type.replace("_seed", "")
        elapsed = now - details["start_time"]
        remaining = details["duration"] - elapsed
        
        if remaining <= 0:
            status = "✅ Ready to harvest!"
        else:
            status = f"⏳ {int(remaining)}s remaining"
        
        plantings.append(
            f"{EMOJI_MAP[crop_name]} {crop_name.title()} x{details['amount']} - {status}"
        )

    embed = Embed(
        title=f"🌱 {ctx.author.display_name}'s Garden",
        description="\n".join(plantings) or "No active plantings",
        color=INFO_COLOR
    )
    await ctx.send(embed=embed)


# Command: harvest
@bot.command()
async def harvest(ctx):
    user_id = str(ctx.author.id)
    data = load_data()
    now = time.time()
    
    if user_id not in data["users"] or not data["users"][user_id].get("plantings"):
        embed = Embed(
            title="❌ Nothing to Harvest",
            description="No completed plantings!",
            color=ERROR_COLOR
        )
        await ctx.send(embed=embed)
        return

    user = data["users"][user_id]
    harvested = []
    
    for planting_id in list(user["plantings"].keys()):
        details = user["plantings"][planting_id]
        if now - details["start_time"] >= details["duration"]:
            seed_type = details["seed_type"]
            crop_name = seed_type.replace("_seed", "")
            
            # Find crop rarity
            crop_tier = next(
                (tier for tier, values in CROPS.items() 
                 if crop_name in values["crops"]),
                "common"
            )
            
            # Calculate yield
            tier_data = CROPS[crop_tier]
            base = tier_data["base_yield"]
            extra = random.randint(0, tier_data["max_extra"])
            # Multiply yield by the amount (should always be 1)
            total_yield = (base + extra) * details["amount"]
            
            # Update inventory
            if crop_name not in user["inventory"]:
                user["inventory"][crop_name] = 0
            user["inventory"][crop_name] += total_yield
            
            harvested.append(
                f"{EMOJI_MAP[crop_name]} {crop_name.title()} x{total_yield}"
            )
            del user["plantings"][planting_id]

    if not harvested:
        embed = Embed(
            title="❌ Nothing to Harvest",
            description="No completed plantings!",
            color=ERROR_COLOR
        )
    else:
        save_data(data)
        embed = Embed(
            title="💰 Harvest Complete!",
            description="\n".join(harvested),
            color=EMBED_COLOR
        )
        embed.set_footer(text="Check your inventory with !inv")

    await ctx.send(embed=embed)

# Handle all sell commands
@bot.command()
async def sell(ctx, *, args=None):
    """Handle selling of crops"""
    user_id = str(ctx.author.id)
    data = load_data()
    
    if user_id not in data["users"]:
        await ctx.send("You don't have anything to sell!")
        return

    if not args:
        await sell_all(ctx, data)
    else:
        await sell_specific(ctx, data, args)

# Command: sell
async def sell_all(ctx, data):
    user_id = str(ctx.author.id)
    user = data["users"][user_id]
    
    # Filter valid crops with prices
    valid_crops = {crop: qty for crop, qty in user["inventory"].items() if crop in PRICES}
    
    # Calculate total value
    total = sum(quantity * PRICES[crop] for crop, quantity in valid_crops.items())
    
    if total == 0:
        embed = Embed(
            title="🚫 Empty Inventory",
            description="You don't have anything to sell!",
            color=ERROR_COLOR
        )
        await ctx.send(embed=embed)
        return

    # Confirmation embed
    confirm_embed = Embed(
        title="⚠️ Confirm Bulk Sale",
        description=f"Are you sure you want to sell **ALL** crops?",
        color=INFO_COLOR
    )
    confirm_embed.add_field(
        name="Total Value",
        value=f"${total:,}",
        inline=True
    )
    confirm_embed.add_field(
        name="Confirmation",
        value="React with ✅ to confirm\nReact with ❌ to cancel",
        inline=True
    )
    confirm_embed.set_footer(text="This will clear your entire crop inventory!")
    
    confirm_msg = await ctx.send(embed=confirm_embed)
    await confirm_msg.add_reaction("✅")
    await confirm_msg.add_reaction("❌")

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ["✅", "❌"]

    try:
        reaction, _ = await bot.wait_for("reaction_add", timeout=30.0, check=check)
        
        if str(reaction.emoji) == "✅":
            # Reset inventory and add balance
            for crop in user["inventory"]:
                user["inventory"][crop] = 0
            user["balance"] += total
            save_data(data)
            
            success_embed = Embed(
                title="💰 Bulk Sale Complete!",
                description=f"Successfully sold all crops!",
                color=EMBED_COLOR
            )
            success_embed.add_field(
                name="Total Earned",
                value=f"${total:,}",
                inline=True
            )
            success_embed.add_field(
                name="New Balance",
                value=f"${user['balance']:,}",
                inline=True
            )
            await ctx.send(embed=success_embed)
            
        else:
            cancel_embed = Embed(
                title="🚫 Sale Canceled",
                description="Your crops remain in your inventory.",
                color=ERROR_COLOR
            )
            await ctx.send(embed=cancel_embed)

    except TimeoutError:
        timeout_embed = Embed(
            title="⏳ Sale Expired",
            description="Confirmation timed out after 30 seconds.",
            color=ERROR_COLOR
        )
        await ctx.send(embed=timeout_embed)

# Command: sell <crop> <amount>
async def sell_specific(ctx, data, args):
    user_id = str(ctx.author.id)
    user = data["users"][user_id]
    
    try:
        args = args.split()
        if len(args) not in [1, 2]:
            raise ValueError
        
        crop = args[0].lower()
        amount = int(args[1]) if len(args) == 2 else user["inventory"].get(crop, 0)
        
        if crop not in PRICES:  # Check against PRICES instead of CROPS
            embed = Embed(
                title="❌ Invalid Crop",
                description="That's not a sellable crop!",
                color=ERROR_COLOR
            )
            embed.add_field(
                name="Available Crops",
                value=", ".join(PRICES.keys()),
                inline=False
            )
            await ctx.send(embed=embed)
            return
            
        if amount <= 0:
            embed = Embed(
                title="❌ Invalid Amount",
                description="Amount must be a positive number!",
                color=ERROR_COLOR
            )
            await ctx.send(embed=embed)
            return
            
        if user["inventory"][crop] < amount:
            embed = Embed(
                title="❌ Insufficient Quantity",
                description=f"You only have {user['inventory'][crop]} {crop}!",
                color=ERROR_COLOR
            )
            await ctx.send(embed=embed)
            return

        # Process sale
        value = amount * PRICES[crop]
        user["inventory"][crop] -= amount
        user["balance"] += value
        save_data(data)
        
        embed = Embed(
            title=f"{EMOJI_MAP[crop]} Successful Sale!",
            description=f"Sold **{amount}** {crop.title()}",
            color=EMBED_COLOR
        )
        embed.add_field(
            name="Total Earned",
            value=f"${value:,}",
            inline=True
        )
        embed.add_field(
            name="New Balance",
            value=f"${user['balance']:,}",
            inline=True
        )
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

    except (ValueError, IndexError):
        embed = Embed(
            title="❌ Invalid Format",
            description="**Proper usage:**\n`!sell <crop> [amount]`",
            color=ERROR_COLOR
        )
        embed.add_field(
            name="Examples",
            value="`!sell wheat` - Sell all wheat\n`!sell apple 5` - Sell 5 apples",
            inline=False
        )
        await ctx.send(embed=embed)

# Command: Inventory
@bot.command(name="inventory", aliases=["inv"])
async def inventory(ctx, user: discord.Member = None):
    """Check your or another user's inventory"""
    target_user = user or ctx.author
    
    user_id = str(target_user.id)
    data = load_data()

    if user_id not in data["users"]:
        description = (f"{target_user.mention} hasn't farmed yet!" 
                      if user else "You haven't farmed yet! Use `!roll` to get started.")
        embed = Embed(
            title="🚜 Farming Inventory",
            description=description,
            color=ERROR_COLOR
        )
        await ctx.send(embed=embed)
        return

    user_data = data["users"][user_id]
    crops = user_data["inventory"]
    seeds = user_data["seeds"]
    balance = user_data.get("balance", 0)
    
    embed = Embed(
        title=f"🎒 {target_user.display_name}'s Inventory",
        color=INFO_COLOR
    )
    embed.add_field(
        name="💰 Balance",
        value=f"${balance:,}",
        inline=False
    )
    
    # Crops Section
    crop_items = "\n".join(
        [f"{EMOJI_MAP[crop]} {crop.title()}: {qty} (${PRICES[crop]}/ea)" 
         for crop, qty in crops.items() if qty > 0]
    ) or "No crops harvested"
    embed.add_field(
        name="🌾 Harvested Crops",
        value=crop_items,
        inline=False
    )
    
    # Seeds Section
    seed_items = "\n".join(
        [f"{EMOJI_MAP[seed]} {seed.replace('_', ' ').title()}: {qty}" 
         for seed, qty in seeds.items() if qty > 0]
    ) or "No seeds available"
    embed.add_field(
        name="🌱 Seed Inventory",
        value=seed_items,
        inline=False
    )
    
    embed.set_thumbnail(url=target_user.display_avatar.url)
    await ctx.send(embed=embed)

@inventory.error
async def inventory_error(ctx, error):
    if isinstance(error, commands.BadArgument):
        embed = Embed(
            title="❌ Invalid User",
            description="Couldn't find that user in this server!",
            color=ERROR_COLOR
        )
        embed.add_field(
            name="Valid Formats",
            value="• `!inv @Username`\n• `!inv DisplayName`",
            inline=False
        )
        await ctx.send(embed=embed)
    else:
        raise error

# Command: Leaderboard
@bot.command()
async def leaderboard(ctx):
    data = load_data()
    users = data["users"]

    sorted_users = sorted(
        users.items(),
        key=lambda x: x[1].get("balance", 0),
        reverse=True
    )[:10]

    embed = Embed(
        title="🏆 Wealth Leaderboard",
        description="Top 10 richest farmers",
        color=0xf1c40f  # Gold color
    )
    
    for idx, (user_id, stats) in enumerate(sorted_users, 1):
        try:
            # Get the user object
            user = await bot.fetch_user(int(user_id))
            # Get server-specific member (for nickname)
            member = ctx.guild.get_member(user.id)
            display_name = user.name
            total = stats.get("balance", 0)
            
            embed.add_field(
                name=f"{idx}. {display_name}",
                value=f"${total:,}",
                inline=False
            )
            
        except Exception as e:
            print(f"Error processing user {user_id}: {e}")
            continue  # Skip invalid users

    if not embed.fields:
        embed.description = "No farmers yet! Start with `!farm`"

    embed.set_footer(text="Keep farming to climb the ranks!")
    await ctx.send(embed=embed)


# Run the bot
token = get_token()
if token is None:
    print("Error: Could not read token from .env file")
else:
    bot.run(token)
