import discord
from discord.ext import commands
from discord import app_commands
import os
import traceback
from ledger import Ledger
from dotenv import load_dotenv

# 1. 環境変数のロード
load_dotenv()

# 2. データの初期化 (Gist同期機能付きLedger)
# ※ledger.py 内で lang キーを扱っていても、この構成なら問題ありません
ledger_instance = Ledger()

class Rbm25Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        super().__init__(
            command_prefix="!", 
            intents=intents,
            status=discord.Status.online,
            activity=discord.Activity(
                type=discord.ActivityType.watching, 
                name="Rb m/25 システム稼働中"
            )
        )

    async def setup_hook(self):
        """
        モジュールの読み込みとコマンドの同期
        """
        # 読み込むコグのリスト
        cogs_list = [
            "cogs.utility",
            "cogs.economy",
            "cogs.entertainment",
            "cogs.admin"
        ]

        print("--- Rb m/25 | 初期化シーケンス開始 ---")
        for extension in cogs_list:
            try:
                await self.load_extension(extension)
                print(f"[成功] モジュール読み込み完了: {extension}")
            except Exception:
                print(f"[失敗] モジュール: {extension}\n{traceback.format_exc()}")

        # スラッシュコマンドをDiscordサーバーへ同期
        try:
            print("[システム] コマンドを同期中...")
            synced = await self.tree.sync()
            print(f"[システム] オンライン: {len(synced)} 個のコマンドを同期しました。")
        except Exception:
            print(f"[致命的] ツリー同期失敗:\n{traceback.format_exc()}")

bot = Rbm25Bot()

# --- 3. グローバル・エラーハンドラー ---
@bot.tree.error
async def on_app_command_error(it: discord.Interaction, error: app_commands.AppCommandError):
    """
    エラー発生時に詳細をログに出力し、ユーザーに通知します
    """
    orig_error = getattr(error, "original", error)
    
    # クールダウン（連投防止）エラー
    if isinstance(error, app_commands.CommandOnCooldown):
        await it.response.send_message(f"しばらく待ってから実行してください（残り {error.retry_after:.1f}秒）", ephemeral=True)
        return

    # コンソールへの詳細出力
    print("\n" + "!"*40)
    print("🔴 コマンドエラー報告")
    print(f"コマンド: /{it.command.name if it.command else '不明'}")
    print(f"ユーザー: {it.user}")
    print(f"エラー型: {type(orig_error).__name__}")
    print(f"内容: {orig_error}")
    print("-" * 20)
    traceback.print_exception(type(orig_error), orig_error, orig_error.__traceback__)
    print("!"*40 + "\n")

    # ユーザーへの応答
    if not it.response.is_done():
        await it.response.send_message(
            f"⚠️ **システムエラーが発生しました**\n型: `{type(orig_error).__name__}`\n管理者に連絡してください。", 
            ephemeral=True
        )

# --- 4. 貢献度(XP) 蓄積ロジック ---
last_xp_time = {}

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    now = discord.utils.utcnow()
    uid = message.author.id
    
    # 3秒に1回、2 XP を付与
    if uid not in last_xp_time or (now - last_xp_time[uid]).total_seconds() > 3:
        u = ledger_instance.get_user(uid)
        u["xp"] += 2
        ledger_instance.save()
        last_xp_time[uid] = now
        
    await bot.process_commands(message)

# --- 5. 起動完了通知 ---
@bot.event
async def on_ready():
    print("--------------------------------------------------")
    print(f"  Rb m/25 | 日本語専用インターフェース")
    print(f"  稼働中: {bot.user.name}")
    print("--------------------------------------------------")

# --- 6. ボットの実行 ---
if __name__ == "__main__":
    token = os.getenv("DISCORD_BOT_TOKEN")
    if token:
        bot.run(token)
    else:
        print("[致命的] DISCORD_BOT_TOKEN が環境変数に見つかりません。")
