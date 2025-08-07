import discord
from discord.ext import commands
from discord import app_commands
import json
import os


def build_dynamic_diagram(
    pre_evo_main: list[str],
    pre_evo_alts: list[str],
    current: str,
    evo_main: list[str],
    evo_alts: list[str]
) -> str:
    """
    Dynamically builds a properly aligned ASCII evolution diagram with compact spacing.

    Diagram:
          pre_alt[0]──┐          ┌──evo_alt[0]
                     │          │
    pre_alt[1]──┐    │          │    ┌──evo_alt[1]
               │    │          │    │
    pre_main══╪══╪══current══╪══╪══evo_main
               │    │          │    │
    pre_alt[2]──┘    │          │    └──evo_alt[2]
                     │          │
          pre_alt[3]──┘          └──evo_alt[3]
    """
    import math

    # 1. Calculate the max name length for dynamic alignment
    all_names = pre_evo_main + pre_evo_alts + [current] + evo_main + evo_alts
    max_name_length = max(len(name) for name in all_names)
    node_width = max_name_length + 2  # Minimal padding for neatness

    # 2. Helper functions
    def pad_name(name: str, width: int) -> str:
        """Center a name in a given width."""
        return name.center(width)

    def connector_line(spaces: int, symbol: str) -> str:
        """Generate a vertical connector."""
        return " " * spaces + symbol

    # 3. Split alternate evolutions and pre-evolutions into halves
    pre_evo_half = math.ceil(len(pre_evo_alts) / 2)
    evo_half = math.ceil(len(evo_alts) / 2)
    pre_top, pre_bottom = pre_evo_alts[:pre_evo_half], pre_evo_alts[pre_evo_half:]
    evo_top, evo_bottom = evo_alts[:evo_half], evo_alts[evo_half:]

    # 4. Build the top section
    top_section = []
    for i in range(max(len(pre_top), len(evo_top))):
        pre = f"{pad_name(pre_top[i], node_width)}──┐" if i < len(pre_top) else " " * (node_width + 3)
        evo = f"┌──{pad_name(evo_top[i], node_width)}" if i < len(evo_top) else ""
        top_section.append(pre + evo)

    if pre_top or evo_top:
        top_section.append(
            (" " * (node_width)) + "│" + (" " * (node_width)) + "│"
        )

    # 5. Build the center row
    pre_main_str = pad_name(pre_evo_main[0] if pre_evo_main else "", node_width)
    current_str = pad_name(current, node_width)
    evo_main_str = "═══".join(pad_name(evo, node_width) for evo in evo_main)
    center_row = f"{pre_main_str}══╪══{current_str}══╪══{evo_main_str}"

    # 6. Build the bottom section
    bottom_section = []
    for i in range(max(len(pre_bottom), len(evo_bottom))):
        pre = f"{pad_name(pre_bottom[i], node_width)}──┘" if i < len(pre_bottom) else " " * (node_width + 3)
        evo = f"└──{pad_name(evo_bottom[i], node_width)}" if i < len(evo_bottom) else ""
        bottom_section.append(pre + evo)

    if pre_bottom or evo_bottom:
        bottom_section.insert(
            0,
            (" " * (node_width)) + "│" + (" " * (node_width)) + "│"
        )

    # 7. Combine everything into the final diagram
    diagram = []
    if top_section:
        diagram.extend(top_section)
    diagram.append(center_row)
    if bottom_section:
        diagram.extend(bottom_section)

    # 8. Return the diagram wrapped in a code block
    return "```\n" + "\n".join(diagram) + "\n```"

class DigievoCog(commands.Cog):
    """Cog for displaying Digimon evolution diagrams."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="digievo", description="Show the Digimon's evo lines.")
    @app_commands.describe(name="The Digimon name (autocomplete).")
    async def get_digimon_evo(self, interaction: discord.Interaction, name: str):
        file_path = f"data/digimon/{name.lower()}.json"
        if not os.path.exists(file_path):
            await interaction.response.send_message(
                f"Sorry, no data for '{name}'.", ephemeral=True
            )
            return

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Extract evolution data
        pre_evo_main = data.get("evolve_from", {}).get("main_line", [])
        pre_evo_alts = data.get("evolve_from", {}).get("alternate_lines", [])
        evo_main = data.get("evolutions", {}).get("main_line", [])
        evo_alts = data.get("evolutions", {}).get("alternate_lines", [])
        current = data["name"]

        # Generate the diagram
        diagram = build_dynamic_diagram(pre_evo_main, pre_evo_alts, current, evo_main, evo_alts)
        await interaction.response.send_message(diagram)

    @get_digimon_evo.autocomplete("name")
    async def digimon_name_autocomplete(self, interaction: discord.Interaction, current: str):
        if not os.path.isdir("data/digimon"):
            return []
        all_files = os.listdir("data/digimon")
        json_files = [f[:-5] for f in all_files if f.lower().endswith(".json")]
        matched = [dn for dn in json_files if current.lower() in dn.lower()][:25]
        return [app_commands.Choice(name=m.capitalize(), value=m) for m in matched]


async def setup(bot: commands.Bot):
    await bot.add_cog(DigievoCog(bot))
