import discord
from discord.ext import commands
import time
import uuid
from utils.database import load_data, save_data, get_user_data
from config import ItemConfig, Colors
from utils.embeds import error_embed, success_embed

class Items(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def use(self, ctx, *, item_name: str):
        """Use an item from your inventory"""
        user_id = str(ctx.author.id)
        data = load_data()
        now = time.time()
        
        user = get_user_data(user_id, data)
        
        # Initialize items inventory if it doesn't exist
        if "items" not in user:
            user["items"] = {}
        
        # Initialize active effects if they don't exist
        if "active_effects" not in user:
            user["active_effects"] = {}
        
        # Clean up item name
        item_name = item_name.lower().replace(" ", "_")
        
        # Check if item exists
        if item_name not in ItemConfig.ITEMS:
            await ctx.send(embed=error_embed(
                "❌ Invalid Item",
                f"That item doesn't exist! Use `!shop items` to see available items."
            ))
            return
        
        # Check if user has the item
        if item_name not in user["items"] or user["items"][item_name] <= 0:
            await ctx.send(embed=error_embed(
                "❌ No Item",
                f"You don't have any {ItemConfig.ITEMS[item_name]['name']}!"
            ))
            return
        
        # Get item configuration
        item_config = ItemConfig.ITEMS[item_name]
        
        # Create effect
        effect_id = str(uuid.uuid4())
        effect = {
            "type": item_config["effect"]["type"],
            "multiplier": item_config["effect"]["multiplier"],
            "start_time": now,
            "end_time": now + item_config["effect"]["duration"],
            "name": item_config["name"],
            "emoji": item_config["emoji"]
        }
        
        # Add effect
        user["active_effects"][effect_id] = effect
        
        # Remove one item from inventory
        user["items"][item_name] -= 1
        if user["items"][item_name] <= 0:
            del user["items"][item_name]
        
        save_data(data)
        
        # Send success message
        await ctx.send(embed=success_embed(
            f"{item_config['emoji']} Item Used!",
            f"Successfully used {item_config['name']}!\n" +
            f"Effect: {item_config['description']}\n" +
            f"Duration: {item_config['effect']['duration']} seconds\n\n" +
            "Use `!effects` to view your active effects!"
        ))

async def setup(bot):
    await bot.add_cog(Items(bot)) 