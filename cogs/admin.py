import discord
from discord.ext import commands
from discord import app_commands
import sys

class Admin(commands.Cog):
    def __init__(self, bot, ledger):
        self.bot = bot
        self.ledger = ledger
        # 管理権限設定
        self.ADMIN_ROLE_ID = 1453336556961140866
        self.ADMIN_USER_IDS = [840821281838202880]

    async def is_admin(self, it: discord.Interaction):
        # 権限照会
        has_role = any(role.id == self.ADMIN_ROLE_ID for role in it.user.roles)
        is_special_user = it.user.id in self.ADMIN_USER_IDS
        
        if has_role or is_special_user:
            return True
            
        await it.response.send_message("アクセス権限が不足しています。", ephemeral=True)
        return False

    @app_commands.command(name="admin_grant", description="指定したユーザーへ資金を付与します。")
    async def admin_grant(self, it: discord.Interaction, target: discord.Member, amount: int):
        if not await self.is_admin(it): return
        
        u = self.ledger.get_user(target.id)
        u["money"] += amount
        self.ledger.save()
        
        embed = discord.Embed(title="Grant Authorized", color=0x94a3b8) # スレートブルー
        embed.description = f"**{target.display_name}** 様へ **{amount:,} 資金** を付与しました。"
        embed.set_footer(text="Administrative Action")
        await it.response.send_message(embed=embed)

    @app_commands.command(name="admin_confiscate", description="指定したユーザーから資金を回収します。")
    async def admin_confiscate(self, it: discord.Interaction, target: discord.Member, amount: int):
        if not await self.is_admin(it): return
        
        u = self.ledger.get_user(target.id)
        u["money"] = max(0, u["money"] - amount)
        self.ledger.save()
        
        embed = discord.Embed(title="Adjustment Applied", color=0x94a3b8)
        embed.description = f"**{target.display_name}** 様の口座より **{amount:,} 資金** を回収しました。"
        embed.set_footer(text="Administrative Action")
        await it.response.send_message(embed=embed)

    @app_commands.command(name="restart", description="システムの再起動を実行します。")
    async def restart(self, it: discord.Interaction):
        if not await self.is_admin(it): return
        
        embed = discord.Embed(
            title="System Reboot", 
            description="システムの最適化のため、再起動プロセスを開始します。\n完了までしばらくお待ちください。", 
            color=0x475569 # スレートグレー
        )
        embed.add_field(name="Authorized by", value=it.user.display_name, inline=True)
        embed.add_field(name="Status", value="Processing...", inline=True)
        embed.set_footer(text="Infrastructure Maintenance")
        
        await it.response.send_message(embed=embed)
        
        print(f"[SYSTEM] Reboot authorized by {it.user.name}.")
        sys.exit()

async def setup(bot):
    pass
