import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime
import time

class Countdown(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="countdown", description="目標時刻までを精密に計測します")
    @app_commands.describe(
        title="名称",
        date="日付 (YYYY/MM/DD)",
        time="時刻 (HH:MM) ※省略時は 00:00"
    )
    async def countdown(self, interaction: discord.Interaction, title: str, date: str, time_str: str = "00:00"):
        try:
            # 日付と時刻を統合してパース
            target_dt = datetime.strptime(f"{date} {time_str}", '%Y/%m/%d %H:%M')
            target_ts = int(target_dt.timestamp())
            now_ts = int(time.time())
            
            diff = target_ts - now_ts

            if diff <= 0:
                return await interaction.response.send_message(
                    f"⌛ **{title}** : 目標時刻に到達しました。", ephemeral=True
                )

            # --- 機能的ビジュアル要素 ---
            # 1. プログレスバー（簡易版）
            # ここでは開始日を「コマンド実行時」として100%から減っていく形式
            bar_length = 10
            progress_bar = "■" * bar_length # シンプルなバー

            # 2. Discord動的タイムスタンプ
            # <t:timestamp:R> は「3日後」「2時間前」のように自動更新される
            dynamic_rel = f"<t:{target_ts}:R>" 
            dynamic_full = f"<t:{target_ts}:F>"

            nordic_slate = 0x4C566A
            embed = discord.Embed(title=title, color=nordic_slate)
            
            # 敢えて「残り〇〇」と書かず、タイムスタンプに語らせる機能美
            embed.add_field(
                name="Status", 
                value=f"{progress_bar}\n目標まで **{dynamic_rel}**", 
                inline=False
            )
            
            embed.add_field(
                name="Deadline",
                value=dynamic_full,
                inline=False
            )

            embed.set_footer(text="Rb m/25E | Precision & Minimal")

            await interaction.response.send_message(embed=embed)

        except ValueError:
            await interaction.response.send_message(
                "❌ 形式エラー: `2025/12/31` `23:59` のように入力してください。", 
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(Countdown(bot))
