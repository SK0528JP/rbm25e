import discord
from discord.ext import commands
import os
from ledger import Ledger

# 1. データの初期化（最優先）
# ここでインスタンス化し、各Cogへ「手渡し」します
ledger_instance = Ledger()

class Rbm25Bot(commands.Bot):
    def __init__(self):
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
        モジュールのロードとコマンド同期。
        """
        # ロード対象のリスト
        cogs_list = [
            "cogs.utility",
            "cogs.economy",
            "cogs.entertainment",
            "cogs.admin"
        ]

        for extension in cogs_list:
            try:
                # 重要：extensionをロードする際、setup関数が呼ばれます
                await self.load_extension(extension)
                print(f"[SYSTEM] Module loaded: {extension}")
            except Exception as e:
                # ここでエラーが出ている場合、ターミナルに表示されます
                print(f"[ERROR] Failed to load module {extension}: {e}")

        # スラッシュコマンドをDiscordサーバーへ送信
        await self.tree.sync()
        print("[SYSTEM] Global command synchronization completed.")

bot = Rbm25Bot()

# --- 各Cogが利用するためのledger参照用関数（循環インポート防止） ---
# Cog側で from main import ledger とせず、このインスタンスを setup で渡します

@bot.event
async def on_ready():
    print("--------------------------------------------------")
    print(f"  Rb m/25 | Swedish Modern System Interface")
    print(f"  Status: Operational as {bot.user.name}")
    print("--------------------------------------------------")

# XP付与ロジック
last_xp_time = {}
@bot.event
async def on_message(message):
    if message.author.bot: return
    now = discord.utils.utcnow()
    uid = message.author.id
    if uid not in last_xp_time or (now - last_xp_time[uid]).total_seconds() > 3:
        ledger_instance.add_xp(uid, 2)
        ledger_instance.save()
        last_xp_time[uid] = now
    await bot.process_commands(message)

if __name__ == "__main__":
    token = os.getenv("DISCORD_BOT_TOKEN")
    if token:
        bot.run(token)
    else:
        print("[CRITICAL] Token not found.")
