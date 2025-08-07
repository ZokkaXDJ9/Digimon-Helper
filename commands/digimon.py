import discord
from discord.ext import commands
from discord import app_commands, ui
import json
import os

def bullet_scale(value: int, max_value: int) -> str:
    """
    Returns a string like '⬤⬤⬤⭘⭘⭘ `3/6`' to represent current vs max.
    Example: bullet_scale(3, 6) -> '⬤⬤⬤⭘⭘⭘ `3/6`'
    """
    if max_value < 1:
        max_value = max(value, 1)
    filled = "⬤" * value
    empty = "⭘" * (max_value - value)
    return f"{filled}{empty} `{value}/{max_value}`"


def build_info_message(data: dict) -> str:
    """
    Builds the Digimon info message, including evolution details.
    """
    digimon_name = data.get("name", "Unknown")
    attribute = data.get("attribute", "Unknown")
    level = data.get("level", "Unknown")
    hp_value = data.get("hp", 0)

    strength_str = bullet_scale(data.get("strength", 0), data.get("strength_max", data.get("strength", 0)))
    dex_str = bullet_scale(data.get("dexterity", 0), data.get("dexterity_max", data.get("dexterity", 0)))
    vit_str = bullet_scale(data.get("vitality", 0), data.get("vitality_max", data.get("vitality", 0)))
    spc_str = bullet_scale(data.get("special", 0), data.get("special_max", data.get("special", 0)))
    ins_str = bullet_scale(data.get("insight", 0), data.get("insight_max", data.get("insight", 0)))

    ability = data.get("ability", "None")
    evolves_from = data.get("evolves_from", None)
    evolves_to = data.get("evolves_to", [])

    lines = [
        f"### {digimon_name}",
        f"**Attribute**: {attribute}",
        f"**Level**: {level}",
        "",
        f"**HP**: {hp_value}",
        f"**Strength**: {strength_str}",
        f"**Dexterity**: {dex_str}",
        f"**Vitality**: {vit_str}",
        f"**Special**: {spc_str}",
        f"**Insight**: {ins_str}",
    ]

    if ability:
        lines.append(f"**Ability**: {ability}")

    return "\n".join(lines)


class DigimonView(ui.View):
    def __init__(self, bot, data):
        super().__init__()
        self.bot = bot
        self.data = data

    @ui.button(label="Show Moves", style=discord.ButtonStyle.primary)
    async def show_moves(self, interaction: discord.Interaction, button: ui.Button):
        moves = self.data.get("moves", [])
        if not moves:
            await interaction.response.edit_message(
                content="This Digimon has no recorded moves.",
                view=self
            )
            return

        move_text = "\n".join(f"- {move}" for move in moves)
        content = f"### {self.data.get('name', 'Unknown')} Moves\n\n{move_text}"
        await interaction.response.edit_message(content=content, view=self)

    @ui.button(label="Show Evolution", style=discord.ButtonStyle.success)
    async def show_evolution(self, interaction: discord.Interaction, button: ui.Button):
        evolves_from = self.data.get("evolves_from", "Unknown")
        evolves_to = self.data.get("evolves_to", [])

        evolution_text = f"**Evolves From**: {evolves_from}\n"
        if evolves_to:
            evolution_text += f"**Evolves To**: {', '.join(evolves_to)}"
        else:
            evolution_text += "**Evolves To**: None"

        content = f"### {self.data.get('name', 'Unknown')} Evolution\n\n{evolution_text}"
        await interaction.response.edit_message(content=content, view=self)

    @ui.button(label="Show Info", style=discord.ButtonStyle.secondary)
    async def show_info(self, interaction: discord.Interaction, button: ui.Button):
        await interaction.response.edit_message(content=build_info_message(self.data), view=self)


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
        json_path = f"data/digimon/{name.lower()}.json"
        if not os.path.exists(json_path):
            await interaction.response.send_message(
                f"Sorry, I couldn't find data for '{name}'.",
                ephemeral=True
            )
            return

        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            await interaction.response.send_message(
                f"Error: The file for '{name}' is not valid JSON.",
                ephemeral=True
            )
            return

        message_content = build_info_message(data)
        view = DigimonView(self.bot, data)
        await interaction.response.send_message(message_content, view=view)

    @get_digimon.autocomplete("name")
    async def digimon_name_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str
    ) -> list[app_commands.Choice[str]]:
        if not os.path.isdir("data/digimon"):
            return []

        all_digimon = [
            file[:-5] for file in os.listdir("data/digimon")
            if file.lower().endswith(".json")
        ]

        matched = [dn for dn in all_digimon if current.lower() in dn.lower()][:25]
        return [app_commands.Choice(name=dm.capitalize(), value=dm) for dm in matched]


async def setup(bot: commands.Bot):
    await bot.add_cog(DigimonCog(bot))
