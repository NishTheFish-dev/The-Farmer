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
    GameConstants
)
from utils.embeds import error_embed, success_embed, confirmation_embed

class Farming(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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
                "amount": 1
            }

        # Update seeds inventory
        user["seeds"][seed_type] -= plant_amount
        save_data(data)

        # Calculate updated capacity after planting
        updated_used_capacity = len(user["plantings"][biome])

        await ctx.send(embed=success_embed(
            f"{BiomeConfig.BIOMES[biome]['emoji']} Planting Started!",
            f"Planting {plant_amount} {seed_type.replace('_seed', '')} seed{'s' if plant_amount > 1 else ''} in {biome}\n" +
            f"Plots used: {updated_used_capacity}/{current_capacity}\n" +
            f"Use `!garden {biome}` to track your plantings"
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

        # If no biome specified, try to use preferred biome
        if not biome and preferred_biome:
            biome = preferred_biome

        # If still no biome specified, show overview
        if not biome:
            embed = discord.Embed(
                title=f"🌱 {ctx.author.display_name}'s Gardens Overview",
                description="Select a biome to view detailed plantings:",
                color=discord.Color.blue()
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

        # Validate biome
        biome = biome.lower()
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

        # Show specific biome garden
        plantings = []
        biome_data = BiomeConfig.BIOMES[biome]
        
        for planting_id, details in user["plantings"][biome].items():
            seed_type = details["seed_type"]
            crop_name = seed_type.replace("_seed", "")
            elapsed = now - details["start_time"]
            remaining = details["duration"] - elapsed
            
            if remaining <= 0:
                status = "✅ Ready to harvest!"
            else:
                status = f"⏳ {int(remaining)}s remaining"
            
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
        
        await ctx.send(embed=embed)

    @commands.command()
    async def harvest(self, ctx, biome: str = None):
        """Harvest all ready crops from all biomes or a specific biome"""
        user_id = str(ctx.author.id)
        data = load_data()
        now = time.time()
        
        user = get_user_data(user_id, data)
        
        # If no biome specified, harvest from all biomes
        biomes_to_harvest = []
        if biome:
            # Validate biome
            biome = biome.lower()
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
            
            biomes_to_harvest = [biome]
        else:
            # Get all unlocked biomes
            biomes_to_harvest = [b for b, data in user["biomes"].items() 
                               if data["unlocked"] or b == "grassland"]
        
        # Check all biomes for ready crops
        ready_crops = {}
        for b in biomes_to_harvest:
            harvested = await self.harvest_from_biome(user, b, now)
            if harvested:
                ready_crops[b] = harvested
        
        if not ready_crops:
            await ctx.send(embed=error_embed(
                "❌ Nothing to Harvest",
                "No crops are ready to harvest yet!" +
                (f" in {biome}" if biome else "")
            ))
            return
        
        # Create harvest summary
        summary_lines = []
        for b, crops in ready_crops.items():
            summary_lines.append(f"\n**{BiomeConfig.BIOMES[b]['emoji']} {b.title()}:**")
            summary_lines.extend([f"  {crop}" for crop in crops])
        
        # Send confirmation message
        confirm_msg = await ctx.send(embed=confirmation_embed(
            "🌾 Ready to Harvest!",
            f"The following crops are ready to harvest:\n" + "\n".join(summary_lines) +
            "\n\nReact with ✅ to harvest all crops!"
        ))
        await confirm_msg.add_reaction("✅")
        await confirm_msg.add_reaction("❌")

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["✅", "❌"]

        try:
            reaction, _ = await self.bot.wait_for(
                "reaction_add", 
                timeout=GameConstants.CONFIRMATION_TIMEOUT,
                check=check
            )
            
            if str(reaction.emoji) == "✅":
                # Process the harvest
                save_data(data)
                
                await ctx.send(embed=success_embed(
                    "🌾 Harvest Complete!",
                    f"Successfully harvested:\n" + "\n".join(summary_lines) +
                    "\n\nUse `!inv` to view your harvested crops!"
                ))
            else:
                await ctx.send(embed=error_embed(
                    "❌ Harvest Cancelled",
                    "Your crops remain in the garden."
                ))

        except TimeoutError:
            await ctx.send(embed=error_embed(
                "⏳ Harvest Expired",
                f"Confirmation timed out after {GameConstants.CONFIRMATION_TIMEOUT} seconds."
            ))

    def get_random_seed(self):
        """Get a random seed based on rarity tiers."""
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

    async def harvest_from_biome(self, user, biome, now):
        """Harvest all ready crops from a specific biome."""
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

async def setup(bot):
    await bot.add_cog(Farming(bot)) 