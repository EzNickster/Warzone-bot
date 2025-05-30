
import discord
from discord.ext import commands
import os
import json

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

win_counts = {
    "Solo": 0,
    "Duo": 0,
    "Quads": 0,
    "Rebirth": 0,
}

user_siege = {}

# Speicherfunktion
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

def generate_embed():
    embed = discord.Embed(title="🏆 Warzone Siege Tracker", description="Klicke ➕ für Sieg, ➖ zum Zurücknehmen", color=discord.Color.green())
    for mode, count in win_counts.items():
        embed.add_field(name=mode, value=f"{count} Siege", inline=False)
    return embed

class WinButton(discord.ui.Button):
    def __init__(self, mode, operator):
        label = f"{'➕' if operator == 'add' else '➖'} {mode}"
        style = discord.ButtonStyle.success if operator == 'add' else discord.ButtonStyle.danger
        super().__init__(label=label, style=style)
        self.mode = mode
        self.operator = operator

    async def callback(self, interaction: discord.Interaction):
        user_id = interaction.user.id

        if self.operator == 'add':
            win_counts[self.mode] += 1
            user_siege[user_id] = user_siege.get(user_id, 0) + 1
            save_data()
        elif self.operator == 'remove':
            if win_counts[self.mode] > 0:
                win_counts[self.mode] -= 1
                if user_siege.get(user_id, 0) > 0:
                    user_siege[user_id] -= 1
                save_data()

        embed = generate_embed()
        await interaction.response.edit_message(embed=embed, view=self.view)

class WinButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        for mode in win_counts:
            self.add_item(WinButton(mode, "add"))
            self.add_item(WinButton(mode, "remove"))

@bot.command()
async def tracker(ctx):
    embed = generate_embed()
    view = WinButtonView()
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

# Lade gespeicherte Siege beim Start
load_data()

# Starte den Bot
bot.run(os.getenv("DISCORD_TOKEN"))
