import discord  # 小文字に修正
from discord.ext import commands, tasks
import os
from datetime import datetime, timedelta, timezone
from ledger import Ledger

# --- [SYSTEM CONFIGURATION] ---
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GIST_ID = os.getenv("GIST_ID")
GITHUB_TOKEN = os.getenv("MY_GITHUB_TOKEN")

JST = timezone(timedelta(hours=9), 'JST')

ledger_instance = None

# --- [INTENTS & PERMISSIONS] ---
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True 
intents.invites = True  # 招待トラッカー用に明示的に有効化

class Rb_m25_Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None
        )
        self.start_time = datetime.now(JST)
        
        if GIST_ID and GITHUB_TOKEN:
            self.ledger = Ledger(GIST_ID, GITHUB_TOKEN)
            print("💎 Ledger System: Connected")
        else:
            self.ledger = None
            print("⚠️ Ledger System: Disabled (Missing Env Vars)")
        
        global ledger_instance
        ledger_instance = self.ledger

    async def setup_hook(self):
        print("\n--- [SYSTEM BOOT SEQUENCE] ---")
        
        cogs_list = [
            "cogs.status", 
            "cogs.economy", 
            "cogs.admin",
            "cogs.entertainment", 
            "cogs.roulette", 
            "cogs.user",
            "cogs.ping", 
            "cogs.help",
            "cogs.gallery", 
            "cogs.exchange",
            "cogs.ranking",
            "cogs.broadcast",
            "cogs.server",
            "cogs.wt",
            "cogs.ai",
            "cogs.countdown",
            "cogs.fishing", 
            "cogs.contact",
            "cogs.translator",
            "cogs.invite_search", # 招待追跡ユニット
            "cogs.study"
        ]
        
        for cog in cogs_list:
            try:
                await self.load_extension(cog)
                print(f"✅ Loaded: {cog}")
            except commands.ExtensionError as e:
                print(f"❌ Failed: {cog} | {e}")

        try:
            print("🛰️ Synchronizing command tree...")
            await self.tree.sync()
            print("✨ Global commands synced.")
        except Exception as e:
            print(f"⚠️ Sync failed: {e}")

        self.update_status.start()
        self.auto_save.start()
        print("--- [SYSTEM READY] ---\n")

    @tasks.loop(minutes=10)
    async def auto_save(self):
        if self.ledger:
            try:
                self.ledger.save()
                now_str = datetime.now(JST).strftime('%H:%M')
                print(f"💾 [AUTO-SAVE] {now_str} Data synchronized to Gist.")
            except Exception as e:
                print(f"❌ [AUTO-SAVE ERROR] {e}")

    @auto_save.before_loop
    async def before_auto_save(self):
        await self.wait_until_ready()

    @tasks.loop(seconds=10)
    async def update_status(self):
        if not self.is_ready():
            return
        try:
            latency = round(self.latency * 1000)
            now = datetime.now(JST)
            uptime = now - self.start_time
            total_seconds = int(uptime.total_seconds())
            days, remainder = divmod(total_seconds, 86400)
            hours, remainder = divmod(remainder, 3600)
            minutes, _ = divmod(remainder, 60)
            
            uptime_str = f"{hours}h {minutes}m"
            if days > 0:
                uptime_str = f"{days}d " + uptime_str

            wd_list = ["月", "火", "水", "木", "金", "土", "日"]
            time_str = now.strftime(f"%m/%d({wd_list[now.weekday()]}) %H:%M")
            status_text = f"Lat: {latency}ms | Up: {uptime_str} | {time_str}"
            
            await self.change_presence(
                status=discord.Status.idle,
                activity=discord.Activity(type=discord.ActivityType.watching, name=status_text)
            )
        except Exception as e:
            print(f"⚠️ Status Loop Warning: {e}")

    @update_status.before_loop
    async def before_update_status(self):
        await self.wait_until_ready()

bot = Rb_m25_Bot()

@bot.event
async def on_ready():
    print(f"✅ Logged in as: {bot.user.name} (ID: {bot.user.id})")
    # インテントの状態を起動ログに表示
    print(f"💎 Intents: Presence={'✅' if intents.presences else '❌'}, Members={'✅' if intents.members else '❌'}, Invites={'✅' if intents.invites else '❌'}")

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    if bot.ledger:
        try:
            u = bot.ledger.get_user(message.author.id)
            u["xp"] = u.get("xp", 0) + 1
            # 内部データ更新のみ。セーブはauto_saveタスクに任せるのが安全
        except Exception as e:
            print(f"❌ Experience System Error: {e}")

    await bot.process_commands(message)

if __name__ == "__main__":
    if not TOKEN:
        print("❌ CRITICAL ERROR: 'DISCORD_BOT_TOKEN' environment variable is missing.")
    else:
        bot.run(TOKEN)
