import discord
from discord.ext import commands
from utils.database import load_data
from utils.views import LeaderboardView

class Leaderboard(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def leaderboard(self, ctx):
        """View the richest farmers"""
        data = load_data()
        users = data["users"]

        sorted_users = sorted(
            users.items(),
            key=lambda x: x[1].get("balance", 0),
            reverse=True
        )

        view = LeaderboardView(sorted_users)
        embed = await view.create_embed(self.bot)
        view.message = await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(Leaderboard(bot)) 