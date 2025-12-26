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
GUILD_ID = 1062900513017962576  # ← 【重要】ここにあなたのサーバーIDを入れてください

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
        print("--- [COMMAND RECOVERY INITIATED] ---")
        
        # 1. すべてのCogを読み込み
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

        # 2. 強制同期セクション
        if GUILD_ID:
            try:
                target_guild = discord.Object(id=GUILD_ID)
                
                print(f"♻️ Guild {GUILD_ID} のコマンドキャッシュをクリア中...")
                # 一旦そのサーバーのコマンドを空にする
                self.tree.clear_commands(guild=target_guild)
                await self.tree.sync(guild=target_guild)
                
                print("🛰️ 最新の全コマンドをサーバーに再同期中...")
                # グローバル（今読み込んだ全Cogのコマンド）をサーバーにコピー
                self.tree.copy_global_to(guild=target_guild)
                await self.tree.sync(guild=target_guild)
                
                print("✨ サーバーへの強制同期が完了しました。")
            except Exception as e:
                print(f"⚠️ サーバー同期中にエラー (無視して続行): {e}")

        # 3. 全体（グローバル）同期も実行
        try:
            await self.tree.sync()
            print("🌎 グローバル同期リクエスト送信完了。")
        except Exception as e:
            print(f"⚠️ グローバル同期エラー: {e}")

        print("--- [SETUP HOOK FINISHED] ---")
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
            print(f"❌ status_loop Error: {e}")

bot = Rb_m25_Bot()

@bot.event
async def on_ready():
    print(f"--- Rb m/25 System Online ---")
    print(f"Logged in as: {bot.user.name}")
    print(f"Ready to serve '同志たち' server.")
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
            print(f"💾 Auto-saved data for {message.author.display_name}")

    await bot.process_commands(message)

if TOKEN:
    bot.run(TOKEN)
else:
    print("❌ Error: DISCORD_BOT_TOKEN is missing.")
