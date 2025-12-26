import discord
from discord.ext import commands, tasks
import os
import asyncio
from datetime import datetime, timedelta, timezone # timezone, timedeltaを追加
from ledger import Ledger

# --- 基本設定 ---
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GIST_ID = os.getenv("GIST_ID")
GITHUB_TOKEN = os.getenv("MY_GITHUB_TOKEN")

# JST (日本標準時) の定義
JST = timezone(timedelta(hours=9), 'JST')

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
        # 起動時刻をJSTで記録
        self.start_time = datetime.now(JST)

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

    # 10秒ごとにステータスを更新するタスク
    @tasks.loop(seconds=10)
    async def update_status(self):
        if not self.is_ready():
            return

        # 1. レイテンシの取得
        latency = round(self.latency * 1000)
        
        # 2. 稼働時間の計算
        now = datetime.now(JST)
        uptime = now - self.start_time
        hours, remainder = divmod(int(uptime.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        
        # 3. 現在時刻のフォーマット (JST)
        # 例: 2025/12/26 18:45:10
        time_str = now.strftime("%Y/%m/%d %H:%M:%S")
        
        # アクティビティ文字列の構築
        # 表示例: "Lat: 42ms | Up: 2h 15m | 2025/12/26 18:45:10 JST"
        status_text = f"Lat: {latency}ms | Up: {hours}h {minutes}m | {time_str} JST"
        
        await self.change_presence(
            status=discord.Status.idle, # 退席中
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
    print(f"Status   : IDLE (JST Monitoring Mode)")
    print(f"-----------------------------")

@bot.event
async def on_message(message):
    if message.author.bot or ledger_instance is None:
        return
    
    u = ledger_instance.get_user(message.author.id)
    u["xp"] += 1
    if u["xp"] % 30 == 0:
        ledger_instance.save()
    
    await bot.process_commands(message)

# 実行
bot.run(TOKEN)
