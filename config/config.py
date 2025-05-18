"""
Configuration module for The Farmer Discord Bot.
This module contains all the constants and configuration values used throughout the bot.
"""

# Color constants
class Colors:
    EMBED = 0x2ecc71  # Green theme
    ERROR = 0xe74c3c  # Red for errors
    INFO = 0x3498db   # Blue for info

# Game constants
class GameConstants:
    MAX_PLANTER_CAPACITY = 3
    ROLL_COOLDOWN = 3  # seconds
    CONFIRMATION_TIMEOUT = 30  # seconds
    LEADERBOARD_TIMEOUT = 60  # seconds
    USERS_PER_PAGE = 10
    BASE_LUCK_FACTOR = 1.0  # Base luck factor for rolls

# Shop configuration
class ShopConfig:
    PAGES = {
        "main": {
            "name": "Main Shop",
            "emoji": "🏪",
            "color": 0xFFA500,  # Orange
            "description": "Welcome to the shop! Select a category to browse items."
        },
        "items": {
            "name": "Items Shop",
            "emoji": "🛍️",
            "color": 0x9B59B6,  # Purple
            "description": "Various items to help with farming!"
        },
        "biomes": {
            "name": "Biome Shop",
            "emoji": "🌍",
            "color": 0x3498DB,  # Blue
            "description": "Unlock new biomes to expand your farming empire!"
        }
    }

# Item configuration
class ItemConfig:
    ITEMS = {
        "watering_can": {
            "name": "Watering Can",
            "shop_name": "x5 Watering Can",
            "emoji": "🚿",
            "price": 100,
            "description": "Makes ALL crops grow 50% faster while active",
            "effect": {
                "type": "growth_speed",
                "multiplier": 1.5,
                "duration": 60  # 1 minute in seconds
            }
        },
        "fertilizer": {
            "name": "Fertilizer",
            "shop_name": "x3 Fertilizer",
            "emoji": "🌱",
            "price": 150,
            "description": "Increases ALL crop yields by 25% while active",
            "effect": {
                "type": "yield_boost",
                "multiplier": 1.25,
                "duration": 300  # 5 minutes in seconds
            }
        },
        "magnifying_glass": {
            "name": "Magnifying Glass",
            "shop_name": "Magnifying Glass",
            "emoji": "🔍",
            "price": 250,
            "description": "Increases roll luck by 50% for 10 minutes",
            "effect": {
                "type": "luck_boost",
                "multiplier": 1.5,
                "duration": 600  # 10 minutes in seconds
            }
        }
    }

# Biome configuration
class BiomeConfig:
    BIOMES = {
        "grassland": {
            "emoji": "🌿",
            "color": 0x90EE90,  # Light green
            "capacity": GameConstants.MAX_PLANTER_CAPACITY,
            "unlock_cost": 0,  # Free/starter biome
            "capacity_upgrade_base_cost": 1000,  # Base cost for capacity upgrade
            "capacity_upgrade_multiplier": 2.0,  # Cost multiplier per upgrade
            "description": "The starter biome. Perfect for beginning farmers!",
            "locked": False  # Always unlocked
        },
        "desert": {
            "emoji": "🏜️",
            "color": 0xFFD700,  # Gold
            "capacity": GameConstants.MAX_PLANTER_CAPACITY,
            "unlock_cost": 5000,
            "capacity_upgrade_base_cost": 2000,
            "capacity_upgrade_multiplier": 2.2,
            "description": "A harsh environment that yields valuable crops.",
            "locked": True
        },
        "tundra": {
            "emoji": "❄️",
            "color": 0xADD8E6,  # Light blue
            "capacity": GameConstants.MAX_PLANTER_CAPACITY,
            "unlock_cost": 10000,
            "capacity_upgrade_base_cost": 3000,
            "capacity_upgrade_multiplier": 2.4,
            "description": "Cold and unforgiving, but rich in unique resources.",
            "locked": True
        },
        "wetlands": {
            "emoji": "💧",
            "color": 0x4169E1,  # Royal blue
            "capacity": GameConstants.MAX_PLANTER_CAPACITY,
            "unlock_cost": 25000,
            "capacity_upgrade_base_cost": 4000,
            "capacity_upgrade_multiplier": 2.6,
            "description": "A fertile region perfect for water-loving plants.",
            "locked": True
        },
        "hell": {
            "emoji": "🔥",
            "color": 0xFF4500,  # Orange red
            "capacity": GameConstants.MAX_PLANTER_CAPACITY,
            "unlock_cost": 50000,
            "capacity_upgrade_base_cost": 5000,
            "capacity_upgrade_multiplier": 3.0,
            "description": "The ultimate farming challenge with the highest rewards.",
            "locked": True
        }
    }

# Seed configuration
class SeedConfig:
    SEEDS = {
        "common": {
            "seeds": ["wheat_seed", "potato_seed"],
            "chance": 60
        },
        "uncommon": {
            "seeds": ["carrot_seed", "rice_seed"],
            "chance": 25
        },
        "rare": {
            "seeds": ["apple_seed", "orange_seed"],
            "chance": 10
        },
        "epic": {
            "seeds": ["kiwi_seed", "banana_seed", "starfruit_seed"],
            "chance": 3.75
        },
        "legendary": {
            "seeds": ["melon_seed", "grape_seed"],
            "chance": 1.25
        }
    }

    PLANT_TIMES = {
        "wheat_seed": 30,
        "potato_seed": 40,
        "rice_seed": 50,
        "carrot_seed": 60,
        "apple_seed": 120,
        "orange_seed": 150,
        "kiwi_seed": 240,
        "melon_seed": 360,
        "banana_seed": 220,
        "starfruit_seed": 250,
        "grape_seed": 380
    }

# Crop configuration
class CropConfig:
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
            "crops": ["kiwi", "banana", "starfruit"],
            "base_yield": 1,
            "max_extra": 2,
            "chance": 1.25
        },
        "legendary": {
            "crops": ["melon", "grape"],
            "base_yield": 1,
            "max_extra": 2,
            "chance": 0.5
        }
    }

    PRICES = {
        "wheat": 2,
        "potato": 3,
        "carrot": 4,
        "rice": 5,
        "apple": 10,
        "orange": 15,
        "kiwi": 25,
        "melon": 50,
        "banana": 30,
        "starfruit": 40,
        "grape": 75
    }

# Mutation configuration
class MutationConfig:
    MUTATIONS = {
        "golden": {
            "chance": 5.0,  # 5% chance
            "price_multiplier": 20,
            "emoji": "⭐"
        },
        "rainbow": {
            "chance": 0.5,  # 0.5% chance
            "price_multiplier": 50,
            "emoji": "🌈"
        }
    }

# Emoji configuration
class EmojiConfig:
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
        "banana": "🍌",
        "starfruit": "⭐",
        "grape": "🍇",

        # Seeds
        "wheat_seed": "🌾",
        "potato_seed": "🥔",
        "carrot_seed": "🥕",
        "rice_seed": "🍚",
        "apple_seed": "🍎",
        "orange_seed": "🍊",
        "kiwi_seed": "🥝",
        "melon_seed": "🍈",
        "banana_seed": "🍌",
        "starfruit_seed": "⭐",
        "grape_seed": "🍇"
    } 