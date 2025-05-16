"""
Database utilities for The Farmer.
This module handles all database operations like loading and saving data.
"""

import json
from config import DataConfig

def load_data():
    """Load farming data from JSON file"""
    try:
        if DataConfig.FARM_DATA_FILE.exists():
            with open(DataConfig.FARM_DATA_FILE, "r") as f:
                return json.load(f)
        return {"users": {}}
    except Exception as e:
        print(f"Error loading data: {e}")
        return {"users": {}}

def save_data(data):
    """Save farming data to JSON file"""
    try:
        # Ensure data directory exists
        DataConfig.DATA_DIR.mkdir(exist_ok=True)
        
        with open(DataConfig.FARM_DATA_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Error saving data: {e}")

def get_user_data(user_id, data):
    """Get user data, creating default structure if needed"""
    if user_id not in data["users"]:
        data["users"][user_id] = DataConfig.get_default_user_data()
        save_data(data)
    return data["users"][user_id] 