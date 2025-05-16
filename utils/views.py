import discord
from discord.ui import View, Button

class LeaderboardView(View):
    def __init__(self, sorted_users, page=0):
        super().__init__(timeout=60)
        self.sorted_users = sorted_users
        self.page = page
        self.users_per_page = 10
        self.max_pages = (len(sorted_users) - 1) // self.users_per_page + 1
        self.message = None
        
        # Only add navigation buttons if there are more than 10 entries
        if len(sorted_users) > 10:
            self.add_item(Button(label="◀", style=discord.ButtonStyle.primary, custom_id="previous"))
            self.add_item(Button(label="▶", style=discord.ButtonStyle.primary, custom_id="next"))
            
            # Add button callbacks
            for item in self.children:
                if item.custom_id == "previous":
                    item.callback = self.previous_button
                elif item.custom_id == "next":
                    item.callback = self.next_button

    async def previous_button(self, interaction: discord.Interaction):
        self.page = max(0, self.page - 1)
        await self.update_message(interaction)

    async def next_button(self, interaction: discord.Interaction):
        self.page = min(self.max_pages - 1, self.page + 1)
        await self.update_message(interaction)

    async def update_message(self, interaction: discord.Interaction):
        embed = await self.create_embed(interaction.client)
        if len(self.sorted_users) > 10:  # Only update button states if buttons exist
            for item in self.children:
                if item.custom_id == "previous":
                    item.disabled = self.page == 0
                elif item.custom_id == "next":
                    item.disabled = self.page >= self.max_pages - 1
        await interaction.response.edit_message(embed=embed, view=self)

    async def on_timeout(self):
        if self.message:
            await self.message.edit(view=None)

    async def create_embed(self, bot):
        start_idx = self.page * self.users_per_page
        page_users = self.sorted_users[start_idx:start_idx + self.users_per_page]
        
        embed = discord.Embed(
            title="🏆 Wealth Leaderboard",
            description=f"Page {self.page + 1}/{self.max_pages}",
            color=0xf1c40f
        )
        
        for idx, (user_id, stats) in enumerate(page_users, start=start_idx + 1):
            try:
                user = await bot.fetch_user(int(user_id))
                total = stats.get("balance", 0)
                embed.add_field(
                    name=f"{idx}. {user.name}",
                    value=f"${total:,}",
                    inline=False
                )
            except Exception as e:
                print(f"Error processing user {user_id}: {e}")
                continue
        
        if not embed.fields:
            embed.description = "No farmers yet! Start with `!farm`"
        
        embed.set_footer(text="Keep farming to climb the ranks!")
        return embed 