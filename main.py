import discord
from discord.ext import commands
from discord import app_commands
import os
import asyncio
from ledger import Ledger
from dotenv import load_dotenv

# 1. 環境変数のロード (.envからTOKENを取得)
load_dotenv()

# 2. データセンターの初期化
# すべてのCogはこの唯一のインスタンスを共有します
ledger_instance = Ledger()

class Rbm25Bot(commands.Bot):
    def __init__(self):
        # インテントの設定 (メンバー管理とメッセージ読み取りを有効化)
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        super().__init__(
            command_prefix="!", 
            intents=intents,
            status=discord.Status.idle,
            activity=discord.Activity(
                type=discord.ActivityType.watching, 
                name="Rb m/25 System Status"
            )
        )

    async def setup_hook(self):
        """
        システム起動時にモジュールをロードし、スラッシュコマンドをDiscordへ登録します。
        """
        # ロード対象のCogリスト
        cogs_list = [
            "cogs.utility",
            "cogs.economy",
            "cogs.entertainment",
            "cogs.admin"
        ]

        print("--- Rb m/25 | Initialization Sequence ---")
        for extension in cogs_list:
            try:
                # 拡張機能のロード
                await self.load_extension(extension)
                print(f"[SUCCESS] Module: {extension}")
            except Exception as e:
                print(f"[FAILURE] Module: {extension} | Reason: {e}")

        # グローバルコマンドの同期 (Discord側にコマンドを表示させるための最重要処理)
        try:
            print("[SYSTEM] Synchronizing global command tree...")
            synced = await self.tree.sync()
            print(f"[SYSTEM] Interface Online: {len(synced)} commands synced.")
        except Exception as e:
            print(f"[CRITICAL] Tree sync failed: {e}")

bot = Rbm25Bot()

# --- 3. グローバル・エラーハンドラー ---
@bot.tree.error
async def on_app_command_error(it: discord.Interaction, error: app_commands.AppCommandError):
    """コマンド実行中のエラーを補足し、ユーザーへ通知します。"""
    if isinstance(error, app_commands.CommandOnCooldown):
        await it.response.send_message(f"Cooldown: {error.retry_after:.1f}s", ephemeral=True)
    else:
        print(f"[LOG ERROR] {error}")
        if not it.response.is_done():
            await it.response.send_message("An internal system error has occurred.", ephemeral=True)

# --- 4. 貢献度(XP) 蓄積ユニット ---
last_xp_time = {}

@bot.event
async def on_message(message):
    # Bot自身の発言は無視
    if message.author.bot:
        return
    
    now = discord.utils.utcnow()
    uid = message.author.id
    
    # 3秒間のインターバルを置いてXPを加算
    if uid not in last_xp_time or (now - last_xp_time[uid]).total_seconds() > 3:
        ledger_instance.add_xp(uid, 2)
        # ledger.py 内で自動セーブと lang 補完が行われます
        ledger_instance.save()
        last_xp_time[uid] = now
        
    # プレフィックスコマンドの処理 (必要な場合)
    await bot.process_commands(message)

# --- 5. 起動完了ログ ---
@bot.event
async def on_ready():
    print("--------------------------------------------------")
    print(f"  Rb m/25 | Swedish Modern System Interface")
    print(f"  Operational as: {bot.user.name}")
    print(f"  Status: Fully Integrated")
    print("--------------------------------------------------")

# --- 6. システム・エントリーポイント ---
if __name__ == "__main__":
    token = os.getenv("DISCORD_BOT_TOKEN")
    if token:
        bot.run(token)
    else:
        print("[CRITICAL] Termination: DISCORD_BOT_TOKEN not found in environment.")
