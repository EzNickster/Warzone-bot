
import discord
from discord.ext import commands
import os
import json

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Spielmodi
modes = [
    "Warzone Einfach 4er",
    "Warzone Solo",
    "Warzone Duo",
    "Warzone 4er",
    "Rebirth Solo",
    "Rebirth Duo",
    "Rebirth Trio",
    "Rebirth 4er"
]

win_counts = {mode: 0 for mode in modes}
user_siege = {}

# Speicherfunktionen
def save_data():
    with open("data.json", "w") as f:
        json.dump({"win_counts": win_counts, "user_siege": user_siege}, f)

def load_data():
    global win_counts, user_siege
    try:
        with open("data.json", "r") as f:
            data = json.load(f)
            win_counts.update(data.get("win_counts", {}))
            user_siege.update({int(k): v for k, v in data.get("user_siege", {}).items()})
    except FileNotFoundError:
        pass

# Embed für Übersicht
def generate_embed():
    embed = discord.Embed(title="🏆 Warzone Siege Tracker", description="Klicke auf einen Modus und wähle deine Mitspieler", color=discord.Color.green())
    for mode in win_counts:
        embed.add_field(name=mode, value=f"{win_counts[mode]} Siege", inline=False)
    return embed

# Sieg-Button mit Auswahl
class WinButton(discord.ui.Button):
    def __init__(self, mode):
        super().__init__(label=f"➕ {mode}", style=discord.ButtonStyle.primary)
        self.mode = mode

    async def callback(self, interaction: discord.Interaction):
        view = PlayerSelectView(self.mode)
        await interaction.response.send_message(f"Wähle Mitspieler für **{self.mode}**:", view=view, ephemeral=True)

# Benutzer-Auswahl
class PlayerSelect(discord.ui.UserSelect):
    def __init__(self, mode):
        super().__init__(placeholder="Wähle bis zu 4 Mitspieler", min_values=1, max_values=4)
        self.mode = mode

    async def callback(self, interaction: discord.Interaction):
        win_counts[self.mode] += 1
        for user in self.values:
            user_siege[user.id] = user_siege.get(user.id, 0) + 1
        save_data()
        await interaction.response.send_message(f"Sieg für **{self.mode}** eingetragen! 🎉", ephemeral=True)

# Ansicht für Auswahl
class PlayerSelectView(discord.ui.View):
    def __init__(self, mode):
        super().__init__(timeout=60)
        self.add_item(PlayerSelect(mode))

# Übersicht anzeigen
class TrackerView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        for mode in modes:
            self.add_item(WinButton(mode))

@bot.command()
async def tracker(ctx):
    embed = generate_embed()
    view = TrackerView()
    await ctx.send(embed=embed, view=view)

@bot.command()
async def leaderboard(ctx):
    if not user_siege:
        await ctx.send("Noch keine Siege vergeben.")
        return

    sorted_users = sorted(user_siege.items(), key=lambda x: x[1], reverse=True)
    leaderboard_text = ""
    for i, (user_id, count) in enumerate(sorted_users, start=1):
        member = await ctx.guild.fetch_member(user_id)
        leaderboard_text += f"{i}. {member.display_name}: {count} Siege\n"

    embed = discord.Embed(title="📊 Leaderboard", description=leaderboard_text, color=discord.Color.blue())
    await ctx.send(embed=embed)

load_data()
bot.run(os.getenv("DISCORD_TOKEN"))
