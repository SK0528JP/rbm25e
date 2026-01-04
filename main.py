import discord
from discord.ext import commands, tasks
import os
from datetime import datetime, timedelta, timezone
from ledger import Ledger

# --- [SYSTEM CONFIGURATION] ---
# 環境変数の読み込み
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GIST_ID = os.getenv("GIST_ID")
GITHUB_TOKEN = os.getenv("MY_GITHUB_TOKEN")

# タイムゾーン設定 (JST)
JST = timezone(timedelta(hours=9), 'JST')

# グローバル変数の事前定義 (Cogsからの参照用)
ledger_instance = None

# --- [INTENTS & PERMISSIONS] ---
# 全方位監視モード: メンバー、メッセージ、プレゼンス(ステータス)を有効化
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True # ⚠️ 必須: これによりSpotifyやゲーム情報を取得可能

class Rb_m25_Bot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None
        )
        self.start_time = datetime.now(JST)
        
        # Ledger (資産管理システム) の初期化
        # 設定が不足している場合は None として安全に起動
        if GIST_ID and GITHUB_TOKEN:
            self.ledger = Ledger(GIST_ID, GITHUB_TOKEN)
            print("💎 Ledger System: Connected")
        else:
            self.ledger = None
            print("⚠️ Ledger System: Disabled (Missing Env Vars)")
        
        # グローバル変数へのバインド
        global ledger_instance
        ledger_instance = self.ledger

    async def setup_hook(self):
        print("\n--- [SYSTEM BOOT SEQUENCE] ---")
        
        # 読み込む拡張モジュール (Cogs) のリスト
        cogs_list = [
            "cogs.status", 
            "cogs.economy", 
            "cogs.admin",
            "cogs.entertainment", 
            "cogs.roulette", 
            "cogs.user",       # 精密調査ユニット
            "cogs.ping", 
            "cogs.help",
            "cogs.gallery", 
            "cogs.exchange",
            "cogs.ranking",
            "cogs.broadcast",
            "cogs.server",
            "cogs.wt",         # 兵器データユニット
            "cogs.ai",
            "cogs.countdown",  # 戦術時計ユニット
            "cogs.fishing", 
            "cogs.contact",
            "cogs.translator",
            "cogs.study"
        ]
        
        # モジュールのロード
        for cog in cogs_list:
            try:
                await self.load_extension(cog)
                print(f"✅ Loaded: {cog}")
            except commands.ExtensionError as e:
                print(f"❌ Failed: {cog} | {e}")

        # スラッシュコマンドの同期
        try:
            print("🛰️ Synchronizing command tree...")
            await self.tree.sync()
            print("✨ Global commands synced.")
        except Exception as e:
            print(f"⚠️ Sync failed: {e}")

        # バックグラウンドタスクの開始
        self.update_status.start()
        self.auto_save.start()
        print("--- [SYSTEM READY] ---\n")

    # --- Task: 自動保存 (10分間隔) ---
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

    # --- Task: ステータス更新 (10秒間隔) ---
    @tasks.loop(seconds=10)
    async def update_status(self):
        # Botが準備完了していない場合はスキップ
        if not self.is_ready():
            return
        
        try:
            # レイテンシ (ms)
            latency = round(self.latency * 1000)
            
            # 稼働時間 (Uptime)
            now = datetime.now(JST)
            uptime = now - self.start_time
            total_seconds = int(uptime.total_seconds())
            days, remainder = divmod(total_seconds, 86400)
            hours, remainder = divmod(remainder, 3600)
            minutes, _ = divmod(remainder, 60)
            
            # Uptime表記の整形 (例: 1d 2h 30m)
            uptime_str = f"{hours}h {minutes}m"
            if days > 0:
                uptime_str = f"{days}d " + uptime_str

            # 日時表記
            wd_list = ["月", "火", "水", "木", "金", "土", "日"]
            time_str = now.strftime(f"%m/%d({wd_list[now.weekday()]}) %H:%M")
            
            # ステータス文言の構築
            status_text = f"Lat: {latency}ms | Up: {uptime_str} | {time_str}"
            
            await self.change_presence(
                status=discord.Status.idle, # 北欧的静寂 (Idle)
                activity=discord.Activity(type=discord.ActivityType.watching, name=status_text)
            )
        except Exception as e:
            print(f"⚠️ Status Loop Warning: {e}")

    @update_status.before_loop
    async def before_update_status(self):
        await self.wait_until_ready()

# Botインスタンスの生成
bot = Rb_m25_Bot()

@bot.event
async def on_ready():
    print(f"✅ Logged in as: {bot.user.name} (ID: {bot.user.id})")
    print(f"💎 Intents: Presences={'✅' if intents.presences else '❌'}, Members={'✅' if intents.members else '❌'}")

@bot.event
async def on_message(message):
    # Bot自身のメッセージは無視
    if message.author.bot:
        return
    
    # XPシステムの処理
    if bot.ledger:
        try:
            u = bot.ledger.get_user(message.author.id)
            u["xp"] = u.get("xp", 0) + 1
            
            # 30メッセージごとに保存 (頻繁なAPIコールを避けるため)
            if u["xp"] % 30 == 0:
                bot.ledger.save()
        except Exception as e:
            print(f"❌ Experience System Error: {e}")

    # コマンド処理へ
    await bot.process_commands(message)

# メイン実行ブロック
if __name__ == "__main__":
    if not TOKEN:
        print("❌ CRITICAL ERROR: 'DISCORD_BOT_TOKEN' environment variable is missing.")
    else:
        bot.run(TOKEN)
