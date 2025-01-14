import discord
from discord.ext import commands
from discord import app_commands
import json
import os

def bullet_scale(value: int, max_value: int) -> str:
    """
    Returns a string like '⬤⬤⬤⭘⭘⭘ `3/6`' to represent current vs max.
    Example: bullet_scale(3, 6) -> '⬤⬤⬤⭘⭘⭘ `3/6`'
    """
    # Handle edge cases: if max_value == 0, avoid dividing by zero
    if max_value < 1:
        max_value = max(value, 1)
    filled = "⬤" * value
    empty = "⭘" * (max_value - value)
    return f"{filled}{empty} `{value}/{max_value}`"

class DigimonCog(commands.Cog):
    """A Cog that shows Digimon stats in a Pokerole-like format (simplified)."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="digimon",
        description="Show Digimon stats in a Pokerole-like format (simple)."
    )
    @app_commands.describe(name="The name of the Digimon (e.g. Agumon)")
    async def get_digimon(self, interaction: discord.Interaction, name: str):
        """
        Reads data/digimon/{name}.json and displays a stylized text output 
        without ID number, emoji, height, weight, or hp_max.
        """
        # 1) Build the path (lowercase the name to match your file convention)
        json_path = f"data/digimon/{name.lower()}.json"
        if not os.path.exists(json_path):
            await interaction.response.send_message(
                f"Sorry, I couldn't find data for '{name}'.",
                ephemeral=True
            )
            return

        # 2) Load the JSON safely (handle decode errors)
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            await interaction.response.send_message(
                f"Error: The file for '{name}' is not valid JSON.",
                ephemeral=True
            )
            return

        # 3) Gather stats
        digimon_name = data.get("name", "Unknown")
        attribute = data.get("attribute", "Unknown")
        hp_value = data.get("hp", 0)

        # Safely get stat & stat_max for bullet-scale
        # If "strength_max" is missing, default to the same as "strength"
        strength_val = data.get("strength", 0)
        strength_max = data.get("strength_max", strength_val)

        dex_val = data.get("dexterity", 0)
        dex_max = data.get("dexterity_max", dex_val)

        vit_val = data.get("vitality", 0)
        vit_max = data.get("vitality_max", vit_val)

        spc_val = data.get("special", 0)
        spc_max = data.get("special_max", spc_val)

        ins_val = data.get("insight", 0)
        ins_max = data.get("insight_max", ins_val)

        # Convert them to bullet-scale strings
        strength_str = bullet_scale(strength_val, strength_max)
        dex_str      = bullet_scale(dex_val, dex_max)
        vit_str      = bullet_scale(vit_val, vit_max)
        spc_str      = bullet_scale(spc_val, spc_max)
        ins_str      = bullet_scale(ins_val, ins_max)

        # Ability (if present)
        ability = data.get("ability")

        # 4) Build the text output
        # Example layout:
        # ### Agumon
        # **Attribute**: Vaccine
        # **HP**: 5
        # **Strength**: ⬤⬤⬤⭘⭘⭘ `3/6`
        # **Dexterity**: ⬤⬤⬤⭘⭘⭘ `3/6`
        # ...
        # **Ability**: Pepper Breath
        lines = []
        lines.append(f"### {digimon_name}")
        lines.append(f"**Attribute**: {attribute}")
        lines.append(f"**HP**: {hp_value}")
        lines.append(f"**Strength**: {strength_str}")
        lines.append(f"**Dexterity**: {dex_str}")
        lines.append(f"**Vitality**: {vit_str}")
        lines.append(f"**Special**: {spc_str}")
        lines.append(f"**Insight**: {ins_str}")

        if ability:
            lines.append(f"**Ability**: {ability}")

        final_message = "\n".join(lines)

        # 5) Send the response as plain text (Markdown rendered by Discord)
        await interaction.response.send_message(final_message)

    # Optional: Autocomplete, if you want a dropdown of known digimon
    @get_digimon.autocomplete("name")
    async def digimon_name_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str
    ) -> list[app_commands.Choice[str]]:
        """
        Suggest available Digimon names based on JSON files in data/digimon/.
        """
        # If the folder doesn't exist or is empty, just return []
        if not os.path.isdir("data/digimon"):
            return []

        all_digimon = []
        for file in os.listdir("data/digimon"):
            if file.lower().endswith(".json"):
                digimon_name = file[:-5]  # "agumon.json" -> "agumon"
                all_digimon.append(digimon_name)

        # Filter by user input, up to Discord's 25-suggestion limit
        matched = [
            dn for dn in all_digimon
            if current.lower() in dn.lower()
        ][:25]

        # Return them as capitalized names in the dropdown, 
        # but keep the actual value lowercase for the file lookup
        return [
            app_commands.Choice(name=dm.capitalize(), value=dm)
            for dm in matched
        ]

async def setup(bot: commands.Bot):
    """Called automatically when this cog is loaded."""
    await bot.add_cog(DigimonCog(bot))
