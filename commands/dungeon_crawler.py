import discord
from discord.ext import commands
from discord import app_commands
import random
import os
import json

ROOM_DESCRIPTIONS = [
    "You enter a torch-lit stone chamber with ancient runes on the walls.",
    "The room is filled with a thick, swirling mist that makes it hard to see.",
    "You find yourselves in a library with rotting books and scattered scrolls.",
    "A collapsed ceiling blocks half the room. There are footprints in the dust.",
    "Crystals grow from the floor, emitting a faint magical glow.",
    "The air here is frigid, and you see your breath in the flickering light."
]

DIRECTIONS = {
    "⬆️": "Up",
    "⬇️": "Down",
    "⬅️": "Left",
    "➡️": "Right"
}
DIRECTION_EMOJI = {v: k for k, v in DIRECTIONS.items()}
STAIRS_EMOJI = "🏃‍♂️"  # Running man for stairs

def get_room_image(dungeon_id, room_id):
    for ext in ['jpg', 'png']:
        img_path = f"dungeons/{dungeon_id}/{room_id}.{ext}"
        if os.path.isfile(img_path):
            return discord.File(img_path), os.path.basename(img_path)
    return None, None

def load_dungeon_json(dungeon_id):
    path = f"dungeons/{dungeon_id}/rooms.json"
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
    return None

def pick_stairs_room(dungeon, exclude_room):
    room_candidates = [
        room_id for room_id, room in dungeon["rooms"].items()
        if room.get("room") and room_id != exclude_room
    ]
    return random.choice(room_candidates) if room_candidates else None

