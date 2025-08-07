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
    # Same structure, but with try-except
    for filename in os.listdir("./commands"):
        if filename.endswith(".py") and not filename.startswith("__"):
            extension = filename[:-3]  # strip ".py"
            try:
                await bot.load_extension(f"commands.{extension}")
                print(f"Loaded extension: {extension}")
            except commands.errors.NoEntryPointError:
                # This file doesn't have `setup` or `async def setup(bot)`, so skip it.
                print(f"Skipped non-Cog file: {extension}")
            except commands.ExtensionFailed as e:
                # Some other error inside the extension code
                print(f"Failed to load extension {extension}: {e}")

async def main():
    await load_extensions()
    token = get_token()
    await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())
