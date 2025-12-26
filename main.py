import discord
from discord.ext import commands, tasks # tasksを追加
import os
import asyncio
from datetime import datetime
from ledger import Ledger

# --- 基本設定 ---
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GIST_ID = os.getenv("GIST_ID")
GITHUB_TOKEN = os.getenv("MY_GITHUB_TOKEN")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class Rb_m25_Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None
        )
        self.start_time = datetime.now() # 稼働開始時間を記録

    async def setup_hook(self):
        cogs_list = [
            "cogs.status", "cogs.economy", "cogs.admin",
            "cogs.entertainment", "cogs.roulette", "cogs.user",
            "cogs.ping", "cogs.help", "cogs.exchange"
        ]
        for cog in cogs_list:
            try:
                await self.load_extension(cog)
                print(f"✅ Module Loaded: {cog}")
            except Exception as e:
                print(f"❌ Failed to load {cog}: {e}")

        await self.tree.sync()
        print("🛰️ Command Tree Synced.")
        
        # ステータス更新ループを開始
        self.update_status.start()

    # 60秒ごとにステータスを更新するタスク
    @tasks.loop(seconds=60)
    async def update_status(self):
        if not self.is_ready():
            return

        # レイテンシの取得
        latency = round(self.bot.latency * 1000) if hasattr(self, 'bot') else round(bot.latency * 1000)
        
        # 稼働時間の計算
        uptime = datetime.now() - self.start_time
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, _ = divmod(remainder, 60)
        
        # アクティビティ文字列の構築
        # 例: "Latency: 42ms | Uptime: 2h 15m"
        status_text = f"Lat: {latency}ms | Up: {hours}h {minutes}m"
        
        await self.change_presence(
            status=discord.Status.idle,
            activity=discord.Activity(
                type=discord.ActivityType.watching, 
                name=status_text
            )
        )

bot = Rb_m25_Bot()
ledger_instance = Ledger(GIST_ID, GITHUB_TOKEN)

@bot.event
async def on_ready():
    print(f"--- Rb m/25 System Online ---")
    print(f"Node Name: {bot.user.name}")
    print(f"Status   : IDLE (Monitoring Mode)")
    print(f"-----------------------------")

# ... (on_message以降は変更なし)
bot.run(TOKEN)
