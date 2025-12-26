import discord
from discord.ext import commands
from discord import app_commands

class Economy(commands.Cog):
    def __init__(self, bot, ledger):
        self.bot = bot
        self.ledger = ledger

    @app_commands.command(name="pay", description="指定したユーザーへ資金を送金します。")
    async def pay(self, it: discord.Interaction, recipient: discord.Member, amount: int):
        if amount <= 0:
            await it.response.send_message("1以上の数値を入力してください。", ephemeral=True)
            return

        sender_data = self.ledger.get_user(it.user.id)
        if sender_data["money"] < amount:
            await it.response.send_message(f"残高が不足しています。（現在：{sender_data['money']:,}）", ephemeral=True)
            return

        recipient_data = self.ledger.get_user(recipient.id)
        sender_data["money"] -= amount
        recipient_data["money"] += amount
        self.ledger.save()

        embed = discord.Embed(title="Transaction Completed", color=0x88a096) # セージグリーン
        embed.description = "送金処理が正常に完了いたしました。"
        embed.add_field(name="Sender", value=it.user.display_name, inline=True)
        embed.add_field(name="Recipient", value=recipient.display_name, inline=True)
        embed.add_field(name="Amount", value=f"{amount:,} 資金", inline=False)
        embed.set_footer(text="Nordic Financial Ledger")
        await it.response.send_message(embed=embed)

    @app_commands.command(name="exchange", description="蓄積されたXPを資金に換算します。")
    async def exchange(self, it: discord.Interaction, amount: int):
        u = self.ledger.get_user(it.user.id)
        if amount <= 0 or u["xp"] < amount:
            await it.response.send_message("XPが不足しているか、数値が正しくありません。", ephemeral=True)
            return

        u["xp"] -= amount
        u["money"] += amount
        self.ledger.save()

        embed = discord.Embed(title="Asset Conversion", color=0x94a3b8) # スレートブルー
        embed.description = "資産の振り替えが完了いたしました。"
        embed.add_field(name="Converted XP", value=f"{amount:,} XP", inline=True)
        embed.add_field(name="Total Credit", value=f"{amount:,} 資金", inline=True)
        embed.set_footer(text="Asset Management Unit")
        await it.response.send_message(embed=embed)

    @app_commands.command(name="ranking", description="貢献度（XP）の上位10名を表示します。")
    async def ranking(self, it: discord.Interaction):
        all_users = self.ledger.data
        sorted_users = sorted(all_users.items(), key=lambda x: x[1].get("xp", 0), reverse=True)[:10]

        embed = discord.Embed(
            title="Contribution Ranking",
            description="現在のコミュニティにおける貢献度上位者です。",
            color=0x475569 # スレートグレー
        )
        
        if not sorted_users:
            embed.description = "データが見つかりませんでした。"
        else:
            for i, (uid, stats) in enumerate(sorted_users, 1):
                # IDから名前を取得（キャッシュを利用）
                member = it.guild.get_member(int(uid))
                user_name = member.display_name if member else f"User_{uid[:4]}"
                
                # 北欧風にシンプルなラベルと強調
                embed.add_field(
                    name=f"No. {i:02d}",
                    value=f"**{user_name}**\n{stats['xp']:,} XP",
                    inline=True
                )

        embed.set_footer(text="Performance Analytics")
        await it.response.send_message(embed=embed)

    @app_commands.command(name="money_ranking", description="資産保有量の上位10名を表示します。")
    async def money_ranking(self, it: discord.Interaction):
        all_users = self.ledger.data
        sorted_users = sorted(all_users.items(), key=lambda x: x[1].get("money", 0), reverse=True)[:10]

        embed = discord.Embed(
            title="Wealth Ranking",
            description="現在のコミュニティにおける資産保有量上位者です。",
            color=0x5c7a67 # モスグリーン
        )
        
        if not sorted_users:
            embed.description = "データが見つかりませんでした。"
        else:
            for i, (uid, stats) in enumerate(sorted_users, 1):
                member = it.guild.get_member(int(uid))
                user_name = member.display_name if member else f"User_{uid[:4]}"
                
                embed.add_field(
                    name=f"No. {i:02d}",
                    value=f"**{user_name}**\n{stats['money']:,} 資金",
                    inline=True
                )

        embed.set_footer(text="Wealth Statistics")
        await it.response.send_message(embed=embed)

async def setup(bot):
    pass
