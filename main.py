import discord
from discord.ext import commands, tasks
import os
from datetime import datetime, timedelta, timezone
from ledger import Ledger

# --- 環境設定 ---
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GIST_ID = os.getenv("GIST_ID")
GITHUB_TOKEN = os.getenv("MY_GITHUB_TOKEN")
# 同志たちのサーバーID（数字で入力）
GUILD_ID = None  # ← ここをあなたのサーバーIDに！

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
        self.ledger = Ledger(GIST_ID, GITHUB_TOKEN) if GIST_ID and GITHUB_TOKEN else None

    async def setup_hook(self):
        print("--- [DEBUG] setup_hook 開始 ---")
        
        cogs_list = [
            "cogs.status", "cogs.economy", "cogs.admin",
            "cogs.entertainment", "cogs.roulette", "cogs.user",
            "cogs.ping", "cogs.help", "cogs.exchange", "cogs.study"
        ]
        
        for cog in cogs_list:
            try:
                await self.load_extension(cog)
                print(f"✅ Module Loaded: {cog}")
            except Exception as e:
                print(f"❌ Failed to load {cog}: {e}")

        # --- 同期処理の最適化 ---
        try:
            if GUILD_ID:
                print(f"🛰️ 同志たちのサーバー ({GUILD_ID}) へ同期を開始...")
                target_guild = discord.Object(id=GUILD_ID)
                self.tree.copy_global_to(guild=target_guild)
                await self.tree.sync(guild=target_guild)
                print("✅ サーバー専用同期 完了")
            
            # グローバル同期はレート制限回避のため、必要最低限に
            # await self.tree.sync() 
            # print("✅ グローバル同期 完了")
            
        except Exception as e:
            print(f"⚠️ 同期中にエラー発生 (無視して続行): {e}")

        print("--- [DEBUG] setup_hook 終了。ループを開始します ---")
        self.update_status.start()

    @tasks.loop(seconds=10)
    async def update_status(self):
        if not self.is_ready():
            return
        
        try:
            latency = round(self.latency * 1000)
            now = datetime.now(JST)
            uptime = now - self.start_time
            
            hours, remainder = divmod(int(uptime.total_seconds()), 3600)
            minutes, _ = divmod(remainder, 60)
            
            wd_list = ["月", "火", "水", "木", "金", "土", "日"]
            time_str = now.strftime(f"%Y/%m/%d({wd_list[now.weekday()]}) %H:%M")
            
            status_text = f"Lat: {latency}ms | Up: {hours}h {minutes}m | {time_str} JST"
            
            await self.change_presence(
                status=discord.Status.idle,
                activity=discord.Activity(type=discord.ActivityType.watching, name=status_text)
            )
        except Exception as e:
            print(f"❌ status_loop エラー: {e}")

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
            print(f"💾 Auto-saved: {message.author.display_name}")

    await bot.process_commands(message)

if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ Error: DISCORD_BOT_TOKEN is missing.")
