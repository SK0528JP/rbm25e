import discord
from discord.ext import commands
from discord import app_commands

class Economy(commands.Cog):
    def __init__(self, bot, ledger):
        self.bot = bot
        self.ledger = ledger

    # --- 送金コマンド ---
    @app_commands.command(name="pay", description="他のユーザーに資産(cr)を送金します")
    @app_commands.describe(target="送金相手", amount="送る金額")
    async def pay(self, it: discord.Interaction, target: discord.Member, amount: int):
        """
        ユーザー間送金ユニット。
        """
        if target.bot:
            await it.response.send_message("❌ ボットに送金することはできません。", ephemeral=True)
            return

        if target.id == it.user.id:
            await it.response.send_message("❌ 自分自身に送金することはできません。", ephemeral=True)
            return

        if amount <= 0:
            await it.response.send_message("❌ 1cr以上の金額を指定してください。", ephemeral=True)
            return

        # 送り主のデータ取得
        u_sender = self.ledger.get_user(it.user.id)
        current_balance = u_sender.get("money", 0)
        
        # 残高チェック
        if current_balance < amount:
            await it.response.send_message(f"❌ 残高が不足しています。（現在の所持金: {current_balance} cr）", ephemeral=True)
            return

        # 送金処理
        u_target = self.ledger.get_user(target.id)
        
        u_sender["money"] = current_balance - amount
        u_target["money"] = u_target.get("money", 0) + amount
        
        # Gistへの保存
        self.ledger.save()

        embed = discord.Embed(
            title="✅ 送金完了", 
            description=f"取引が正常に承認されました。",
            color=0x88a096
        )
        embed.add_field(name="送り主", value=it.user.display_name, inline=True)
        embed.add_field(name="受取人", value=target.display_name, inline=True)
        embed.add_field(name="送金額", value=f"**{amount:,}** cr", inline=False)
        embed.set_footer(text="Rb m/25 Financial Services")
        
        await it.response.send_message(embed=embed)

    # --- 所持金確認コマンド (任意で追加) ---
    @app_commands.command(name="balance", description="自分の現在の所持金を確認します")
    async def balance(self, it: discord.Interaction):
        user_data = self.ledger.get_user(it.user.id)
        money = user_data.get("money", 0)
        xp = user_data.get("xp", 0)
        
        embed = discord.Embed(title=f"💰 {it.user.display_name} の資産情報", color=0x94a3b8)
        embed.add_field(name="所持金", value=f"**{money:,}** cr", inline=True)
        embed.add_field(name="累積貢献度", value=f"**{xp:,}** xp", inline=True)
        
        await it.response.send_message(embed=embed)

async def setup(bot):
    # main.py で定義されている ledger_instance をインポート
    from __main__ import ledger_instance
    await bot.add_cog(Economy(bot, ledger_instance))
