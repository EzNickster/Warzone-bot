
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
user_mode_wins = {}
leaderboard_message = {"channel_id": None, "message_id": None}

def save_data():
    with open("data.json", "w") as f:
        json.dump({
            "win_counts": win_counts,
            "user_siege": user_siege,
            "user_mode_wins": user_mode_wins,
            "leaderboard_message": leaderboard_message
        }, f)

def load_data():
    global win_counts, user_siege, user_mode_wins, leaderboard_message
    try:
        with open("data.json", "r") as f:
            data = json.load(f)
            win_counts.update(data.get("win_counts", {}))
            user_siege.update({int(k): v for k, v in data.get("user_siege", {}).items()})
            user_mode_wins.update({int(k): v for k, v in data.get("user_mode_wins", {}).items()})
            leaderboard_message.update(data.get("leaderboard_message", {}))
    except FileNotFoundError:
        pass

def generate_embed():
    embed = discord.Embed(
        title="🏆 Warzone Siege Tracker",
        description="🎮 Wähle einen Modus und trag deinen Sieg mit Mitspielern ein:",
        color=discord.Color.gold()
    )
    for mode in win_counts:
        embed.add_field(name=f"🔹 {mode}", value=f"{win_counts[mode]} Siege", inline=False)
    embed.set_footer(text="⏺ Per Klick + Auswahl deiner Mitspieler werden die Siege automatisch gezählt.")
    return embed

class WinButton(discord.ui.Button):
    def __init__(self, mode):
        super().__init__(label=f"➕ {mode}", style=discord.ButtonStyle.primary)
        self.mode = mode

    async def callback(self, interaction: discord.Interaction):
        view = PlayerSelectView(self.mode)
        await interaction.response.send_message(f"Wähle Mitspieler für **{self.mode}**:", view=view, ephemeral=True)

class PlayerSelect(discord.ui.UserSelect):
    def __init__(self, mode):
        super().__init__(placeholder="Wähle bis zu 4 Mitspieler", min_values=1, max_values=4)
        self.mode = mode

    async def callback(self, interaction: discord.Interaction):
        win_counts[self.mode] += 1
        for user in self.values:
            user_siege[user.id] = user_siege.get(user.id, 0) + 1
            user_mode_wins.setdefault(user.id, {})
            user_mode_wins[user.id][self.mode] = user_mode_wins[user.id].get(self.mode, 0) + 1
        save_data()
        await update_leaderboard(interaction.guild)
        await interaction.response.send_message(f"Sieg für **{self.mode}** eingetragen! 🎉", ephemeral=True)

class PlayerSelectView(discord.ui.View):
    def __init__(self, mode):
        super().__init__(timeout=60)
        self.add_item(PlayerSelect(mode))

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
    await update_leaderboard(ctx.guild, ctx.channel)

@bot.command()
async def setup(ctx):
    embed = discord.Embed(title="📊 Warzone Leaderboard", description="Lade Daten...", color=discord.Color.blue())
    message = await ctx.send(embed=embed)
    leaderboard_message["channel_id"] = message.channel.id
    leaderboard_message["message_id"] = message.id
    save_data()
    await update_leaderboard(ctx.guild)
    await ctx.send("✅ Leaderboard eingerichtet und wird ab jetzt automatisch aktualisiert.")

async def update_leaderboard(guild, channel=None):
    if not leaderboard_message["channel_id"] or not leaderboard_message["message_id"]:
        return

    channel = channel or guild.get_channel(leaderboard_message["channel_id"])
    if not channel:
        return

    try:
        message = await channel.fetch_message(leaderboard_message["message_id"])
    except:
        return

    if not user_siege:
        embed = discord.Embed(title="📊 Warzone Leaderboard", description="Noch keine Siege vergeben.", color=discord.Color.red())
        return await message.edit(embed=embed)

    sorted_users = sorted(user_siege.items(), key=lambda x: x[1], reverse=True)
    leaderboard_text = ""
    for i, (user_id, count) in enumerate(sorted_users, start=1):
        member = guild.get_member(user_id)
        if not member:
            continue
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🎖️"
        leaderboard_text += f"{medal} {i}. {member.display_name} – {count} Siege\n"

    mode_stats = ""
    for user_id, modes_dict in user_mode_wins.items():
        member = guild.get_member(user_id)
        if not member:
            continue
        stats = ", ".join(f"{mode}: {count}" for mode, count in modes_dict.items())
        mode_stats += f"🔸 {member.display_name}: {stats}\n"

    embed = discord.Embed(title="📊 Warzone Leaderboard", color=discord.Color.purple())
    embed.add_field(name="🏅 Aktuelle Platzierung", value=leaderboard_text or "Keine Daten", inline=False)
    embed.add_field(name="📌 Modus-Übersicht", value=mode_stats or "Keine Daten", inline=False)
    embed.set_footer(text="🔁 Dieses Leaderboard wird automatisch aktualisiert.")
    await message.edit(embed=embed)

load_data()
bot.run(os.getenv("DISCORD_TOKEN"))
