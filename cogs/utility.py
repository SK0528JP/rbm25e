import discord
from discord.ext import commands
from discord import app_commands

class Utility(commands.Cog):
    def __init__(self, bot, ledger):
        self.bot = bot
        self.ledger = ledger

    @app_commands.command(name="help", description="Rb m/25 の操作ガイドを表示します")
    async def help_command(self, it: discord.Interaction):
        embed = discord.Embed(
            title="🌿 Rb m/25 システムガイド",
            description=(
                "### 💎 資産と貢献度\n- **貢献度 (XP)**: チャットで蓄積。\n- **資産 (Credits)**: 通貨。\n\n"
                "### 📜 コマンド一覧\n"
                "- `/status` : 自分の簡易ステータス\n- `/user` : 詳細プロファイル（ID検索対応版）\n"
                "- `/ranking` : ランキング表示\n- `/pay` : 送金\n"
                "- `/janken` : じゃんけん\n- `/fortune` : おみくじ\n- `/ping` : 応答速度"
            ),
            color=0x475569
        )
        await it.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="status", description="自分の簡易ステータスを表示します")
    async def status(self, it: discord.Interaction):
        u = self.ledger.get_user(it.user.id)
        embed = discord.Embed(title=f"{it.user.display_name} の照会結果", color=0xf8fafc)
        embed.add_field(name="データ", value=f"💰: {u.get('money', 0):,} cr\n✨: {u.get('xp', 0):,} XP")
        await it.response.send_message(embed=embed)

    @app_commands.command(name="ping", description="応答速度を確認します")
    async def ping(self, it: discord.Interaction):
        await it.response.send_message(f"📡 `{round(self.bot.latency * 1000)}ms`", ephemeral=True)

async def setup(bot):
    from __main__ import ledger_instance
    await bot.add_cog(Utility(bot, ledger_instance))