class DungeonCrawl(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.active_crawls = {}

    @app_commands.command(name="dungeon", description="Start a dungeon crawl!")
    @app_commands.describe(
        floors="How many dungeon floors?",
        difficulty="Difficulty level (easy, medium, hard, etc)",
        player1="Party member 1",
        player2="Party member 2 (optional)",
        player3="Party member 3 (optional)",
        player4="Party member 4 (optional)",
        player5="Party member 5 (optional)",
    )
    @app_commands.choices(
        difficulty=[
            app_commands.Choice(name="Easy", value="easy"),
            app_commands.Choice(name="Medium", value="medium"),
            app_commands.Choice(name="Hard", value="hard"),
        ]
    )
    async def dungeon(
        self, interaction: discord.Interaction,
        floors: int,
        difficulty: app_commands.Choice[str],
        player1: discord.Member,
        player2: discord.Member = None,
        player3: discord.Member = None,
        player4: discord.Member = None,
        player5: discord.Member = None
    ):
        channel = interaction.channel

        if channel.id in self.active_crawls:
            await interaction.response.send_message("A dungeon crawl is already active in this channel!", ephemeral=True)
            return

        all_players = [interaction.user]
        for player in (player1, player2, player3, player4, player5):
            if player and player not in all_players:
                all_players.append(player)

        # Load first dungeon (floor 1)
        dungeon = load_dungeon_json(1)
        if not dungeon:
            await interaction.response.send_message("Could not load dungeon for floor 1.", ephemeral=True)
            return

        current_room_id = dungeon["startingRoom"]
        stairs_room_id = pick_stairs_room(dungeon, current_room_id)

        crawl_state = {
            "players": all_players,
            "floors": floors,
            "difficulty": difficulty.value,
            "current_floor": 1,
            "current_dungeon": dungeon,
            "current_room_id": current_room_id,
            "stairs_room_id": stairs_room_id,
            "awaiting_activity": set(m.id for m in all_players),
            "last_msg": None,
            "waiting_for_checkin": True,
            "waiting_for_reactions": False,
            "pending_reactors": set(),
            "votes": {},
            "vote_message_id": None,
        }
        self.active_crawls[channel.id] = crawl_state

        await interaction.response.send_message(
            f"🗝️ **Dungeon Crawl Begins!**\n"
            f"Party: {', '.join(m.mention for m in all_players)}\n"
            f"Floors: {floors} | Difficulty: {difficulty.value.capitalize()}\n\n"
            "**How it works:**\n"
            "- Each floor is a new map, loaded from your prepared dungeons.\n"
            "- A random room on each floor (other than start) contains stairs. You must find it!\n"
            "- Everyone **must write at least once** in the chat before each new room.\n"
            "- After that, the room is described, and the team will vote where to go with emoji!\n"
            f"- **If you find stairs, react with {STAIRS_EMOJI} to go deeper.**\n"
            "- The most voted direction is chosen, but **everyone must vote before moving on**.\n"
            "Let's begin!\n\n"
            f"{all_players[0].mention}, please say something to show you're here!"
        )

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild is None or message.author.bot:
            return
        state = self.active_crawls.get(message.channel.id)
        if not state or not state.get("waiting_for_checkin", False):
            return
        if message.author.id in state["awaiting_activity"]:
            state["awaiting_activity"].remove(message.author.id)
        if not state["awaiting_activity"]:
            state["waiting_for_checkin"] = False
            await self.describe_room(message.channel, state)

    async def describe_room(self, channel, state):
        state["votes"] = {}
        state["pending_reactors"] = set(m.id for m in state["players"])
        state["waiting_for_reactions"] = True

        dungeon = state["current_dungeon"]
        room_id = state["current_room_id"]
        room = dungeon["rooms"][room_id]

        # Use ways from dungeon file
        ways = room["ways"]
        possible_dirs = {DIRECTION_EMOJI[way]: way for way in ways if way in DIRECTION_EMOJI}
        is_stairs_room = (room_id == state["stairs_room_id"] and room.get("room", False))
        if is_stairs_room:
            possible_dirs[STAIRS_EMOJI] = "Stairs"

        dir_text = ' '.join(possible_dirs.keys())
        desc = random.choice(ROOM_DESCRIPTIONS)
        if is_stairs_room:
            desc += f"\n\n**You see a staircase descending! React with {STAIRS_EMOJI} to go deeper.**"

        file, img_filename = get_room_image(state["current_floor"], room_id)
        embed = discord.Embed(
            title=f"Room {room_id} (Floor {state['current_floor']})",
            description=desc,
            color=0xdaa520
        )
        if img_filename:
            embed.set_image(url=f"attachment://{img_filename}")

        msg = await channel.send(
            f"Which way will the party go? React with {dir_text} below!\n"
            f"**All party members must vote before the room continues!**",
            embed=embed,
            file=file
        ) if file else await channel.send(
            f"Which way will the party go? React with {dir_text} below!\n"
            f"**All party members must vote before the room continues!**",
            embed=embed
        )
        for emoji in possible_dirs:
            await msg.add_reaction(emoji)
        state["vote_message_id"] = msg.id
        state["last_msg"] = msg
        state["current_possible_dirs"] = possible_dirs

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        state = self.active_crawls.get(payload.channel_id)
        if not state or not state.get("waiting_for_reactions", False):
            return
        if payload.message_id != state.get("vote_message_id"):
            return
        if payload.user_id not in [m.id for m in state["players"]]:
            return
        emoji = str(payload.emoji)
        if emoji not in state["current_possible_dirs"]:
            return

        state["votes"][payload.user_id] = emoji
        state["pending_reactors"].discard(payload.user_id)

        if not state["pending_reactors"]:
            state["waiting_for_reactions"] = False
            await self.tally_votes_and_move(payload.channel_id)

    async def tally_votes_and_move(self, channel_id):
        state = self.active_crawls.get(channel_id)
        if not state:
            return
        channel = self.bot.get_channel(channel_id)
        vote_counts = {emoji: 0 for emoji in state["current_possible_dirs"]}
        for vote in state["votes"].values():
            if vote in vote_counts:
                vote_counts[vote] += 1
        best_dirs = [k for k, v in vote_counts.items() if v == max(vote_counts.values()) and v > 0]
        if not best_dirs:
            await channel.send("No direction chosen! (Bug?)")
            return
        chosen_dir_emoji = random.choice(best_dirs)
        chosen_dir = state["current_possible_dirs"][chosen_dir_emoji]

        # Handle stairs:
        if chosen_dir == "Stairs":
            await channel.send(f"The party descends the staircase! {STAIRS_EMOJI}")
            # Next floor logic:
            if state["current_floor"] >= state["floors"]:
                await channel.send("You descend the last stairs and complete the dungeon. **Victory!**")
                self.active_crawls.pop(channel.id, None)
                return
            else:
                state["current_floor"] += 1
                dungeon = load_dungeon_json(state["current_floor"])
                if not dungeon:
                    await channel.send(f"Could not load dungeon for floor {state['current_floor']}.")
                    self.active_crawls.pop(channel.id, None)
                    return
                state["current_dungeon"] = dungeon
                state["current_room_id"] = dungeon["startingRoom"]
                # New stairs for new floor:
                state["stairs_room_id"] = pick_stairs_room(dungeon, dungeon["startingRoom"])
                await channel.send(f"Descending to floor {state['current_floor']}!")
                await channel.send("Before the next room, everyone must check in again by sending a message!")
                state["awaiting_activity"] = set(m.id for m in state["players"])
                state["waiting_for_checkin"] = True
                return

        await channel.send(f"The party moves **{chosen_dir}**! {chosen_dir_emoji}")

        # Move party to the next room (as before)
        current_room = state["current_dungeon"]["rooms"][state["current_room_id"]]
        x, y = current_room["x"], current_room["y"]
        if chosen_dir == "Up":
            y -= 1
        elif chosen_dir == "Down":
            y += 1
        elif chosen_dir == "Left":
            x -= 1
        elif chosen_dir == "Right":
            x += 1

        next_room_id = None
        for rid, room in state["current_dungeon"]["rooms"].items():
            if room["x"] == x and room["y"] == y:
                next_room_id = rid
                break

        if not next_room_id:
            await channel.send("There is no room in that direction! The crawl ends here.")
            self.active_crawls.pop(channel.id, None)
            return

        state["current_room_id"] = next_room_id

        await channel.send("Before the next room, everyone must check in again by sending a message!")
        state["awaiting_activity"] = set(m.id for m in state["players"])
        state["waiting_for_checkin"] = True

async def setup(bot):
    await bot.add_cog(DungeonCrawl(bot))
