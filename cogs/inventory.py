import discord
from discord.ext import commands
from utils.database import load_data, save_data, get_user_data
from config import CropConfig, MutationConfig, EmojiConfig, ItemConfig
from utils.embeds import error_embed, success_embed, confirmation_embed

class Inventory(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="inventory", aliases=["inv"])
    async def inventory(self, ctx, user: discord.Member = None):
        """Check your or another user's inventory"""
        target_user = user or ctx.author
        user_id = str(target_user.id)
        data = load_data()

        if user_id not in data["users"]:
            description = (f"{target_user.mention} hasn't farmed yet!" 
                        if user else "You haven't farmed yet! Use `!roll` to get started.")
            await ctx.send(embed=error_embed(
                "🎒 Farming Inventory",
                description
            ))
            return

        user_data = data["users"][user_id]
        crops = user_data["inventory"]
        seeds = user_data["seeds"]
        balance = user_data.get("balance", 0)
        
        embed = discord.Embed(
            title=f"🎒 {target_user.display_name}'s Inventory",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="💰 Balance",
            value=f"${balance:,}",
            inline=False
        )
        
        # Items Section
        if "items" not in user_data:
            user_data["items"] = {}
        
        items_lines = []
        for item_name, quantity in user_data["items"].items():
            if item_name in ItemConfig.ITEMS:
                item = ItemConfig.ITEMS[item_name]
                items_lines.append(
                    f"{item['emoji']} {item['name']}: {quantity}\n"
                    f"└ {item['description']}"
                )
        
        embed.add_field(
            name="🛠️ Items",
            value="\n".join(items_lines) if items_lines else "No items",
            inline=False
        )
        
        # Crops Section
        crop_lines = []
        for crop, data in crops.items():
            # Handle old inventory structure
            if isinstance(data, int):
                if data > 0:
                    crop_lines.append(f"{EmojiConfig.EMOJI_MAP[crop]} {crop.title()}: {data} (${CropConfig.PRICES[crop]}/ea)")
            else:
                # Handle normal crops
                if data["amount"] > 0:
                    crop_lines.append(f"{EmojiConfig.EMOJI_MAP[crop]} {crop.title()}: {data['amount']} (${CropConfig.PRICES[crop]}/ea)")
                
                # Handle mutations
                if "mutations" in data:
                    for mutation, amount in data["mutations"].items():
                        if amount > 0:
                            price = CropConfig.PRICES[crop] * MutationConfig.MUTATIONS[mutation]["price_multiplier"]
                            crop_lines.append(
                                f"{MutationConfig.MUTATIONS[mutation]['emoji']} {mutation.title()} {crop.title()}: {amount} (${price}/ea)"
                            )
        
        embed.add_field(
            name="🌾 Harvested Crops",
            value="\n".join(crop_lines) if crop_lines else "No crops harvested",
            inline=False
        )
        
        # Seeds Section
        seed_items = "\n".join(
            [f"{EmojiConfig.EMOJI_MAP[seed]} {seed.replace('_', ' ').title()}: {qty}" 
             for seed, qty in seeds.items() if qty > 0]
        ) or "No seeds available"
        embed.add_field(
            name="🌱 Seed Inventory",
            value=seed_items,
            inline=False
        )
        
        embed.set_thumbnail(url=target_user.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.command()
    async def sell(self, ctx, *, args=None):
        """Handle selling of crops"""
        user_id = str(ctx.author.id)
        data = load_data()
        
        if user_id not in data["users"]:
            await ctx.send(embed=error_embed(
                "❌ No Account",
                "You don't have anything to sell!"
            ))
            return

        if not args:
            await self.sell_all(ctx, data)
        else:
            await self.sell_specific(ctx, data, args)

    async def sell_all(self, ctx, data):
        """Sell all crops"""
        user_id = str(ctx.author.id)
        user = data["users"][user_id]
        
        # Calculate total value including mutations
        total = 0
        sale_summary = []
        
        for crop, crop_data in user["inventory"].items():
            if crop not in CropConfig.PRICES:
                continue
                
            # Handle old inventory structure
            if isinstance(crop_data, int):
                if crop_data > 0:
                    value = crop_data * CropConfig.PRICES[crop]
                    total += value
                    sale_summary.append(f"{EmojiConfig.EMOJI_MAP[crop]} {crop.title()}: {crop_data} (${value:,})")
            else:
                # Normal crops
                if crop_data["amount"] > 0:
                    value = crop_data["amount"] * CropConfig.PRICES[crop]
                    total += value
                    sale_summary.append(f"{EmojiConfig.EMOJI_MAP[crop]} {crop.title()}: {crop_data['amount']} (${value:,})")
                
                # Mutated crops
                if "mutations" in crop_data:
                    for mutation, amount in crop_data["mutations"].items():
                        if amount > 0:
                            mut_price = CropConfig.PRICES[crop] * MutationConfig.MUTATIONS[mutation]["price_multiplier"]
                            value = amount * mut_price
                            total += value
                            sale_summary.append(
                                f"{MutationConfig.MUTATIONS[mutation]['emoji']} {mutation.title()} {crop.title()}: {amount} (${value:,})"
                            )
        
        if total == 0:
            await ctx.send(embed=error_embed(
                "🚫 Empty Inventory",
                "You don't have anything to sell!"
            ))
            return

        # Confirmation embed
        confirm_msg = await ctx.send(embed=confirmation_embed(
            "⚠️ Confirm Bulk Sale",
            f"Are you sure you want to sell **ALL** crops?\n\n**Sale Summary:**\n" + "\n".join(sale_summary),
            total
        ))
        await confirm_msg.add_reaction("✅")
        await confirm_msg.add_reaction("❌")

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) in ["✅", "❌"]

        try:
            reaction, _ = await self.bot.wait_for("reaction_add", timeout=30.0, check=check)
            
            if str(reaction.emoji) == "✅":
                # Reset inventory and add balance
                for crop in user["inventory"]:
                    if isinstance(user["inventory"][crop], int):
                        user["inventory"][crop] = 0
                    else:
                        user["inventory"][crop] = {
                            "amount": 0,
                            "mutations": {}
                        }
                user["balance"] += total
                save_data(data)
                
                await ctx.send(embed=success_embed(
                    "💰 Bulk Sale Complete!",
                    f"Successfully sold all crops!\n\n**Sale Summary:**\n" + 
                    "\n".join(sale_summary) +
                    f"\n\n**Total Earned:** ${total:,}\n**New Balance:** ${user['balance']:,}"
                ))
                
            else:
                await ctx.send(embed=error_embed(
                    "🚫 Sale Canceled",
                    "Your crops remain in your inventory."
                ))

        except TimeoutError:
            await ctx.send(embed=error_embed(
                "⏳ Sale Expired",
                "Confirmation timed out after 30 seconds."
            ))

    async def sell_specific(self, ctx, data, args):
        """Sell specific crops"""
        user_id = str(ctx.author.id)
        user = data["users"][user_id]
        
        try:
            args = args.split()
            if len(args) not in [1, 2]:
                raise ValueError
            
            crop = args[0].lower()
            mutation = None
            
            # Check if selling a specific mutation
            if ":" in crop:
                crop, mutation = crop.split(":", 1)
                if mutation not in MutationConfig.MUTATIONS:
                    await ctx.send(embed=error_embed(
                        "❌ Invalid Mutation",
                        "That mutation type doesn't exist!"
                    ))
                    return
            
            if crop not in CropConfig.PRICES:
                await ctx.send(embed=error_embed(
                    "❌ Invalid Crop",
                    f"That's not a sellable crop!\n\nAvailable Crops:\n{', '.join(CropConfig.PRICES.keys())}"
                ))
                return
                
            # Get available amount based on mutation
            if mutation:
                available = user["inventory"].get(crop, {}).get("mutations", {}).get(mutation, 0)
            else:
                available = user["inventory"].get(crop, {}).get("amount", 0)
            
            amount = int(args[1]) if len(args) == 2 else available
                
            if amount <= 0:
                await ctx.send(embed=error_embed(
                    "❌ Invalid Amount",
                    "Amount must be a positive number!"
                ))
                return
                
            if available < amount:
                await ctx.send(embed=error_embed(
                    "❌ Insufficient Quantity",
                    f"You only have {available} {mutation + ' ' if mutation else ''}{crop}!"
                ))
                return

            # Calculate value with mutation multiplier
            base_value = CropConfig.PRICES[crop]
            if mutation:
                base_value *= MutationConfig.MUTATIONS[mutation]["price_multiplier"]
            value = amount * base_value

            # Process sale
            if mutation:
                user["inventory"][crop]["mutations"][mutation] -= amount
            else:
                user["inventory"][crop]["amount"] -= amount
            user["balance"] += value
            save_data(data)

            await ctx.send(embed=success_embed(
                "💰 Sale Complete!",
                f"Successfully sold {amount} {mutation + ' ' if mutation else ''}{crop}!\n\n" +
                f"**Earned:** ${value:,}\n**New Balance:** ${user['balance']:,}"
            ))

        except (ValueError, IndexError):
            await ctx.send(embed=error_embed(
                "❌ Invalid Format",
                "**Usage:**\n`!sell <crop> [amount]` - Sell normal crops\n`!sell <crop:mutation> [amount]` - Sell mutated crops"
            ))

async def setup(bot):
    await bot.add_cog(Inventory(bot)) 