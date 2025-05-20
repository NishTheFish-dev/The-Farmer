import discord
from discord.ext import commands
from utils.database import load_data, save_data, get_user_data
from utils.embeds import error_embed, success_embed
from config import Colors

class Skills(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.skills = {
            "grow_rate": {
                "name": "Grow Rate",
                "description": "Increase your grow rate by 0.5% per level",
                "max_level": 20,
                "cost_per_level": 10,
                "effect_per_level": 0.005,  # 0.5%
                "max_effect": 0.10  # 10%
            },
            "crop_yield": {
                "name": "Crop Yield",
                "description": "Increase your crop yield by 0.5% per level",
                "max_level": 20,
                "cost_per_level": 10,
                "effect_per_level": 0.005,  # 0.5%
                "max_effect": 0.10  # 10%
            },
            "roll_luck": {
                "name": "Roll Luck",
                "description": "Increase your roll luck by 1% per level",
                "max_level": 20,
                "cost_per_level": 10,
                "effect_per_level": 0.01,  # 1%
                "max_effect": 0.20  # 20%
            },
            "xp_per_harvest": {
                "name": "XP per Harvest",
                "description": "Increase your XP per harvest by 0.5 per level",
                "max_level": 10,
                "cost_per_level": 10,
                "effect_per_level": 0.5,
                "max_effect": 5.0
            }
        }
        
        # Add shortcuts for skills
        self.skill_shortcuts = {
            "gr": "grow_rate",
            "cy": "crop_yield",
            "rl": "roll_luck",
            "xp": "xp_per_harvest"
        }

    def get_skill_level(self, user_data: dict, skill: str) -> int:
        """Get the current level of a skill"""
        if "skills" not in user_data:
            user_data["skills"] = {}
        return user_data["skills"].get(skill, 0)

    def get_skill_effect(self, user_data: dict, skill: str) -> float:
        """Calculate the current effect of a skill"""
        level = self.get_skill_level(user_data, skill)
        skill_info = self.skills[skill]
        return min(level * skill_info["effect_per_level"], skill_info["max_effect"])

    def get_upgrade_cost(self, user_data: dict, skill: str) -> int:
        """Calculate the cost to upgrade a skill"""
        current_level = self.get_skill_level(user_data, skill)
        if current_level >= self.skills[skill]["max_level"]:
            return -1
        return self.skills[skill]["cost_per_level"] * (current_level + 1)

    @commands.command()
    async def skills(self, ctx):
        """View your skills and XP"""
        user_id = str(ctx.author.id)
        data = load_data()
        user = get_user_data(user_id, data)
        
        # Initialize skills if they don't exist
        if "skills" not in user:
            user["skills"] = {}
            for skill in self.skills:
                user["skills"][skill] = 0
            save_data(data)
        
        # Initialize XP if it doesn't exist
        if "xp" not in user:
            user["xp"] = 0
            save_data(data)
        
        embed = discord.Embed(
            title="🌳 Skill Tree",
            description=f"Current XP: {user['xp']:.1f}",
            color=Colors.EMBED
        )
        
        for skill_id, skill in self.skills.items():
            current_level = user["skills"].get(skill_id, 0)
            current_effect = self.get_skill_effect(user, skill_id)
            upgrade_cost = self.get_upgrade_cost(user, skill_id)
            
            # Format the effect text
            effect_text = f"{current_effect * 100:.1f}%"
            if skill_id == "xp_per_harvest":
                effect_text = f"+{current_effect:.1f}"
            
            # Add skill info to embed
            embed.add_field(
                name=f"{skill['name']}",
                value=f"{skill['description']}\nLevel {current_level}/{skill['max_level']} ({effect_text})\nUpgrade Cost: {upgrade_cost:.1f} XP",
                inline=False
            )
        
        # Add shortcuts info
        shortcuts_text = "\n".join([f"`{shortcut}` - {self.skills[skill]['name']}" for shortcut, skill in self.skill_shortcuts.items()])
        embed.add_field(
            name="Shortcuts",
            value=f"Use these shortcuts to upgrade skills:\n{shortcuts_text}",
            inline=False
        )
        
        await ctx.send(embed=embed)

    @commands.command()
    async def upgrade(self, ctx, skill: str = None):
        """Upgrade a skill using XP"""
        if not skill:
            await ctx.send(embed=error_embed(
                "❌ Missing Arguments",
                "**Usage:** `!upgrade <skill>`\nExample: `!upgrade grow_rate` or `!upgrade gr`"
            ))
            return

        skill = skill.lower()
        # Check if the input is a shortcut
        if skill in self.skill_shortcuts:
            skill = self.skill_shortcuts[skill]
        
        if skill not in self.skills:
            await ctx.send(embed=error_embed(
                "❌ Invalid Skill",
                f"Available skills:\n" + 
                "\n".join([f"`{s}` - {self.skills[s]['name']}" for s in self.skills.keys()]) +
                "\n\nShortcuts:\n" +
                "\n".join([f"`{shortcut}` - {self.skills[skill]['name']}" for shortcut, skill in self.skill_shortcuts.items()])
            ))
            return

        user_id = str(ctx.author.id)
        data = load_data()
        user = get_user_data(user_id, data)

        # Initialize skills and XP if they don't exist
        if "skills" not in user:
            user["skills"] = {}
        if "xp" not in user:
            user["xp"] = 0

        upgrade_cost = self.get_upgrade_cost(user, skill)
        if upgrade_cost == -1:
            await ctx.send(embed=error_embed(
                "✨ Max Level",
                f"{self.skills[skill]['name']} is already at maximum level!"
            ))
            return

        if user["xp"] < upgrade_cost:
            await ctx.send(embed=error_embed(
                "❌ Insufficient XP",
                f"You need {upgrade_cost:.1f} XP to upgrade {self.skills[skill]['name']}.\nYou have {user['xp']:.1f} XP."
            ))
            return

        # Perform the upgrade
        user["xp"] -= upgrade_cost
        user["skills"][skill] = user["skills"].get(skill, 0) + 1
        save_data(data)

        new_level = user["skills"][skill]
        new_effect = self.get_skill_effect(user, skill)
        effect_text = f"{new_effect * 100:.1f}%"
        if skill == "xp_per_harvest":
            effect_text = f"+{new_effect:.1f}"

        await ctx.send(embed=success_embed(
            "✨ Skill Upgraded",
            f"{self.skills[skill]['name']} upgraded to level {new_level}!\nCurrent effect: {effect_text}"
        ))

async def setup(bot):
    await bot.add_cog(Skills(bot)) 