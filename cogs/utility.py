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
        システムの使いかたを分かりやすく解説するヘルプコマンドです。
        """
        embed = discord.Embed(
            title="🌿 Rb m/25 システムガイド",
            description=(
                "Rb m/25 は、北欧モダニズムの思想を取り入れた多機能管理システムです。\n"
                "全てのメッセージは日本語で提供されています。\n\n"
                "### 💎 資産と貢献度\n"
                "- **貢献度 (XP)**: チャットで発言するたびに蓄積されます（3秒間隔）。\n"
                "- **資産 (Credits)**: 初期値 100 cr。ゲームや送金で使用します。\n\n"
                "### 📜 利用可能なコマンド\n"
                "- `/status` : 自分の現在の資産とXPを確認します。\n"
                "- `/ranking` : サーバー内の長者・貢献者ランキングを表示します。\n"
                "- `/pay` : 他のユーザーに資産を安全に送金します。\n"
                "- `/janken` : 娯楽ユニット。勝利すると 10 cr 獲得できます。\n"
                "- `/fortune` : 今日のおみくじを引きます。\n"
                "- `/ping` : システムの応答速度を測定します。\n\n"
                "*※ `/lang` コマンドは日本語専用化に伴い廃止されました。*"
            ),
            color=0x475569 # スレートグレー
        )
        embed.set_author(name="Rb m/25 インターフェース", icon_url=self.bot.user.display_avatar.url)
        embed.set_footer(text="Rb m/25 Infrastructure Division")
        
        # 本人にのみ表示
        await it.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="status", description="自分のプロファイルと資産状況を表示します")
    async def status(self, it: discord.Interaction):
        """
        ユーザーの現在のステータスを可視化します。
        """
        u = self.ledger.get_user(it.user.id)
        
        embed = discord.Embed(color=0xf8fafc)
        embed.set_author(name=f"{it.user.display_name} のステータス", icon_url=it.user.display_avatar.url)
        
        status_info = (
            f"💰 **保有資産**: {u['money']:,} cr\n"
            f"✨ **貢献度**: {u['xp']:,} XP\n"
            f"📅 **登録日**: {u.get('joined_at', '不明')}"
        )
        embed.add_field(name="データ照会結果", value=status_info, inline=False)
        
        # 最終アクティブ時間の表示
        last_active = u.get('last_active', '記録なし')
        embed.set_footer(text=f"最終稼働: {last_active} | Rb m/25")
        
        await it.response.send_message(embed=embed)

    @app_commands.command(name="ping", description="システムの応答速度を確認します")
    async def ping(self, it: discord.Interaction):
        """
        レイテンシを確認します。
        """
        latency = round(self.bot.latency * 1000)
        await it.response.send_message(f"📡 **システム応答速度**: `{latency}ms`", ephemeral=True)

async def setup(bot):
    from __main__ import ledger_instance
    await bot.add_cog(Utility(bot, ledger_instance))
