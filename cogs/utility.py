import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional

class Utility(commands.Cog):
    def __init__(self, bot, ledger):
        self.bot = bot
        self.ledger = ledger

    @app_commands.command(name="ping", description="システムの応答速度を確認します。")
    async def ping(self, it: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        # 状態によって色を微調整（UX: 視覚的フィードバック）
        status_color = 0x88a096 if latency < 150 else 0xe67e22
        
        embed = discord.Embed(title="System Latency", color=status_color)
        embed.description = f"📡 **Connection is stable.**\n応答速度: `{latency}ms`"
        await it.response.send_message(embed=embed)

    @app_commands.command(name="status", description="自身のステータスを照会します。")
    async def status(self, it: discord.Interaction):
        u = self.ledger.get_user(it.user.id)
        embed = discord.Embed(color=0xf8fafc) # 極めて薄いグレー（クリーンな背景）
        embed.set_author(name=f"{it.user.display_name} - Profile", icon_url=it.user.display_avatar.url)
        
        # 資産状況を一つの大きなフィールドに集約（UX: 読みやすさ重視）
        embed.add_field(
            name="📊 Financial Status", 
            value=f"```💰 資産: {u['money']:,} 資金\n✨ 貢献: {u['xp']:,} XP```", 
            inline=False
        )
        
        # 補足情報を横並び（UX: 画面スペースの節約）
        embed.add_field(name="📅 Join Date", value=f"`{u.get('joined_at', 'N/A')}`", inline=True)
        embed.add_field(name="🕒 Active", value=f"`{u.get('last_active', 'N/A')}`", inline=True)
        
        await it.response.send_message(embed=embed)

    @app_commands.command(name="help", description="操作ガイドを表示します。")
    async def help_command(self, it: discord.Interaction):
        embed = discord.Embed(
            title="System Interface Guide",
            description="各モジュールの機能一覧です。詳細はスラッシュコマンドを入力して確認してください。",
            color=0x475569
        )
        
        # カテゴリごとに整理（UX: 構造化された情報）
        categories = {
            "🔍 Information": "`/status` `/user` `/ping`",
            "💳 Finance": "`/pay` `/exchange` `/ranking` `/money_ranking`",
            "💬 Interaction": "`/janken` `/omikuji` `/meigen` `/roulette` `/comment`",
            "⚙️ Management": "`/admin_grant` `/admin_confiscate` `/restart`"
        }
        
        for name, cmds in categories.items():
            embed.add_field(name=name, value=cmds, inline=True)
            
        embed.set_footer(text="Settings > Command Help")
        await it.response.send_message(embed=embed, ephemeral=True)

async def setup(bot): pass
