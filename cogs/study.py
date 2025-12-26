import discord
from discord import app_commands
from discord.ext import commands
import time
from datetime import datetime

class Study(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="study_start", description="学習任務を開始します（再起動対応版）")
    async def study_start(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        if not self.bot.ledger:
            await interaction.followup.send("❌ Ledgerが有効ではありません。")
            return

        user_data = self.bot.ledger.get_user(interaction.user.id)
        
        # 既に開始時間が記録されているかチェック
        if user_data.get("study_start_time"):
            await interaction.followup.send("⚠️ 既に学習任務に就いています。一旦終了してください。")
            return

        # 現在時刻をUNIXタイムスタンプで保存
        user_data["study_start_time"] = time.time()
        self.bot.ledger.save()
        
        embed = discord.Embed(
            title="🚀 学習任務開始",
            description=f"同志 {interaction.user.display_name}、戦線へようこそ。\nデータは保存されました。Botが再起動しても継続可能です。",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="study_end", description="学習任務を終了し、成果を記録します。")
    async def study_end(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        if not self.bot.ledger:
            await interaction.followup.send("❌ Ledgerが有効ではありません。")
            return

        user_data = self.bot.ledger.get_user(interaction.user.id)
        start_time = user_data.get("study_start_time")
        
        if not start_time:
            await interaction.followup.send("❌ 学習任務が開始されていません。")
            return

        # 経過時間を計算
        elapsed_seconds = int(time.time() - start_time)
        minutes = elapsed_seconds // 60
        
        # 累積時間に加算し、開始時間をリセット
        if "total_study_time" not in user_data:
            user_data["total_study_time"] = 0
        
        user_data["total_study_time"] += minutes
        user_data["study_start_time"] = None # 開始状態をクリア
        
        self.bot.ledger.save()

        embed = discord.Embed(
            title="🏁 学習任務完了",
            description=f"同志 {interaction.user.display_name}、お疲れ様だ。",
            color=discord.Color.green(),
            timestamp=datetime.now()
        )
        embed.add_field(name="今回の戦果", value=f"**{minutes} 分**", inline=True)
        embed.add_field(name="累積学習時間", value=f"**{user_data['total_study_time']} 分**", inline=True)
        
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Study(bot))
