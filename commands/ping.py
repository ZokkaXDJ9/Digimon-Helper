import discord
from discord.ext import commands
from discord import app_commands

class PingCog(commands.Cog):
    """A simple Cog that houses a /ping slash command."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="ping",
        description="Replies with Pong!"
    )
    async def ping(self, interaction: discord.Interaction):
        """Send 'Pong!' as a response."""
        await interaction.response.send_message("Pong!")

async def setup(bot: commands.Bot):
    """Called automatically when this file is loaded as an extension."""
    await bot.add_cog(PingCog(bot))
