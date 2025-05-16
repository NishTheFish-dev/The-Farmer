"""
Data configuration for The Farmer.
This module contains data-related configuration like file paths and database settings.
"""

from pathlib import Path

class DataConfig:
    """Configuration for data storage and management."""
    
    # Base data directory
    DATA_DIR = Path("data")
    
    # Farm data file
    FARM_DATA_FILE = DATA_DIR / "farm_data.json"
    
    # Default user data structure
    @staticmethod
    def get_default_user_data():
        """Get the default data structure for a new user."""
        from .config import BiomeConfig, CropConfig, SeedConfig
        
        return {
            "last_rolled": 0,
            "inventory": {
                crop: {"amount": 0, "mutations": {}} 
                for tier in CropConfig.CROPS.values() 
                for crop in tier["crops"]
            },
            "seeds": {
                seed: 0 
                for seed in SeedConfig.PLANT_TIMES.keys()
            },
            "plantings": {
                biome: {} 
                for biome in BiomeConfig.BIOMES.keys()
            },
            "balance": 0,
            "biomes": {
                biome: {
                    "unlocked": not BiomeConfig.BIOMES[biome]["locked"],
                    "capacity": BiomeConfig.BIOMES[biome]["capacity"]
                } for biome in BiomeConfig.BIOMES.keys()
            }
        } 