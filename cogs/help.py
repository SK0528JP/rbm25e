import discord
from discord import app_commands
from discord.ext import commands

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Rb m/25 のすべてのコマンドを確認します")
    async def help(self, it: discord.Interaction):
        embed = discord.Embed(
            title="📖 Rb m/25 命令体系マニュアル",
            description="各セクションのコマンド詳細は以下の通りです。",
            color=0x3498db
        )

        # --- 経済 & ランキング ---
        embed.add_field(
            name="💰 経済・ランキング (Finance & Ranking)",
            value=(
                "`/balance` - 現在の所持金(cr)とXPを確認\n"
                "`/pay [user] [amount]` - 資産を他の同志に送金\n"
                "`/ranking [category]` - 資産/XP/釣り/学習のランキングを表示"
            ),
            inline=False
        )

        # --- 学習管理 ---
        embed.add_field(
            name="📚 学習管理 (Study Management)",
            value=(
                "`/study_start` - 学習セッションを開始\n"
                "`/study_end` - 学習を終了し、報酬(cr/xp)を獲得\n"
                "`/study_stats` - 自分の累計・今日の学習時間を確認"
            ),
            inline=False
        )

        # --- フィッシング ---
        embed.add_field(
            name="🎣 フィッシング (Fishing)",
            value=(
                "`/fishing` - 釣りを行う（待機時間あり）\n"
                "`/fishing_inventory` - 自分の生け簀（バケツ）を確認\n"
                "`/fishing_sale [index/all]` - 獲物を売却して cr に換金"
            ),
            inline=False
        )

        # --- ギャラリー & エンタメ ---
        embed.add_field(
            name="🖼️ ギャラリー & エンタメ (Entertainment)",
            value=(
                "`/gallery_add [name] [image]` - 画像をストックする\n"
                "`/gallery_view [name]` - 保存した画像を呼び出す\n"
                "`/roulette [amount]` - 所持金を賭けて勝負"
            ),
            inline=False
        )

        # --- システム ---
        embed.add_field(
            name="⚙️ システム (System)",
            value=(
                "`/ping` - 応答速度を確認\n"
                "`/status` - ボットの稼働状況を確認"
            ),
            inline=False
        )

        embed.set_footer(text="Rb m/25 System | 指令の実行には権限が必要です")
        
        await it.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Help(bot))
