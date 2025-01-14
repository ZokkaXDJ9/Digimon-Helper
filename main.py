import discord
from discord.ext import commands
import os
import asyncio

def get_token() -> str:
    with open("token.txt", "r") as f:
        return f.read().strip()

intents = discord.Intents.default()

# Supply command_prefix="" to avoid using any text-based commands
bot = commands.Bot(command_prefix="", intents=intents)

@bot.event
async def on_ready():
    await bot.tree.sync()  # Sync slash commands so they appear in Discord
    print(f"Bot is online as {bot.user}")

async def load_extensions():
    for filename in os.listdir("./commands"):
        if filename.endswith(".py") and not filename.startswith("__"):
            extension = filename[:-3]  # e.g., "ping"
            await bot.load_extension(f"commands.{extension}")

async def main():
    await load_extensions()
    token = get_token()
    await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())
