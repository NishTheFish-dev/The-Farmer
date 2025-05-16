from discord import Embed
from config import Colors

def error_embed(title: str, description: str) -> Embed:
    """Create an error embed"""
    return Embed(
        title=title,
        description=description,
        color=Colors.ERROR
    )

def success_embed(title: str, description: str) -> Embed:
    """Create a success embed"""
    return Embed(
        title=title,
        description=description,
        color=Colors.EMBED
    )

def info_embed(title: str, description: str) -> Embed:
    """Create an info embed"""
    return Embed(
        title=title,
        description=description,
        color=Colors.INFO
    )

def confirmation_embed(title: str, description: str, value: int = None) -> Embed:
    """Create a confirmation embed"""
    embed = Embed(
        title=title,
        description=description,
        color=Colors.INFO
    )
    
    if value is not None:
        embed.add_field(
            name="Total Value",
            value=f"${value:,}",
            inline=True
        )
    
    embed.add_field(
        name="Confirmation",
        value="React with ✅ to confirm\nReact with ❌ to cancel",
        inline=True
    )
    
    return embed 