import discord
from discord.ext import commands
import random
import time
from utils.database import load_data, save_data, get_user_data
from config import (
    BiomeConfig,
    SeedConfig,
    CropConfig,
    MutationConfig,
    EmojiConfig,
    Colors,
    GameConstants,
    ItemConfig
)
from utils.embeds import error_embed, success_embed, confirmation_embed

class Farming(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_active_effects(self, user_data: dict, now: float) -> dict:
        """Get all active effects and clean up expired ones"""
        if "active_effects" not in user_data:
            user_data["active_effects"] = {}
        
        # Clean up expired effects
        expired = []
        for effect_id, effect in user_data["active_effects"].items():
            if now > effect["end_time"]:
                expired.append(effect_id)
        
        for effect_id in expired:
            del user_data["active_effects"][effect_id]
        
        return user_data["active_effects"]

    def get_current_luck_factor(self, user_data: dict, now: float) -> float:
        """Calculate current luck factor based on active effects and skills"""
        luck_factor = GameConstants.BASE_LUCK_FACTOR
        active_effects = self.get_active_effects(user_data, now)
        
        # Apply skill bonus
        if "skills" in user_data and "roll_luck" in user_data["skills"]:
            skill_level = user_data["skills"]["roll_luck"]
            luck_factor *= (1 + min(skill_level * 0.01, 0.20))  # 1% per level, max 20%
        
        # Apply active effects
        for effect in active_effects.values():
            if effect["type"] == "luck_boost":
                luck_factor *= effect["multiplier"]
        
        return luck_factor

    def get_growth_speed_multiplier(self, user_data: dict, now: float) -> float:
        """Calculate current growth speed multiplier based on active effects and skills"""
        multiplier = 1.0
        active_effects = self.get_active_effects(user_data, now)
        
        # Apply skill bonus
        if "skills" in user_data and "grow_rate" in user_data["skills"]:
            skill_level = user_data["skills"]["grow_rate"]
            multiplier *= (1 + min(skill_level * 0.005, 0.10))  # 0.5% per level, max 10%
        
        # Apply active effects
        for effect in active_effects.values():
            if effect["type"] == "growth_speed":
                multiplier = max(multiplier, effect["multiplier"])
                break
        
        return multiplier

    def has_active_fertilizer(self, user_data: dict, now: float) -> bool:
        """Check if there's an active fertilizer effect"""
        active_effects = self.get_active_effects(user_data, now)
        for effect in active_effects.values():
            if effect["type"] == "yield_boost":
                return True
        return False

    def get_yield_multiplier(self, user_data: dict, now: float, is_fertilized: bool = False) -> float:
        """Calculate current yield multiplier based on active effects, fertilized status, and skills"""
        multiplier = 1.0
        
        # Apply skill bonus
        if "skills" in user_data and "crop_yield" in user_data["skills"]:
            skill_level = user_data["skills"]["crop_yield"]
            multiplier *= (1 + min(skill_level * 0.005, 0.10))  # 0.5% per level, max 10%
        
        # If the crop was fertilized when planted, always apply the fertilizer multiplier
        if is_fertilized:
            # Get the fertilizer multiplier from config
            fertilizer_multiplier = ItemConfig.ITEMS["fertilizer"]["effect"]["multiplier"]
            multiplier *= fertilizer_multiplier
        
        # Check for other active yield effects
        active_effects = self.get_active_effects(user_data, now)
        for effect in active_effects.values():
            if effect["type"] == "yield_boost":
                multiplier *= effect["multiplier"]
        
        return multiplier

    def calculate_growth_progress(self, planting: dict, now: float, growth_multiplier: float) -> float:
        """Calculate growth progress for a planting, accounting for dynamic growth speed"""
        base_duration = planting["duration"]
        elapsed = now - planting["start_time"]
        
        # Apply current growth multiplier to elapsed time
        effective_elapsed = elapsed * growth_multiplier
        
        return effective_elapsed / base_duration

    def calculate_xp_gain(self, user_data: dict, seed_amount: int) -> float:
        """Calculate XP gain from harvesting crops (1 XP per seed planted)"""
        base_xp = 1.0  # Base XP per seed planted
        
        # Apply XP per harvest skill bonus
        if "skills" in user_data and "xp_per_harvest" in user_data["skills"]:
            skill_level = user_data["skills"]["xp_per_harvest"]
            base_xp += min(skill_level * 0.5, 5.0)  # +0.5 per level, max +5
        
        return base_xp * seed_amount

    @commands.command()
    async def set(self, ctx, biome: str = None):
        """Set your preferred biome for planting"""
        if not biome:
            await ctx.send(embed=error_embed(
                "❌ Missing Arguments",
                "**Usage:** `!set <biome>`\nExample: `!set grassland`"
            ))
            return

        biome = biome.lower()
        if biome not in BiomeConfig.BIOMES:
            await ctx.send(embed=error_embed(
                "❌ Invalid Biome",
                f"Available biomes:\n" + 
                "\n".join([f"{BiomeConfig.BIOMES[b]['emoji']} {b}" for b in BiomeConfig.BIOMES.keys()])
            ))
            return

        user_id = str(ctx.author.id)
        data = load_data()
        user = get_user_data(user_id, data)

        # Check if biome is unlocked
        if not user["biomes"][biome]["unlocked"] and biome != "grassland":
            await ctx.send(embed=error_embed(
                "🔒 Biome Locked",
                f"You haven't unlocked the {biome} biome yet!\nUse `!shop biomes` to view unlock costs."
            ))
            return

        user["preferred_biome"] = biome
        save_data(data)

        await ctx.send(embed=success_embed(
            f"{BiomeConfig.BIOMES[biome]['emoji']} Biome Set",
            f"Your preferred biome has been set to {biome}.\nYou can now use `!plant <seed> [amount]` without specifying the biome!"
        ))

    @commands.command()
    async def unset(self, ctx):
        """Remove your preferred biome setting"""
        user_id = str(ctx.author.id)
        data = load_data()
        user = get_user_data(user_id, data)

        if user["preferred_biome"] is None:
            await ctx.send(embed=error_embed(
                "❌ No Biome Set",
                "You don't have a preferred biome set!"
            ))
            return

        old_biome = user["preferred_biome"]
        user["preferred_biome"] = None
        save_data(data)

        await ctx.send(embed=success_embed(
            "🔄 Biome Unset",
            f"Your preferred biome ({old_biome}) has been unset.\nYou'll need to specify the biome when using `!plant` again."
        ))

    @commands.command()
    async def roll(self, ctx):
        """Roll for seeds"""
        user_id = str(ctx.author.id)
        data = load_data()
        now = time.time()
        
        user = get_user_data(user_id, data)
        time_since_last = now - user["last_rolled"]

        # 1 second cooldown
        if time_since_last < 1:
            remaining = 1 - time_since_last
            await ctx.send(embed=error_embed(
                "⏳ Rolling Cooldown",
                f"You need to wait {int(remaining)} seconds!"
            ))
            return

        seed, amount, rarity = self.get_random_seed()
        user["last_rolled"] = now
        user["seeds"][seed] = user["seeds"].get(seed, 0) + amount
        save_data(data)

        await ctx.send(embed=success_embed(
            f"{EmojiConfig.EMOJI_MAP[seed]} {rarity.title()} Seed Roll!",
            f"You obtained **{amount}** {seed.replace('_', ' ').title()}!"
        ))

    @commands.command()
    async def plant(self, ctx, arg1: str = None, arg2: str = None, arg3: int = None):
        """Plant seeds in a biome"""
        user_id = str(ctx.author.id)
        data = load_data()
        now = time.time()
        
        user = get_user_data(user_id, data)
        # Handle case where preferred_biome doesn't exist in user data
        preferred_biome = user.get("preferred_biome")

        # Check for active fertilizer effect
        is_fertilized = self.has_active_fertilizer(user, now)

        # Handle "plant all" command
        if arg1 and arg1.lower() == "all":
            if preferred_biome:
                await self.plant_all_seeds(ctx, preferred_biome, user, data, now, is_fertilized)
            else:
                await ctx.send(embed=error_embed(
                    "❌ No Biome Set",
                    "You need to set a preferred biome with `!set <biome>` first!"
                ))
            return
        elif arg2 and arg2.lower() == "all":
            biome = arg1.lower()
            if biome not in BiomeConfig.BIOMES:
                await ctx.send(embed=error_embed(
                    "❌ Invalid Biome",
                    f"Available biomes:\n" + 
                    "\n".join([f"{BiomeConfig.BIOMES[b]['emoji']} {b}" for b in BiomeConfig.BIOMES.keys()])
                ))
                return
            
            # Check if biome is unlocked
            if not user["biomes"][biome]["unlocked"] and biome != "grassland":
                await ctx.send(embed=error_embed(
                    "🔒 Biome Locked",
                    f"You haven't unlocked the {biome} biome yet!\nUse `!shop biomes` to view unlock costs."
                ))
                return
                
            await self.plant_all_seeds(ctx, biome, user, data, now, is_fertilized)
            return

        # Parse arguments based on whether a preferred biome is set
        if preferred_biome is not None:
            # If preferred biome is set, first arg is seed type
            seed_type = arg1
            amount = arg2
            biome = preferred_biome
            if amount is not None:
                try:
                    amount = int(amount)
                except ValueError:
                    amount = None
        else:
            # If no preferred biome, first arg is biome
            biome = arg1
            seed_type = arg2
            amount = arg3

        if not biome or not seed_type:
            usage = "`!plant <seed> [amount]`" if preferred_biome else "`!plant <biome> <seed> [amount]`"
            example = f"`!plant wheat 2`" if preferred_biome else "`!plant grassland wheat 2`"
            await ctx.send(embed=error_embed(
                "❌ Missing Arguments",
                f"**Usage:** {usage}\nExample: {example}"
            ))
            return

        biome = biome.lower()
        seed_type = seed_type.lower() + "_seed"

        # Validate biome
        if biome not in BiomeConfig.BIOMES:
            await ctx.send(embed=error_embed(
                "❌ Invalid Biome",
                f"Available biomes:\n" + 
                "\n".join([f"{BiomeConfig.BIOMES[b]['emoji']} {b}" for b in BiomeConfig.BIOMES.keys()])
            ))
            return

        # Check if biome is unlocked
        if not user["biomes"][biome]["unlocked"] and biome != "grassland":
            await ctx.send(embed=error_embed(
                "🔒 Biome Locked",
                f"You haven't unlocked the {biome} biome yet!\nUse `!shop biomes` to view unlock costs."
            ))
            return

        # Validation
        if seed_type not in SeedConfig.PLANT_TIMES:
            await ctx.send(embed=error_embed(
                "❌ Invalid Seed Type",
                f"`{seed_type.replace('_seed', '')}` isn't a plantable seed!"
            ))
            return

        available_seeds = user["seeds"].get(seed_type, 0)
        if available_seeds <= 0:
            await ctx.send(embed=error_embed(
                "❌ No Seeds Available",
                f"You don't have any {seed_type.replace('_seed', '')} seeds!"
            ))
            return

        # Calculate remaining planter capacity
        used_capacity = len(user["plantings"][biome])
        current_capacity = user["biomes"][biome]["capacity"]
        remaining_capacity = current_capacity - used_capacity

        # Determine planting amount
        if amount is None:
            plant_amount = min(available_seeds, remaining_capacity)
        else:
            plant_amount = min(amount, available_seeds, remaining_capacity)

        if amount is not None and amount <= 0:
            await ctx.send(embed=error_embed(
                "❌ Invalid Planting",
                "Can't plant 0 or negative seeds!"
            ))
            return

        if plant_amount <= 0:
            await ctx.send(embed=error_embed(
                "❌ Garden Full",
                f"Not enough space in your {biome} garden! (Capacity: {current_capacity}, Used: {used_capacity})"
            ))
            return

        # Create individual plantings
        base_id = f"{user_id}-{int(now*1000)}"
        for i in range(plant_amount):
            planting_id = f"{base_id}-{i}"
            user["plantings"][biome][planting_id] = {
                "seed_type": seed_type,
                "start_time": now,
                "duration": SeedConfig.PLANT_TIMES[seed_type],
                "amount": 1,
                "is_fertilized": is_fertilized  # Mark if planted during fertilizer effect
            }

        # Update seeds inventory
        user["seeds"][seed_type] -= plant_amount
        save_data(data)

        # Calculate updated capacity after planting
        updated_used_capacity = len(user["plantings"][biome])

        # Add fertilizer status to message if active
        status_msg = ""
        if is_fertilized:
            status_msg = "\nPlanted with Fertilizer effect active!"

        await ctx.send(embed=success_embed(
            f"{BiomeConfig.BIOMES[biome]['emoji']} Planting Started!",
            f"Planting {plant_amount} {seed_type.replace('_seed', '')} seed{'s' if plant_amount > 1 else ''} in {biome}\n" +
            f"Plots used: {updated_used_capacity}/{current_capacity}" +
            status_msg +
            f"\nUse `!garden {biome}` to track your plantings"
        ))

    @commands.command()
    async def garden(self, ctx, biome: str = None):
        """View your gardens"""
        user_id = str(ctx.author.id)
        data = load_data()
        now = time.time()

        user = get_user_data(user_id, data)
        # Handle case where preferred_biome doesn't exist in user data
        preferred_biome = user.get("preferred_biome")

        # Get current growth multiplier for progress calculation
        growth_multiplier = self.get_growth_speed_multiplier(user, now)

        # If no biome specified, try to use preferred biome
        if not biome and preferred_biome:
            biome = preferred_biome

        # If still no biome specified, show overview
        if not biome:
            embed = discord.Embed(
                title=f"🌱 {ctx.author.display_name}'s Gardens Overview",
                description="Select a biome to view detailed plantings:",
                color=Colors.EMBED
            )
            
            for biome_name, biome_data in BiomeConfig.BIOMES.items():
                if user["biomes"][biome_name]["unlocked"]:
                    active_plantings = len(user["plantings"][biome_name])
                    capacity = user["biomes"][biome_name]["capacity"]
                    is_preferred = biome_name == preferred_biome
                    prefix = "✨ " if is_preferred else ""
                    embed.add_field(
                        name=f"{prefix}{biome_data['emoji']} {biome_name.title()}",
                        value=f"`!garden {biome_name}`\n{active_plantings}/{capacity} plots used",
                        inline=True
                    )
                elif biome_name == "grassland":
                    capacity = user["biomes"][biome_name]["capacity"]
                    active_plantings = len(user["plantings"][biome_name])
                    is_preferred = biome_name == preferred_biome
                    prefix = "✨ " if is_preferred else ""
                    embed.add_field(
                        name=f"{prefix}{biome_data['emoji']} {biome_name.title()}",
                        value=f"`!garden {biome_name}`\n{active_plantings}/{capacity} plots used",
                        inline=True
                    )
                else:
                    embed.add_field(
                        name=f"{biome_data['emoji']} {biome_name.title()}",
                        value="🔒 Locked\nUnlock in shop: `!shop biomes`",
                        inline=True
                    )
            
            if preferred_biome:
                embed.set_footer(text=f"✨ = Preferred Biome ({preferred_biome})")
            
            await ctx.send(embed=embed)
            return

        # Show specific biome garden
        plantings = []
        biome_data = BiomeConfig.BIOMES[biome]
        
        for planting_id, details in user["plantings"][biome].items():
            seed_type = details["seed_type"]
            crop_name = seed_type.replace("_seed", "")
            
            # Calculate progress using dynamic growth speed
            progress = self.calculate_growth_progress(details, now, growth_multiplier)
            
            if progress >= 1.0:
                status = "✅ Ready to harvest!"
            else:
                remaining = int((1.0 - progress) * details["duration"] / growth_multiplier)
                status = f"⏳ {remaining}s remaining"
            
            plantings.append(
                f"{EmojiConfig.EMOJI_MAP[crop_name]} {crop_name.title()} x{details['amount']} - {status}"
            )

        embed = discord.Embed(
            title=f"{biome_data['emoji']} {ctx.author.display_name}'s {biome.title()} Garden",
            description="\n".join(plantings) or f"No active plantings in {biome} garden",
            color=biome_data['color']
        )
        
        used_capacity = len(user["plantings"][biome])
        current_capacity = user["biomes"][biome]["capacity"]
        embed.add_field(
            name="Garden Capacity",
            value=f"{used_capacity}/{current_capacity} plots used",
            inline=False
        )
        
        # Show active effects if any
        active_effects = self.get_active_effects(user, now)
        if active_effects:
            effects_text = []
            for effect in active_effects.values():
                remaining = int(effect["end_time"] - now)
                effects_text.append(f"{effect['emoji']} {effect['name']} - ⏳ {remaining}s")
            
            embed.add_field(
                name="Active Effects",
                value="\n".join(effects_text),
                inline=False
            )
        
        await ctx.send(embed=embed)

    @commands.command()
    async def harvest(self, ctx, biome: str = None):
        """Harvest your crops"""
        user_id = str(ctx.author.id)
        data = load_data()
        now = time.time()
        
        user = get_user_data(user_id, data)
        
        # Handle biome selection
        if biome:
            biome = biome.lower()
            if biome not in BiomeConfig.BIOMES:
                await ctx.send(embed=error_embed(
                    "❌ Invalid Biome",
                    f"Available biomes:\n" + 
                    "\n".join([f"{BiomeConfig.BIOMES[b]['emoji']} {b}" for b in BiomeConfig.BIOMES.keys()])
                ))
                return
        else:
            biome = user.get("preferred_biome")
            if not biome:
                await ctx.send(embed=error_embed(
                    "❌ No Biome Specified",
                    "Please specify a biome or set a preferred biome using `!set <biome>`"
                ))
                return

        # Check if biome is unlocked
        if not user["biomes"][biome]["unlocked"] and biome != "grassland":
            await ctx.send(embed=error_embed(
                "🔒 Biome Locked",
                f"You haven't unlocked the {biome} biome yet!\nUse `!shop biomes` to view unlock costs."
            ))
            return

        # Harvest crops
        harvested, total_xp_gained = await self.harvest_from_biome(user, biome, now)
        
        if not harvested:
            await ctx.send(embed=error_embed(
                "🌱 Nothing to Harvest",
                f"You don't have any ready crops in the {biome} biome!"
            ))
            return

        # Create harvest message
        summary_lines = []
        for item in harvested:
            summary_lines.append(
                f"{EmojiConfig.EMOJI_MAP[item['crop']]} {item['crop'].replace('_', ' ').title()} x{item['amount']}"
            )

        embed = discord.Embed(
            title=f"{BiomeConfig.BIOMES[biome]['emoji']} Harvest Complete!",
            description=f"Successfully harvested:\n" + "\n".join(summary_lines),
            color=Colors.EMBED
        )

        if total_xp_gained > 0:
            embed.add_field(
                name="✨ XP Gained",
                value=f"{total_xp_gained:.1f}",
                inline=False
            )

        save_data(data)
        await ctx.send(embed=embed)

    def get_random_seed(self):
        """Get a random seed based on rarity tiers and luck factor."""
        user_id = str(self.bot.user.id)  # Get the current user's ID
        data = load_data()
        now = time.time()
        user = get_user_data(user_id, data)
        
        # Get current luck factor
        luck_factor = self.get_current_luck_factor(user, now)
        
        # Apply luck factor to roll chances
        roll = random.uniform(0, 100)
        roll *= luck_factor  # Higher luck means higher effective roll
        
        cumulative = 0
        selected_tier = None
        
        for tier, values in SeedConfig.SEEDS.items():
            cumulative += values["chance"]
            if roll <= cumulative:
                selected_tier = tier
                break
        
        # If no tier was selected (due to high luck), pick legendary
        if selected_tier is None:
            selected_tier = "legendary"
        
        seed = random.choice(SeedConfig.SEEDS[selected_tier]["seeds"])
        return seed, 1, selected_tier

    async def harvest_from_biome(self, user, biome, now):
        """Harvest crops from a specific biome"""
        plantings = user["plantings"][biome]
        harvested = []
        total_xp_gained = 0

        # Initialize inventory if it doesn't exist
        if "inventory" not in user:
            user["inventory"] = {}

        for planting_id, planting in list(plantings.items()):
            if self.calculate_growth_progress(planting, now, self.get_growth_speed_multiplier(user, now)) >= 1.0:
                seed_type = planting["seed_type"]
                crop_type = seed_type.replace("_seed", "")
                amount = planting["amount"]
                is_fertilized = planting.get("is_fertilized", False)

                # Find crop tier and base yield
                crop_tier = next(
                    (tier for tier, values in CropConfig.CROPS.items() 
                     if crop_type in values["crops"]),
                    "common"  # Default to common if not found
                )
                base_yield = CropConfig.CROPS[crop_tier]["base_yield"]
                yield_multiplier = self.get_yield_multiplier(user, now, is_fertilized)
                final_yield = int(base_yield * amount * yield_multiplier)

                # Initialize crop in inventory if it doesn't exist
                if crop_type not in user["inventory"]:
                    user["inventory"][crop_type] = {"amount": 0, "mutations": {}}
                elif isinstance(user["inventory"][crop_type], int):
                    # Convert old format to new format
                    old_amount = user["inventory"][crop_type]
                    user["inventory"][crop_type] = {"amount": old_amount, "mutations": {}}

                # Add to inventory
                user["inventory"][crop_type]["amount"] += final_yield

                # Calculate and add XP (1 XP per seed planted)
                xp_gained = self.calculate_xp_gain(user, amount)  # Pass amount instead of final_yield
                if "xp" not in user:
                    user["xp"] = 0
                user["xp"] += xp_gained
                total_xp_gained += xp_gained

                harvested.append({
                    "crop": crop_type,
                    "amount": final_yield,
                    "xp": xp_gained
                })

                # Remove the planting
                del plantings[planting_id]

        return harvested, total_xp_gained

    async def plant_all_seeds(self, ctx, biome: str, user_data: dict, data: dict, now: float, is_fertilized: bool):
        """Plant all available seeds in a biome, prioritizing rarest seeds first"""
        # Get available planter capacity
        used_capacity = len(user_data["plantings"][biome])
        current_capacity = user_data["biomes"][biome]["capacity"]
        remaining_capacity = current_capacity - used_capacity

        if remaining_capacity <= 0:
            await ctx.send(embed=error_embed(
                "❌ No Space Available",
                f"Your {biome} planters are full! Use `!harvest {biome}` to free up space."
            ))
            return

        # Get all seed types sorted by rarity (legendary to common)
        rarity_order = ["legendary", "epic", "rare", "uncommon", "common"]
        all_seeds = []
        for rarity in rarity_order:
            all_seeds.extend(SeedConfig.SEEDS[rarity]["seeds"])

        # Track what we're going to plant
        to_plant = []
        spaces_used = 0

        # Try to plant seeds in order of rarity
        for seed_type in all_seeds:
            if spaces_used >= remaining_capacity:
                break

            available_seeds = user_data["seeds"].get(seed_type, 0)
            if available_seeds > 0:
                plant_amount = min(available_seeds, remaining_capacity - spaces_used)
                if plant_amount > 0:
                    # Generate unique IDs for each planting
                    for _ in range(plant_amount):
                        planting_id = f"{ctx.author.id}-{now}-{spaces_used}"
                        user_data["plantings"][biome][planting_id] = {
                            "seed_type": seed_type,
                            "start_time": now,
                            "duration": SeedConfig.PLANT_TIMES[seed_type],
                            "amount": 1,
                            "is_fertilized": is_fertilized  # Mark if planted during fertilizer effect
                        }
                        spaces_used += 1
                    
                    # Update seed count
                    user_data["seeds"][seed_type] -= plant_amount
                    to_plant.append(f"{EmojiConfig.EMOJI_MAP[seed_type]} {seed_type.replace('_seed', '').title()}: {plant_amount}")

        if not to_plant:
            await ctx.send(embed=error_embed(
                "❌ No Seeds Available",
                "You don't have any seeds to plant!"
            ))
            return

        save_data(data)
        
        # Add fertilizer status to message if active
        status_msg = ""
        if is_fertilized:
            status_msg = "\nPlanted with Fertilizer effect active!"

        # Send success message
        await ctx.send(embed=success_embed(
            f"{BiomeConfig.BIOMES[biome]['emoji']} Mass Planting Success!",
            f"Successfully planted in {biome}:\n" + "\n".join(to_plant) +
            f"\n\nPlots used: {spaces_used}/{remaining_capacity}" +
            status_msg
        ))

    @commands.command()
    async def effects(self, ctx):
        """View your active effects"""
        user_id = str(ctx.author.id)
        data = load_data()
        now = time.time()
        
        user = get_user_data(user_id, data)
        active_effects = self.get_active_effects(user, now)
        
        if not active_effects:
            await ctx.send(embed=error_embed(
                "🪄 Active Effects",
                "You have no active effects!"
            ))
            return
        
        embed = discord.Embed(
            title="🪄 Active Effects",
            color=Colors.EMBED
        )
        
        for effect_id, effect in active_effects.items():
            remaining = int(effect["end_time"] - now)
            
            embed.add_field(
                name=f"{effect['emoji']} {effect['name']}",
                value=f"⏳ {remaining}s remaining",
                inline=True
            )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Farming(bot)) 