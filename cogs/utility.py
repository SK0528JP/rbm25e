import discord
from discord.ext import commands
from discord import app_commands

class Utility(commands.Cog):
    def __init__(self, bot, ledger):
        self.bot = bot
        self.ledger = ledger

    @app_commands.command(name="help", description="Rb m/25 の操作ガイドを表示します")
    async def help_command(self, it: discord.Interaction):
        """
        システムの全体像と主要コマンドを案内します。
        """
        embed = discord.Embed(
            title="🌿 Rb m/25 システムガイド",
            description=(
                "Rb m/25 は、北欧モダニズムの思想を取り入れたサーバー管理インフラです。\n\n"
                "### 💎 資産と貢献度\n"
                "- **貢献度 (XP)**: アクティビティに応じて蓄積される個人の実績です。\n"
                "- **資産 (Credits)**: 経済システム内で流通する仮想通貨です。\n\n"
                "### 📜 主要コマンドセクション\n"
                "- **`/status`** : 自身の現在のリソースをクイック確認します。\n"
                "- **`/user`** : 指定ユーザーの全公開情報を精密調査します。\n"
                "- **`/ranking`** : サーバー内の長者・貢献者の序列を表示します。\n"
                "- **`/pay`** : 他のユーザーへ資産を安全に送金します。\n"
                "- **`/roulette`** : 複数の選択肢から公平な抽選を行います。\n"
                "- **`/ping`** : システムの応答速度と接続品質を診断します。\n"
                "- **`/janken /fortune`** : 娯楽機能を提供します。"
            ),
            color=0x475569
        )
        embed.set_author(name="Rb m/25 Interface Terminal", icon_url=self.bot.user.display_avatar.url)
        embed.set_footer(text="Rb m/25 Infrastructure Division | Stability First")
        
        await it.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="status", description="自分の現在の簡易ステータスを表示します")
    async def status(self, it: discord.Interaction):
        """
        自分の資産とXPをパッと確認するための軽量コマンド。
        """
        u = self.ledger.get_user(it.user.id)
        
        embed = discord.Embed(color=0xf8fafc)
        embed.set_author(name=f"{it.user.display_name} の資産照会", icon_url=it.user.display_avatar.url)
        
        status_info = (
            f"💰 **保有資産**: {u.get('money', 0):,} cr\n"
            f"✨ **貢献度**: {u.get('xp', 0):,} XP"
        )
        embed.add_field(name="Data Retrieve Success", value=status_info, inline=False)
        embed.set_footer(text="Rb m/25 Quick Status Service")
        
        await it.response.send_message(embed=embed)

async def setup(bot):
    # main.pyで定義されているledgerのインスタンスをロード
    from __main__ import ledger_instance
    await bot.add_cog(Utility(bot, ledger_instance))
