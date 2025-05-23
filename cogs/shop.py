import discord
from discord.ext import commands
from utils.database import load_data, save_data, get_user_data
from config import ShopConfig, BiomeConfig, GameConstants, ItemConfig
from utils.embeds import error_embed, success_embed

class Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def shop(self, ctx, page: str = None, biome: str = None):
        """Access the shop"""
        user_id = str(ctx.author.id)
        data = load_data()
        user = get_user_data(user_id, data)

        # Initialize items inventory if it doesn't exist
        if "items" not in user:
            user["items"] = {}

        # Main shop page
        if not page:
            embed = discord.Embed(
                title=f"{ShopConfig.PAGES['main']['emoji']} {ShopConfig.PAGES['main']['name']}",
                description=ShopConfig.PAGES['main']['description'],
                color=ShopConfig.PAGES['main']['color']
            )
            
            # Add category fields
            for category, info in ShopConfig.PAGES.items():
                if category != "main":
                    embed.add_field(
                        name=f"{info['emoji']} {info['name']}",
                        value=f"`!shop {category}` - {info['description']}",
                        inline=False
                    )
            
            await ctx.send(embed=embed)
            return

        # Validate page
        page = page.lower()
        if page not in ShopConfig.PAGES:
            await ctx.send(embed=error_embed(
                "❌ Invalid Shop Page",
                "That shop page doesn't exist!"
            ))
            return

        # Items shop page
        if page == "items":
            embed = discord.Embed(
                title=f"{ShopConfig.PAGES['items']['emoji']} {ShopConfig.PAGES['items']['name']}",
                description=ShopConfig.PAGES['items']['description'],
                color=ShopConfig.PAGES['items']['color']
            )
            
            for item_id, item in ItemConfig.ITEMS.items():
                owned = user["items"].get(item_id, 0)
                embed.add_field(
                    name=f"{item['emoji']} {item['shop_name']} (${item['price']:,})",
                    value=(
                        f"{item['description']}\n"
                        f"Duration: {item['effect']['duration']}s\n"
                        f"Owned: {owned}\n"
                        f"Buy: `!buy item {item_id}`"
                    ),
                    inline=False
                )
            
            await ctx.send(embed=embed)
            return

        # Biomes shop page
        if page == "biomes":
            if biome:
                # Show specific biome shop
                biome = biome.lower()
                if biome not in BiomeConfig.BIOMES:
                    await ctx.send(embed=error_embed(
                        "❌ Invalid Biome",
                        "That biome doesn't exist!"
                    ))
                    return

                biome_data = BiomeConfig.BIOMES[biome]
                user_biome = user["biomes"][biome]

                if not user_biome["unlocked"]:
                    await ctx.send(embed=error_embed(
                        "🔒 Biome Locked",
                        f"You need to unlock this biome first!\nUse `!shop biomes` to view unlock costs."
                    ))
                    return

                # Calculate next capacity upgrade cost
                current_capacity = user_biome["capacity"]
                base_cost = biome_data["capacity_upgrade_base_cost"]
                multiplier = biome_data["capacity_upgrade_multiplier"]
                upgrades_purchased = current_capacity - GameConstants.MAX_PLANTER_CAPACITY
                next_upgrade_cost = int(base_cost * (multiplier ** upgrades_purchased))

                embed = discord.Embed(
                    title=f"{biome_data['emoji']} {biome.title()} Shop",
                    description=f"Upgrade your {biome} garden!",
                    color=biome_data['color']
                )

                embed.add_field(
                    name="Current Capacity",
                    value=f"{current_capacity} plots",
                    inline=True
                )
                embed.add_field(
                    name="Upgrade Cost",
                    value=f"${next_upgrade_cost:,}",
                    inline=True
                )
                embed.add_field(
                    name="How to Buy",
                    value=f"Use `!buy {biome} capacity` to upgrade",
                    inline=False
                )

            else:
                # Show biomes overview
                embed = discord.Embed(
                    title=f"{ShopConfig.PAGES['biomes']['emoji']} {ShopConfig.PAGES['biomes']['name']}",
                    description="Unlock new biomes to expand your farming empire!",
                    color=ShopConfig.PAGES['biomes']['color']
                )

                for biome_name, biome_data in BiomeConfig.BIOMES.items():
                    if biome_name == "grassland":
                        status = "🔓 Unlocked"
                        value = f"`!shop biomes {biome_name}` to view upgrades"
                    else:
                        user_biome = user["biomes"][biome_name]
                        if user_biome["unlocked"]:
                            status = "🔓 Unlocked"
                            value = f"`!shop biomes {biome_name}` to view upgrades"
                        else:
                            status = "🔒 Locked"
                            value = f"Cost: ${biome_data['unlock_cost']:,}\n`!buy {biome_name}` to unlock"

                    embed.add_field(
                        name=f"{biome_data['emoji']} {biome_name.title()} - {status}",
                        value=value,
                        inline=False
                    )

            await ctx.send(embed=embed)

    @commands.command()
    async def buy(self, ctx, category: str = None, item: str = None):
        """Buy items and upgrades"""
        user_id = str(ctx.author.id)
        data = load_data()
        user = get_user_data(user_id, data)

        # Initialize items inventory if it doesn't exist
        if "items" not in user:
            user["items"] = {}

        if not category:
            await ctx.send(embed=error_embed(
                "❌ Missing Arguments",
                "**Usage:**\n"
                "`!buy <biome>` - Unlock a biome\n"
                "`!buy <biome> capacity` - Upgrade biome capacity\n"
                "`!buy item <item_name>` - Purchase an item"
            ))
            return

        # Handle item purchases
        if category.lower() == "item":
            if not item:
                await ctx.send(embed=error_embed(
                    "❌ Missing Item",
                    "Please specify which item to buy!\nUse `!shop items` to see available items."
                ))
                return

            item = item.lower()
            if item not in ItemConfig.ITEMS:
                await ctx.send(embed=error_embed(
                    "❌ Invalid Item",
                    "That item doesn't exist!\nUse `!shop items` to see available items."
                ))
                return

            item_data = ItemConfig.ITEMS[item]
            cost = item_data["price"]

            if user["balance"] < cost:
                await ctx.send(embed=error_embed(
                    "❌ Insufficient Funds",
                    f"You need ${cost:,} to buy this item!\nYou have: ${user['balance']:,}"
                ))
                return

            # Process purchase
            user["balance"] -= cost
            # Get quantity from shop name (e.g., "x5" -> 5)
            quantity = 1
            if "x" in item_data["shop_name"]:
                quantity = int(item_data["shop_name"].split("x")[1].split()[0])
            user["items"][item] = user["items"].get(item, 0) + quantity
            save_data(data)

            await ctx.send(embed=success_embed(
                f"{item_data['emoji']} Item Purchased!",
                f"You bought {item_data['shop_name']}!\n\n"
                f"**Balance:** ${user['balance']:,}\n"
                f"**Effect:** {item_data['description']}\n"
                f"**Duration:** {item_data['effect']['duration']} seconds\n\n"
                "Use `!use <item_name>` to use this item!"
            ))
            return

        # Handle biome purchases
        biome = category.lower()
        if biome not in BiomeConfig.BIOMES:
            await ctx.send(embed=error_embed(
                "❌ Invalid Biome",
                "That biome doesn't exist!"
            ))
            return

        biome_data = BiomeConfig.BIOMES[biome]
        user_biome = user["biomes"][biome]

        # Buying biome unlock
        if not item:
            if user_biome["unlocked"]:
                await ctx.send(embed=error_embed(
                    "❌ Already Unlocked",
                    f"You've already unlocked the {biome} biome!\nUse `!shop biomes {biome}` to view upgrades."
                ))
                return

            cost = biome_data["unlock_cost"]
            if user["balance"] < cost:
                await ctx.send(embed=error_embed(
                    "❌ Insufficient Funds",
                    f"You need ${cost:,} to unlock this biome!\nYou have: ${user['balance']:,}"
                ))
                return

            # Process purchase
            user["balance"] -= cost
            user_biome["unlocked"] = True
            save_data(data)

            await ctx.send(embed=success_embed(
                f"{biome_data['emoji']} Biome Unlocked!",
                f"You've unlocked the {biome} biome!\n\n" +
                f"**Balance:** ${user['balance']:,}\n" +
                f"**Next Steps:** Use `!shop biomes {biome}` to view upgrades"
            ))

        # Buying capacity upgrade
        elif item.lower() == "capacity":
            if not user_biome["unlocked"]:
                await ctx.send(embed=error_embed(
                    "❌ Biome Locked",
                    f"You need to unlock this biome first!\nUse `!buy {biome}` to unlock."
                ))
                return

            # Calculate upgrade cost
            current_capacity = user_biome["capacity"]
            base_cost = biome_data["capacity_upgrade_base_cost"]
            multiplier = biome_data["capacity_upgrade_multiplier"]
            upgrades_purchased = current_capacity - GameConstants.MAX_PLANTER_CAPACITY
            cost = int(base_cost * (multiplier ** upgrades_purchased))

            if user["balance"] < cost:
                await ctx.send(embed=error_embed(
                    "❌ Insufficient Funds",
                    f"You need ${cost:,} to upgrade capacity!\nYou have: ${user['balance']:,}"
                ))
                return

            # Process purchase
            user["balance"] -= cost
            user_biome["capacity"] += 1
            save_data(data)

            # Calculate next upgrade cost
            next_cost = int(base_cost * (multiplier ** (upgrades_purchased + 1)))

            await ctx.send(embed=success_embed(
                f"{biome_data['emoji']} Capacity Upgraded!",
                f"Your {biome} garden capacity has been increased!\n\n" +
                f"**New Capacity:** {user_biome['capacity']} plots\n" +
                f"**Balance:** ${user['balance']:,}\n" +
                f"**Next Upgrade Cost:** ${next_cost:,}"
            ))

        else:
            await ctx.send(embed=error_embed(
                "❌ Invalid Item",
                "That item doesn't exist!"
            ))

async def setup(bot):
    await bot.add_cog(Shop(bot)) 