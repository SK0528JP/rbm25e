import discord
from discord import app_commands
from discord.ext import commands
import time
from datetime import datetime, timedelta

class Study(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="study_start", description="学習任務を開始します。")
    async def study_start(self, interaction: discord.Interaction):
        await interaction.response.defer()
        if not self.bot.ledger:
            await interaction.followup.send("❌ Ledgerが有効ではありません。")
            return

        user_data = self.bot.ledger.get_user(interaction.user.id)
        if user_data.get("study_start_time"):
            await interaction.followup.send("⚠️ 既に学習任務に就いています。")
            return

        # 開始時刻を保存
        user_data["study_start_time"] = time.time()
        self.bot.ledger.save()
        
        embed = discord.Embed(
            title="🚀 学習任務開始",
            description=f"同志 {interaction.user.display_name}、戦線へようこそ。\n集中力を維持し、目標を完遂せよ。",
            color=discord.Color.blue(),
            timestamp=datetime.now(self.bot.JST)
        )
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="study_end", description="学習任務を終了し、詳細な履歴を記録します。")
    async def study_end(self, interaction: discord.Interaction):
        await interaction.response.defer()
        user_data = self.bot.ledger.get_user(interaction.user.id)
        start_time = user_data.get("study_start_time")
        
        if not start_time:
            await interaction.followup.send("❌ 学習任務が開始されていません。")
            return

        # 経過時間の計算
        elapsed_seconds = int(time.time() - start_time)
        minutes = elapsed_seconds // 60
        
        # --- 履歴記録システム ---
        now_jst = datetime.now(self.bot.JST)
        today_str = now_jst.strftime("%Y-%m-%d")
        
        if "study_history" not in user_data:
            user_data["study_history"] = {}
        
        # 日ごとの記録に加算
        user_data["study_history"][today_str] = user_data["study_history"].get(today_str, 0) + minutes
        
        # 全累計時間の更新
        user_data["total_study_time"] = user_data.get("total_study_time", 0) + minutes
        # 開始状態をリセット
        user_data["study_start_time"] = None
        
        self.bot.ledger.save()

        embed = discord.Embed(
            title="🏁 学習任務完了",
            description=f"同志 {interaction.user.display_name}、帰還を歓迎する。",
            color=discord.Color.green(),
            timestamp=now_jst
        )
        embed.add_field(name="今回の戦果", value=f"**{minutes} 分**", inline=True)
        embed.add_field(name="本日の合計", value=f"**{user_data['study_history'][today_str]} 分**", inline=True)
        embed.add_field(name="全累計時間", value=f"**{user_data['total_study_time']} 分**", inline=True)
        
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="study_stats", description="学習統計を表示します（期間指定可能）")
    @app_commands.choices(period=[
        app_commands.Choice(name="今日", value="today"),
        app_commands.Choice(name="今週（直近7日）", value="week"),
        app_commands.Choice(name="今月（直近30日）", value="month"),
        app_commands.Choice(name="今年", value="year"),
        app_commands.Choice(name="全期間", value="all")
    ])
    async def study_stats(self, interaction: discord.Interaction, period: str = "today"):
        """ユーザーが期間を選んで統計を見れるようにアップグレード"""
        user_data = self.bot.ledger.get_user(interaction.user.id)
        history = user_data.get("study_history", {})
        now_jst = datetime.now(self.bot.JST)
        
        total = 0
        period_text = ""

        if period == "today":
            target = now_jst.strftime("%Y-%m-%d")
            total = history.get(target, 0)
            period_text = "今日"
        elif period == "all":
            total = user_data.get("total_study_time", 0)
            period_text = "全期間"
        else:
            # 指定された日数分遡って合計を計算
            days = 7 if period == "week" else 30 if period == "month" else 365
            for i in range(days):
                date_str = (now_jst - timedelta(days=i)).strftime("%Y-%m-%d")
                total += history.get(date_str, 0)
            period_text = f"直近 {days} 日間"

        embed = discord.Embed(
            title=f"📊 学習統計: {period_text}",
            description=f"同志 {interaction.user.display_name} の戦果報告だ。",
            color=discord.Color.purple(),
            timestamp=now_jst
        )
        embed.add_field(name="合計学習時間", value=f"**{total} 分**", inline=False)
        
        status = "🔴 学習任務中" if user_data.get("study_start_time") else "⚪ 待機中"
        embed.add_field(name="現在の状態", value=status, inline=False)

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Study(bot))
