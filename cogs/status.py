import discord
from discord.ext import commands
from discord import app_commands

class Status(commands.Cog):
    def __init__(self, bot, ledger):
        self.bot = bot
        self.ledger = ledger

    @app_commands.command(name="status", description="自分の現在の簡易ステータスを表示します")
    async def status(self, it: discord.Interaction):
        """
        自身の資産とXPを迅速に照会するための専用ユニット。
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
    from __main__ import ledger_instance
    await bot.add_cog(Status(bot, ledger_instance))
