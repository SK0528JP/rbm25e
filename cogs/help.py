import discord
from discord import app_commands
from discord.ext import commands

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Rb m/25 のすべての機能を確認します")
    async def help(self, it: discord.Interaction):
        embed = discord.Embed(
            title="📖 Rb m/25 命令体系マニュアル",
            description="サーバーで利用可能な全コマンドのリストです。",
            color=0x3498db
        )

        # --- プロフィール・個人ステータス ---
        embed.add_field(
            name="👤 ユーザー情報 (User Status)",
            value=(
                "`/status` - 自分のレベル、XP、所持金、称号を簡易表示\n"
                "`/balance` - 資産(cr)と累計XPの詳細確認"
            ),
            inline=False
        )

        # --- 経済 & ランキング ---
        embed.add_field(
            name="💰 経済・ランキング (Finance & Ranking)",
            value=(
                "`/pay [user] [amount]` - 資産を他の同志に送金\n"
                "`/ranking [category]` - 資産/XP/釣り/学習のランキングを表示\n"
                "`/exchange` - 通貨の交換や特殊アイテムの確認"
            ),
            inline=False
        )

        # --- 学習管理 ---
        embed.add_field(
            name="📚 学習管理 (Study)",
            value=(
                "`/study_start` - 学習セッションを開始\n"
                "`/study_end` - 学習を終了し、報酬(cr/xp)を獲得\n"
                "`/study_stats` - 今日の学習時間と累計記録を確認"
            ),
            inline=False
        )

        # --- フィッシング ---
        embed.add_field(
            name="🎣 フィッシング (Fishing)",
            value=(
                "`/fishing` - 釣りを行う\n"
                "`/fishing_inventory` - 自分の生け簀を確認\n"
                "`/fishing_sale [index/all]` - 獲物を売却して cr に換金"
            ),
            inline=False
        )

        # --- ギャラリー & エンタメ ---
        embed.add_field(
            name="🖼️ エンターテインメント (Entertainment)",
            value=(
                "`/gallery_add [name] [image]` - 画像をストック\n"
                "`/gallery_view [name]` - 保存した画像を呼び出し\n"
                "`/roulette [amount]` - 所持金を賭けたルーレット\n"
                "`/user` - ユーザー設定や詳細プロフィールの表示"
            ),
            inline=False
        )

        # --- システム ---
        embed.add_field(
            name="⚙️ システム (System)",
            value=(
                "`/ping` - 応答速度の測定\n"
                "`/admin` - 管理者用コマンド(制限あり)"
            ),
            inline=False
        )

        embed.set_footer(text="Rb m/25 System | 各種データの同期は完了しています")
        
        await it.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Help(bot))
