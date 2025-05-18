import discord
from discord.ext import commands
from config import Colors

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="farmhelp", aliases=["fhelp"])
    async def farm_help(self, ctx):
        """Shows all available farming commands and their usage"""
        embed = discord.Embed(
            title="🌾 Farming Bot Commands",
            description="Here are all the available commands:",
            color=Colors.INFO
        )

        # Basic Commands
        basic_commands = (
            "`!roll` - Get random seeds (1s cooldown)\n"
            "`!set <biome>` - Set your preferred biome for planting\n"
            "`!unset` - Remove your preferred biome setting\n"
            "`!plant <biome> <seed> [amount]` - Plant seeds in a biome\n"
            "  Example: `!plant grassland wheat 2`\n"
            "`!garden [biome]` - View your gardens or a specific biome\n"
            "`!harvest [biome]` - Harvest all ready crops or from specific biome"
        )
        embed.add_field(
            name="🌱 Basic Commands",
            value=basic_commands,
            inline=False
        )

        # Shop & Upgrades
        shop_commands = (
            "`!shop` - View the main shop\n"
            "`!shop items` - View available items\n"
            "`!shop biomes` - View available biomes\n"
            "`!shop biomes <n>` - View specific biome upgrades\n"
            "`!buy item <name>` - Purchase an item\n"
            "`!buy <biome>` - Unlock a new biome\n"
            "`!buy <biome> capacity` - Upgrade biome capacity"
        )
        embed.add_field(
            name="🏪 Shop & Upgrades",
            value=shop_commands,
            inline=False
        )

        # Inventory & Economy
        inventory_commands = (
            "`!inventory` or `!inv` - View your inventory\n"
            "`!inv @User` - View another user's inventory\n"
            "`!use <item>` - Use an item from your inventory\n"
            "`!effects` - View your active effects\n"
            "`!sell <crop> <amount>` - Sell specific crops\n"
            "  Example: `!sell wheat 5`\n"
            "`!sell` - Sell all crops at once"
        )
        embed.add_field(
            name="💰 Inventory & Economy",
            value=inventory_commands,
            inline=False
        )

        # Leaderboard
        leaderboard_commands = (
            "`!leaderboard` - View the richest farmers"
        )
        embed.add_field(
            name="🏆 Leaderboard",
            value=leaderboard_commands,
            inline=False
        )

        embed.set_footer(text="Use !farmhelp or !fhelp to see this message again")
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Help(bot)) 