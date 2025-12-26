import discord
from discord.ext import commands
from discord import app_commands
import sys

class Admin(commands.Cog):
    def __init__(self, bot, ledger):
        self.bot = bot
        self.ledger = ledger
        self.ADMIN_ROLE_ID = 1453336556961140866

    async def is_admin(self, it: discord.Interaction):
        if any(role.id == self.ADMIN_ROLE_ID for role in it.user.roles):
            return True
        await it.response.send_message("❌ 拒絶：このコマンドを実行する権限がない。", ephemeral=True)
        return False

    @app_commands.command(name="admin_grant", description="【管理者用】特別予算を付与")
    async def admin_grant(self, it: discord.Interaction, target: discord.Member, amount: int):
        if not await self.is_admin(it): return
        u = self.ledger.get_user(target.id)
        u["money"] += amount
        self.ledger.save()
        embed = discord.Embed(title="📢 国家予算承認", color=0xffd700)
        embed.description = f"同志 {target.mention} へ **{amount} 資金** の特別付与が完了した。"
        await it.response.send_message(embed=embed)

    @app_commands.command(name="admin_confiscate", description="【管理者用】不当資産の没収")
    async def admin_confiscate(self, it: discord.Interaction, target: discord.Member, amount: int):
        if not await self.is_admin(it): return
        u = self.ledger.get_user(target.id)
        u["money"] = max(0, u["money"] - amount)
        self.ledger.save()
        embed = discord.Embed(title="📢 資産没収宣告", color=0xff0000)
        embed.description = f"同志 {target.mention} の資産より **{amount} 資金** を回収した。"
        await it.response.send_message(embed=embed)

    @app_commands.command(name="restart", description="【管理者用】システム再起動")
    async def restart(self, it: discord.Interaction):
        if not await self.is_admin(it): return
        embed = discord.Embed(title="🔄 システム再起動", description="これより戦略的再起動を行う。しばし待て。", color=0x333333)
        await it.response.send_message(embed=embed)
        sys.exit()

async def setup(bot):
    pass
