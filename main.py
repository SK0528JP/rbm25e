import discord
from discord import app_commands
from discord.ext import commands
import asyncio
import json
import os
from datetime import datetime, timezone, timedelta

# ========= 基本設定 =========
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CONFIG_FILE = "config.json"
# ============================

# ---------- config 読み書き ----------
def load_config():
    if not os.path.exists(CONFIG_FILE):
        data = {
            "jst_channel_id": None,
            "utc_channel_id": None
        }
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return data

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_config(data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

config = load_config()

# ---------- Bot ----------
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

# ---------- Ping ----------
@bot.tree.command(name="ping", description="Botの応答速度確認")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f"Pong | {latency}ms")

# ---------- じゃんけん（ボタン式） ----------
janken_rooms = {}  # {channel_id: {user_id: hand}}

WIN_MAP = {
    "rock": "scissors",
    "scissors": "paper",
    "paper": "rock"
}

class JankenView(discord.ui.View):
    def __init__(self, channel_id):
        super().__init__(timeout=60)
        self.channel_id = channel_id

    async def register(self, interaction, hand):
        room = janken_rooms.get(self.channel_id)
        if room is None:
            await interaction.response.send_message("じゃんけん未開始", ephemeral=True)
            return

        room[interaction.user.id] = hand
        await interaction.response.send_message("受付完了", ephemeral=True)

    @discord.ui.button(label="✊ グー", style=discord.ButtonStyle.primary)
    async def rock(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.register(interaction, "rock")

    @discord.ui.button(label="✌ チョキ", style=discord.ButtonStyle.success)
    async def scissors(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.register(interaction, "scissors")

    @discord.ui.button(label="✋ パー", style=discord.ButtonStyle.danger)
    async def paper(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.register(interaction, "paper")

@bot.tree.command(name="janken_start", description="じゃんけん開始")
async def janken_start(interaction: discord.Interaction):
    janken_rooms[interaction.channel_id] = {}
    view = JankenView(interaction.channel_id)
    await interaction.response.send_message("じゃんけん開始：ボタンを押せ", view=view)

@bot.tree.command(name="janken_result", description="じゃんけん結果表示")
async def janken_result(interaction: discord.Interaction):
    room = janken_rooms.get(interaction.channel_id)
    if not room or len(room) < 2:
        await interaction.response.send_message("参加者不足")
        return

    hands = set(room.values())

    if len(hands) != 2:
        await interaction.response.send_message("引き分け")
        janken_rooms.pop(interaction.channel_id)
        return

    h1, h2 = list(hands)
    win_hand = h1 if WIN_MAP[h1] == h2 else h2
    winners = [f"<@{uid}>" for uid, h in room.items() if h == win_hand]

    await interaction.response.send_message(f"勝者：{' '.join(winners)}")
    janken_rooms.pop(interaction.channel_id)

# ---------- 時報設定 ----------
@bot.tree.command(name="set_jst_channel", description="JST時報チャンネル設定")
async def set_jst_channel(interaction: discord.Interaction):
    config["jst_channel_id"] = interaction.channel_id
    save_config(config)
    await interaction.response.send_message("JST時報チャンネル設定完了")

@bot.tree.command(name="set_utc_channel", description="UTC時報チャンネル設定")
async def set_utc_channel(interaction: discord.Interaction):
    config["utc_channel_id"] = interaction.channel_id
    save_config(config)
    await interaction.response.send_message("UTC時報チャンネル設定完了")

# ---------- 時報ループ ----------
async def time_signal():
    await bot.wait_until_ready()
    sent_jst = False
    sent_utc = False

    while not bot.is_closed():
        now_utc = datetime.now(timezone.utc)
        now_jst = now_utc.astimezone(timezone(timedelta(hours=9)))

        if now_jst.hour == 0 and now_jst.minute == 0:
            if not sent_jst and config.get("jst_channel_id"):
                ch = bot.get_channel(config["jst_channel_id"])
                if ch:
                    await ch.send("【時報】日本標準時 0:00")
                sent_jst = True
        else:
            sent_jst = False

        if now_utc.hour == 0 and now_utc.minute == 0:
            if not sent_utc and config.get("utc_channel_id"):
                ch = bot.get_channel(config["utc_channel_id"])
                if ch:
                    await ch.send("【時報】UTC 0:00")
                sent_utc = True
        else:
            sent_utc = False

        await asyncio.sleep(30)

# ---------- 起動 ----------
@bot.event
async def on_ready():
    await bot.tree.sync()

    await bot.change_presence(
        status=discord.Status.idle,  # 退席中
        activity=discord.Activity(
            type=discord.ActivityType.listening,  # ♬ マーク
            name="労働中"
        )
    )

    bot.loop.create_task(time_signal())
    print(f"Logged in as {bot.user}")

bot.run(TOKEN)
