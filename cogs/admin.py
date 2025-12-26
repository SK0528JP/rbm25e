import discord
from discord.ext import commands
from discord import app_commands
import sys

class Admin(commands.Cog):
    def __init__(self, bot, ledger):
        self.bot = bot
        self.ledger = ledger
        # 管理権限設定（環境に合わせて調整してください）
        self.ADMIN_ROLE_ID = 1453336556961140866
        self.ADMIN_USER_IDS = [840821281838202880]

    async def is_admin(self, it: discord.Interaction):
        """権限照会プロセス（UX: エラーメッセージの明確化）"""
        has_role = any(role.id == self.ADMIN_ROLE_ID for role in it.user.roles)
        is_special_user = it.user.id in self.ADMIN_USER_IDS
        
        if has_role or is_special_user:
            return True
            
        # 権限がない場合のフィードバック
        embed = discord.Embed(
            title="Access Denied",
            description="この操作を実行するための十分な権限が確認できませんでした。\n必要な権限: `System Administrator`",
            color=0xe74c3c # 警告を示すソフトな赤
        )
        await it.response.send_message(embed=embed, ephemeral=True)
        return False

    @app_commands.command(name="admin_grant", description="指定したユーザーのアカウントに資金を直接付与します。")
    @app_commands.describe(target="付与対象のユーザー", amount="付与する金額")
    async def admin_grant(self, it: discord.Interaction, target: discord.Member, amount: int):
        if not await self.is_admin(it): return
        
        u = self.ledger.get_user(target.id)
        u["money"] += amount
        self.ledger.save()
        
        embed = discord.Embed(title="Asset Allocation Authorized", color=0x94a3b8)
        embed.set_author(name="Administrative Action", icon_url=it.user.display_avatar.url)
        
        # UX: 操作内容を「カード形式」で表示
        embed.add_field(name="Target Account", value=f"👤 {target.display_name}", inline=True)
        embed.add_field(name="Action", value="➕ Grant Assets", inline=True)
        embed.add_field(name="Adjustment Amount", value=f"```fix\n+ {amount:,} 資金\n```", inline=False)
        
        embed.set_footer(text=f"Authorized by {it.user.name}")
        await it.response.send_message(embed=embed)

    @app_commands.command(name="admin_confiscate", description="指定したユーザーのアカウントから資金を回収・調整します。")
    @app_commands.describe(target="調整対象のユーザー", amount="回収する金額")
    async def admin_confiscate(self, it: discord.Interaction, target: discord.Member, amount: int):
        if not await self.is_admin(it): return
        
        u = self.ledger.get_user(target.id)
        u["money"] = max(0, u["money"] - amount)
        self.ledger.save()
        
        embed = discord.Embed(title="Asset Adjustment Applied", color=0x475569)
        embed.set_author(name="Administrative Action", icon_url=it.user.display_avatar.url)
        
        embed.add_field(name="Target Account", value=f"👤 {target.display_name}", inline=True)
        embed.add_field(name="Action", value="➖ Asset Reduction", inline=True)
        embed.add_field(name="Adjustment Amount", value=f"```diff\n- {amount:,} 資金\n```", inline=False)
        
        embed.set_footer(text=f"Processed by {it.user.name}")
        await it.response.send_message(embed=embed)

    @app_commands.command(name="restart", description="システム全体の最適化と再起動プロセスを開始します。")
    async def restart(self, it: discord.Interaction):
        if not await self.is_admin(it): return
        
        embed = discord.Embed(
            title="System Maintenance: Reboot", 
            description="インフラストラクチャの整合性を保つため、システムを再起動します。", 
            color=0x1e293b # 深みのあるダークブルー
        )
        
        # UX: プロセス状況の視覚化
        embed.add_field(name="Status", value="🔄 Initializing shutdown...", inline=True)
        embed.add_field(name="Priority", value="Critical", inline=True)
        
        embed.set_footer(text="System Kernel Information")
        
        await it.response.send_message(embed=embed)
        
        # ログへの記録
        print(f"[SYSTEM] --- REBOOT AUTHORIZED BY {it.user.name} ---")
        
        # 終了処理（実際にはホスティング環境が自動再起動することを想定）
        sys.exit()

async def setup(bot):
    # Cogの登録（main.pyから明示的にインポートするため、ここでの処理はpassでOK）
    pass
