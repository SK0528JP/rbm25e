import os
import asyncio
import random
from datetime import datetime, timezone, timedelta

import discord
from discord.ext import commands, tasks
from discord import app_commands

# ===== 基本設定 =====
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True

JST = timezone(timedelta(hours=9))

# ===== Botクラス ===== 
class MyBot(commands.Bot):
    async def setup_hook(self):
        try:
            await self.tree.sync()
            print("Slash commands synced")
        except Exception as e:
            print(f"Sync failed: {e}")

bot = MyBot(command_prefix="!", intents=intents)

# ===== on_ready =====
@bot.event
async def on_ready():
    await bot.change_presence(
        status=discord.Status.idle,
        activity=discord.Activity(
            type=discord.ActivityType.listening,
            name="🎵 労働中"
        )
    )
    print(f"Logged in as {bot.user}")
    time_signal.start()

# ===== /ping =====
@bot.tree.command(name="ping", description="BOTの遅延を表示")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f"Pong 🏓 {latency}ms")

# ===== じゃんけん =====
class JankenView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    async def play(self, interaction: discord.Interaction, user_hand: str):
        bot_hand = random.choice(["グー", "チョキ", "パー"])

        if user_hand == bot_hand:
            result = "引き分け"
        elif (
            (user_hand == "グー" and bot_hand == "チョキ") or
            (user_hand == "チョキ" and bot_hand == "パー") or
            (user_hand == "パー" and bot_hand == "グー")
        ):
            result = "勝ち"
        else:
            result = "負け"

        await interaction.response.send_message(
            f"{interaction.user.mention}\n"
            f"あなた：{user_hand}\n"
            f"BOT：{bot_hand}\n"
            f"結果：{result}",
            ephemeral=False
        )

    @discord.ui.button(label="グー", style=discord.ButtonStyle.primary)
    async def rock(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.play(interaction, "グー")
 
    @discord.ui.button(label="チョキ", style=discord.ButtonStyle.primary)
    async def scissors(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.play(interaction, "チョキ")

    @discord.ui.button(label="パー", style=discord.ButtonStyle.primary)
    async def paper(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.play(interaction, "パー")

@bot.tree.command(name="janken", description="じゃんけんをする")
async def janken(interaction: discord.Interaction):
    await interaction.response.send_message(
        "じゃんけん開始",
        view=JankenView()
    )
    
# ===== 時報 =====
@tasks.loop(seconds=30)
async def time_signal():
    now_utc = datetime.now(timezone.utc)
    now_jst = now_utc.astimezone(JST)

    if now_jst.hour == 0 and now_jst.minute == 0:
        await send_time_signal("JST")

    if now_utc.hour == 0 and now_utc.minute == 0:
        await send_time_signal("UTC")

async def send_time_signal(label: str):
    for guild in bot.guilds:
        channel = guild.system_channel
        if channel:
            try:
                await channel.send(f"⏰ {label} 00:00 時報")
            except:
                pass

# ===== 起動 =====
bot.run(TOKEN)
