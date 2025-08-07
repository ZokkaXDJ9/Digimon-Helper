import discord
from discord.ext import commands
import random

class InitiativeTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.combat_channels = {}

    @commands.hybrid_command(name="combat_start")
    async def combat_start(self, ctx):
        """Starts initiative tracking in the current channel."""
        if ctx.channel.id in self.combat_channels:
            await ctx.send("Initiative tracking is already active in this channel!")
            return

        self.combat_channels[ctx.channel.id] = {
            "initiatives": [],
            "current_turn": 0,
            "round": 1,
            "buffs": {},  
            "statuses": {},  
            "prio": {},    
            "react": set(),  
            "stall": set()   
        }
        await ctx.send("Combat has started! Use /initiative to join initiative.")

    async def initiative_autocomplete(self, interaction: discord.Interaction, current: str):
        """Autocomplete for initiative participant names."""
        channel_id = interaction.channel.id
        if channel_id not in self.combat_channels:
            return []
        
        return [
            discord.app_commands.Choice(name=char["name"], value=char["name"])
            for char in self.combat_channels[channel_id]["initiatives"]
            if current.lower() in char["name"].lower()
        ]

    @commands.hybrid_command(name="initiative")
    async def initiative(self, ctx, name: str, dexterity: int):
        """Adds a character to the initiative order."""
        if ctx.channel.id not in self.combat_channels:
            await ctx.send("Combat has not been started in this channel. Use /combat_start first.")
            return

        combat = self.combat_channels[ctx.channel.id]
        combat["buffs"][name] = 0  
        combat["statuses"][name] = None  

        final_dex = dexterity + combat["buffs"].get(name, 0)
        if combat["statuses"].get(name) == "Paralysis":
            final_dex //= 2

        d100_roll = random.randint(1, 100)  # d100 for tiebreaker
        combat["initiatives"].append({
            "name": name,
            "dexterity": final_dex,
            "roll": d100_roll
        })

        # Sort by dexterity first, then d100 for tiebreakers
        combat["initiatives"].sort(key=lambda x: (-x["dexterity"], -x["roll"]))
        await ctx.send(f"{name} has joined the initiative with Dexterity {dexterity} and a tiebreaker roll of {d100_roll}!")

    @commands.hybrid_command(name="initiative_remove")
    @discord.app_commands.autocomplete(name=initiative_autocomplete)
    async def initiative_remove(self, ctx, name: str):
        """Removes a character from the initiative order."""
        if ctx.channel.id not in self.combat_channels:
            await ctx.send("Combat has not been started in this channel.")
            return

        combat = self.combat_channels[ctx.channel.id]
        combat["initiatives"] = [char for char in combat["initiatives"] if char["name"] != name]
        await ctx.send(f"{name} has been removed from the initiative order.")

    @commands.hybrid_command(name="initiative_start")
    async def initiative_start(self, ctx):
        """Announces initiative order and starts turn tracking."""
        if ctx.channel.id not in self.combat_channels:
            await ctx.send("Combat has not been started in this channel.")
            return

        combat = self.combat_channels[ctx.channel.id]
        if not combat["initiatives"]:
            await ctx.send("No players are in the initiative order.")
            return

        await self.update_initiative_order(ctx, first_round=True)

    async def update_initiative_order(self, ctx, first_round=False):
        """Updates initiative order at the start of each round."""
        combat = self.combat_channels[ctx.channel.id]

        # Apply Prio, React, and reset after the round
        for char in combat["initiatives"]:
            name = char["name"]
            if name in combat["prio"]:
                char["dexterity"] = combat["prio"][name]
            if name in combat["react"]:
                char["dexterity"] = -1  

        combat["initiatives"].sort(key=lambda x: (-x["dexterity"], -x["roll"]))

        combat["prio"].clear()
        combat["react"].clear()

        initiative_message = f"### Round {combat['round']} Begins! ###\n"
        for i, char in enumerate(combat["initiatives"], start=1):
            initiative_message += f"{i}. {char['name']} (**{char['dexterity']}**)\n"

        await ctx.send(initiative_message)
        await self.announce_turn(ctx)

    async def announce_turn(self, ctx):
        """Announces the current turn."""
        combat = self.combat_channels[ctx.channel.id]
        current_character = combat["initiatives"][combat["current_turn"]]
        await ctx.send(f"It is now **{current_character['name']}'s** turn! {ctx.author.mention}")

    @commands.hybrid_command(name="next")
    async def next(self, ctx):
        """Ends the current turn."""
        combat = self.combat_channels[ctx.channel.id]
        combat["current_turn"] += 1

        if combat["current_turn"] >= len(combat["initiatives"]):
            combat["current_turn"] = 0
            combat["round"] += 1
            combat["stall"].clear()
            await self.update_initiative_order(ctx)

        else:
            await self.announce_turn(ctx)

    @commands.hybrid_command(name="combat_end")
    async def combat_end(self, ctx):
        """Ends combat tracking in the current channel."""
        if ctx.channel.id in self.combat_channels:
            del self.combat_channels[ctx.channel.id]
            await ctx.send("Combat has ended in this channel.")

    @commands.hybrid_command(name="prio")
    @discord.app_commands.autocomplete(name=initiative_autocomplete)
    async def prio(self, ctx, name: str, value: int):
        """Sets initiative to Y for next round only."""
        combat = self.combat_channels[ctx.channel.id]
        combat["prio"][name] = value
        await ctx.send(f"{name}'s initiative is set to {value} for the next round.")

    @commands.hybrid_command(name="react")
    @discord.app_commands.autocomplete(name=initiative_autocomplete)
    async def react(self, ctx, name: str):
        """Sets initiative to lowest priority (last) for next round only."""
        combat = self.combat_channels[ctx.channel.id]
        combat["react"].add(name)
        await ctx.send(f"{name} will act last in the next round.")

    @commands.hybrid_command(name="stall")
    async def stall(self, ctx):
        """Moves the current player to the end of the initiative order for this round only."""
        combat = self.combat_channels[ctx.channel.id]
        current_character = combat["initiatives"][combat["current_turn"]]["name"]

        combat["stall"].add(current_character)
        combat["initiatives"].append(combat["initiatives"].pop(combat["current_turn"]))

        await ctx.send(f"{current_character} is stalling and will act last this round.")
        await self.announce_turn(ctx)

async def setup(bot):
    await bot.add_cog(InitiativeTracker(bot))
