import discord
from discord.ext import commands, tasks
import os
from datetime import datetime, timedelta, timezone
from ledger import Ledger

# --- 環境設定 ---
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GIST_ID = os.getenv("GIST_ID")
GITHUB_TOKEN = os.getenv("MY_GITHUB_TOKEN")

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
        self.start_time = datetime.now(JST)
        # 既存Cogが「from __main__ import ledger_instance」としている場合に対応
        self.ledger = Ledger(GIST_ID, GITHUB_TOKEN) if GIST_ID and GITHUB_TOKEN else None
        global ledger_instance
        ledger_instance = self.ledger

    async def setup_hook(self):
        print("--- [SYSTEM BOOT] ---")
        cogs_list = [
            "cogs.status", "cogs.economy", "cogs.admin",
            "cogs.entertainment", "cogs.roulette", "cogs.user",
            "cogs.ping", "cogs.help", "cogs.exchange", "cogs.study"
        ]
        
        for cog in cogs_list:
            try:
                await self.load_extension(cog)
                print(f"✅ Loaded: {cog}")
            except Exception as e:
                print(f"❌ Failed: {cog} | {e}")

        # GUILD_IDを廃止し、常にグローバル同期を行う
        try:
            print("🛰️ Synchronizing global commands...")
            await self.tree.sync()
            print("✨ Global sync requested.")
        except Exception as e:
            print(f"⚠️ Sync failed: {e}")

        self.update_status.start()

    @tasks.loop(seconds=10)
    async def update_status(self):
        if not self.is_ready():
            return
        
        try:
            # レイテンシ（遅延）の計算
            latency = round(self.latency * 1000)
            
            # アップタイムの計算
            now = datetime.now(JST)
            uptime = now - self.start_time
            hours, remainder = divmod(int(uptime.total_seconds()), 3600)
            minutes, _ = divmod(remainder, 60)
            
            # 曜日のリスト
            wd_list = ["月", "火", "水", "木", "金", "土", "日"]
            time_str = now.strftime(f"%Y/%m/%d({wd_list[now.weekday()]}) %H:%M")
            
            # ステータス文字列の組み立て
            status_text = f"Lat: {latency}ms | Up: {hours}h {minutes}m | {time_str} JST"
            
            await self.change_presence(
                status=discord.Status.idle,
                activity=discord.Activity(type=discord.ActivityType.watching, name=status_text)
            )
        except Exception as e:
            print(f"❌ status_loop Error: {e}")

# 他のCogが import できるようにグローバル変数として定義
ledger_instance = None
bot = Rb_m25_Bot()

@bot.event
async def on_ready():
    print(f"--- Rb m/25 System Online ---")
    print(f"Logged in as: {bot.user.name}")
    print(f"-----------------------------")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    if bot.ledger:
        u = bot.ledger.get_user(message.author.id)
        u["xp"] += 1
        if u["xp"] % 30 == 0:
            bot.ledger.save()

    await bot.process_commands(message)

if TOKEN:
    bot.run(TOKEN)
