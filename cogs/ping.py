import discord
from discord.ext import commands
from discord import app_commands
import time
import datetime

class Ping(commands.Cog):
    def __init__(self, bot, ledger):
        self.bot = bot
        self.ledger = ledger

    @app_commands.command(name="ping", description="システムの応答速度と接続状態を詳細に診断します")
    async def ping(self, it: discord.Interaction):
        """
        APIレイテンシ、WebSocketの応答速度、および稼働状態を診断。
        """
        # 送信タイミングの計測開始
        start_time = time.monotonic()
        
        # 最初の応答
        await it.response.send_message("📡 システム診断中...", ephemeral=True)
        
        # 応答にかかった時間を算出 (End-to-End レイテンシ)
        end_time = time.monotonic()
        api_latency = round((end_time - start_time) * 1000)
        
        # WebSocketのレイテンシ (Discordゲートウェイとの接続速度)
        ws_latency = round(self.bot.latency * 1000)
        
        # 速度に応じたステータス判定
        if ws_latency < 50:
            status = "🟢 最適 (Excellent)"
            color = 0x10b981 # Emerald
        elif ws_latency < 150:
            status = "🟡 良好 (Good)"
            color = 0xf59e0b # Amber
        else:
            status = "🔴 遅延気味 (Warning)"
            color = 0xef4444 # Rose

        embed = discord.Embed(
            title="🛰️ システム診断レポート",
            description="Rb m/25 Infrastructure 接続状況",
            color=color,
            timestamp=datetime.datetime.now()
        )

        embed.add_field(
            name="📡 API Response", 
            value=f"`{api_latency}ms`", 
            inline=True
        )
        embed.add_field(
            name="🌐 WebSocket", 
            value=f"`{ws_latency}ms`", 
            inline=True
        )
        embed.add_field(
            name="📊 Status", 
            value=f"**{status}**", 
            inline=True
        )

        # サーバー情報の付加
        embed.add_field(
            name="🧬 Node Info",
            value=f"Shard ID: `{self.bot.shard_id or 0}`\nConnected: `True`",
            inline=False
        )

        embed.set_footer(text="Rb m/25 Network Operations Center")

        # 最初のメッセージを更新
        await it.edit_original_response(content=None, embed=embed)

async def setup(bot):
    from __main__ import ledger_instance
    await bot.add_cog(Ping(bot, ledger_instance))
