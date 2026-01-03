import discord
from discord.ext import commands
from discord import app_commands
import sys
from datetime import datetime

class Admin(commands.Cog):
    def __init__(self, bot, ledger):
        self.bot = bot
        self.ledger = ledger
        # 管理権限を持つユーザーID
        self.ADMIN_USER_IDS = [840821281838202880]

    async def is_admin(self, it: discord.Interaction):
        """権限があるか確認し、ない場合は通知します。"""
        if it.user.id in self.ADMIN_USER_IDS:
            return True
            
        embed = discord.Embed(
            title="アクセス拒否",
            description="このコマンドを実行する権限がありません。",
            color=0xe74c3c 
        )
        await it.response.send_message(embed=embed, ephemeral=True)
        return False

    # --- サーバーリスト確認 (展開状況把握) ---
    @app_commands.command(name="admin_servers", description="[管理者専用] Botの展開サーバー状況を確認します")
    async def admin_servers(self, it: discord.Interaction):
        if not await self.is_admin(it): return
        await it.response.defer(ephemeral=True)

        guilds = self.bot.guilds
        if not guilds:
            return await it.followup.send("📡 稼働中のサーバーは確認できません。", ephemeral=True)

        embed = discord.Embed(
            title="🛰️ Rb m/25E 展開状況レポート",
            color=0x34495e,
            timestamp=datetime.now()
        )

        total_members = 0
        server_info = []

        for guild in guilds:
            total_members += guild.member_count
            # サーバーオーナーの取得試行
            owner = guild.owner or await self.bot.fetch_user(guild.owner_id)
            server_info.append(
                f"🔹 **{guild.name}**\n"
                f"   ID: `{guild.id}` | 員数: `{guild.member_count}`名\n"
                f"   指揮官: `{owner.name}`"
            )

        # 内容が長すぎる場合は分割
        description = "\n\n".join(server_info)
        if len(description) > 4000:
            description = description[:3900] + "\n\n...[以下省略]"

        embed.description = description
        embed.add_field(name="📊 統計データ", value=f"展開サーバー数: `{len(guilds)}` / 観測下ユーザー総数: `{total_members}`名")
        embed.set_footer(text="Rb m/25 行政プロトコル")

        await it.followup.send(embed=embed, ephemeral=True)

    # --- 資産付与 ---
    @app_commands.command(name="admin_grant", description="指定したユーザーに資産を付与します")
    @app_commands.describe(target="付与対象のユーザー", amount="付与する金額")
    async def admin_grant(self, it: discord.Interaction, target: discord.User, amount: int):
        if not await self.is_admin(it): return
        
        u_target = self.ledger.get_user(target.id)
        u_target["money"] += amount
        self.ledger.save()
        
        embed = discord.Embed(title="資産付与完了", color=0x94a3b8)
        embed.add_field(name="対象者", value=target.name, inline=True)
        embed.add_field(name="付与額", value=f"```fix\n+ {amount:,} cr\n```", inline=False)
        embed.set_footer(text="Rb m/25 行政プロトコル")
        
        await it.response.send_message(embed=embed)

    # --- 資産回収 ---
    @app_commands.command(name="admin_confiscate", description="指定したユーザーから資産を回収します")
    @app_commands.describe(target="回収対象のユーザー", amount="回収する金額")
    async def admin_confiscate(self, it: discord.Interaction, target: discord.User, amount: int):
        if not await self.is_admin(it): return
        
        u_target = self.ledger.get_user(target.id)
        u_target["money"] = max(0, u_target["money"] - amount)
        self.ledger.save()
        
        embed = discord.Embed(title="資産回収完了", color=0x475569)
        embed.add_field(name="対象者", value=target.name, inline=True)
        embed.add_field(name="回収額", value=f"```diff\n- {amount:,} cr\n```", inline=False)
        embed.set_footer(text="Rb m/25 行政プロトコル")
        
        await it.response.send_message(embed=embed)

    # --- システム再起動 ---
    @app_commands.command(name="restart", description="システムを再起動（終了）します")
    async def restart(self, it: discord.Interaction):
        if not await self.is_admin(it): return
        
        embed = discord.Embed(title="システムメンテナンス", description="シャットダウンを開始します...", color=0x1e293b)
        embed.set_footer(text="Rb m/25 行政プロトコル")
        
        await it.response.send_message(embed=embed)
        print(f"[SYSTEM] 再起動が実行されました: 実行者 {it.user.name}")
        
        sys.exit()

async def setup(bot):
    from __main__ import ledger_instance
    await bot.add_cog(Admin(bot, ledger_instance))
