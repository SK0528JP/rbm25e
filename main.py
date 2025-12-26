import discord
from discord.ext import commands
import os
import asyncio
from ledger import Ledger

# 1. データ管理ユニットの初期化
ledger = Ledger()

class MyBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        # ステータスを「退席中(idle)」に、アクティビティを「システム稼働中」に設定
        super().__init__(
            command_prefix="!", 
            intents=intents,
            status=discord.Status.idle,
            activity=discord.Activity(type=discord.ActivityType.watching, name="システム稼働状況")
        )

    async def setup_hook(self):
        # 拡張モジュールのロード処理
        cog_files = ["utility", "economy", "entertainment", "admin"]
        
        # モジュールを手動インポートして追加
        from cogs.utility import Utility
        from cogs.economy import Economy
        from cogs.entertainment import Entertainment
        from cogs.admin import Admin
        
        cogs_map = {
            "utility": Utility,
            "economy": Economy,
            "entertainment": Entertainment,
            "admin": Admin
        }

        for name, cog_class in cogs_map.items():
            try:
                await self.add_cog(cog_class(self, ledger))
                print(f"[SYSTEM] Extension loaded: {name}")
            except Exception as e:
                print(f"[ERROR] Failed to load extension {name}: {e}")

        # スラッシュコマンドの同期
        await self.tree.sync()
        print("[SYSTEM] Command synchronization completed.")

bot = MyBot()

# --- アクティビティ・ログ（XP加算処理） ---
last_xp_time = {}

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    now = discord.utils.utcnow()
    uid = message.author.id
    
    # 3秒のインターバル制限
    if uid not in last_xp_time or (now - last_xp_time[uid]).total_seconds() > 3:
        ledger.add_xp(uid, 2)
        ledger.save()
        last_xp_time[uid] = now

    await bot.process_commands(message)

# --- 起動ログ ---
@bot.event
async def on_ready():
    print(f"[INFO] Logged in as: {bot.user.name} (ID: {bot.user.id})")
    print(f"[INFO] Status: {bot.status} / activity: watching System Status")
    print("--------------------------------------------------")
    print("  Central Information System is now operational.  ")
    print("--------------------------------------------------")

# 実行ユニット
token = os.getenv("DISCORD_BOT_TOKEN")
bot.run(token)
