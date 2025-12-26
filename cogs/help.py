import discord
from discord import app_commands
from discord.ext import commands

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Rb m/25 のコマンドリストを表示します")
    async def help(self, it: discord.Interaction):
        embed = discord.Embed(
            title="📖 Rb m/25 命令体系マニュアル",
            description="現在利用可能なコマンド一覧と機能概要です。",
            color=0x3498db
        )

        # --- ユーザー & ステータス ---
        # status.py / user.py
        embed.add_field(
            name="👤 ユーザー・ステータス (User & Status)",
            value=(
                "`/status` - 自分のステータス（所持金・XP・レベル・称号）を確認\n"
                "`/user` - ユーザープロフィールの詳細設定・確認"
            ),
            inline=False
        )

        # --- 経済 & ランキング ---
        # economy.py / ranking.py / exchange.py
        embed.add_field(
            name="💰 経済・ランキング (Economy)",
            value=(
                "`/pay [user] [amount]` - 他のユーザーに cr (通貨) を送金\n"
                "`/ranking [category]` - 資産・XP・釣り・学習のランキングを表示\n"
                "`/exchange` - ポイント交換・アイテム交換所へのアクセス"
            ),
            inline=False
        )

        # --- フィッシング (釣り) ---
        # fishing.py
        embed.add_field(
            name="🎣 フィッシング (Fishing)",
            value=(
                "`/fishing` - 釣りを開始する\n"
                "`/fishing_inventory` - 獲得した獲物（インベントリ）を確認\n"
                "`/fishing_sale [index/all]` - 獲物を売却して cr を獲得"
            ),
            inline=False
        )

        # --- 学習 (Study) ---
        # study.py
        embed.add_field(
            name="📚 学習機能 (Study)",
            value=(
                "`/study_start` - 学習タイマーを開始\n"
                "`/study_end` - 学習を終了し、時間に応じた報酬を獲得\n"
                "`/study_stats` - 自分の学習記録統計を確認"
            ),
            inline=False
        )

        # --- エンターテインメント ---
        # gallery.py / roulette.py
        embed.add_field(
            name="🎲 エンタメ・ギャラリー (Entertainment)",
            value=(
                "`/roulette [amount]` - 所持金を賭けたルーレット勝負\n"
                "`/gallery_save [name] [image]` - サーバーの思い出(画像)を保存\n"
                "`/gallery_load [name]` - 保存された画像を表示"
            ),
            inline=False
        )

        # --- システム管理 ---
        # ping.py / admin.py
        embed.add_field(
            name="⚙️ システム (System)",
            value=(
                "`/ping` - Botの応答速度(Latency)を確認\n"
                "`/admin` - 管理者専用メニュー（権限所有者のみ）"
            ),
            inline=False
        )

        embed.set_footer(text="Rb m/25 System | Validated Commands Only")
        
        await it.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Help(bot))
