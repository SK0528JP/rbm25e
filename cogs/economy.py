import discord
from discord.ext import commands
from discord import app_commands

class Economy(commands.Cog):
    def __init__(self, bot, ledger):
        self.bot = bot
        self.ledger = ledger

    # --- /pay ---
    @app_commands.command(name="pay", description="同志への送金（国庫を通じた富の再分配）")
    async def pay(self, it: discord.Interaction, recipient: discord.Member, amount: int):
        if amount <= 0:
            await it.response.send_message("❌ 報告：0以下の金額は送金できない。やり直せ！", ephemeral=True)
            return

        sender_data = self.ledger.get_user(it.user.id)
        if sender_data["money"] < amount:
            await it.response.send_message(f"❌ 報告：資金が不足している（現在：{sender_data['money']} 資金）", ephemeral=True)
            return

        recipient_data = self.ledger.get_user(recipient.id)
        sender_data["money"] -= amount
        recipient_data["money"] += amount
        self.ledger.save()

        embed = discord.Embed(title="💰 資金送金報告", color=0x2ecc71)
        embed.description = f"**{it.user.display_name}** 同志から **{recipient.display_name}** 同志へ、資金の移転が行われた。"
        embed.add_field(name="送金額", value=f"**{amount}** 資金", inline=True)
        embed.set_footer(text="国家中央銀行 🏦")
        await it.response.send_message(embed=embed)

    # --- /exchange ---
    @app_commands.command(name="exchange", description="貢献度(XP)を資金に変換する")
    async def exchange(self, it: discord.Interaction, amount: int):
        u = self.ledger.get_user(it.user.id)
        if amount <= 0 or u["xp"] < amount:
            await it.response.send_message("❌ 報告：XPが不足しているか、不正な数値だ。", ephemeral=True)
            return

        u["xp"] -= amount
        u["money"] += amount
        self.ledger.save()

        embed = discord.Embed(title="🔄 貢献度換金証明", color=0x3498db)
        embed.description = f"同志の積み上げた **{amount} XP** を **{amount} 資金** に変換した。"
        embed.set_footer(text="国家労働局 🛠️")
        await it.response.send_message(embed=embed)

    # --- /ranking ---
    @app_commands.command(name="ranking", description="労働英雄ランキング（XP保有量上位10名）")
    async def ranking(self, it: discord.Interaction):
        # データの取得とソート
        all_users = self.ledger.data
        sorted_users = sorted(all_users.items(), key=lambda x: x[1].get("xp", 0), reverse=True)[:10]

        embed = discord.Embed(title="🏆 労働英雄ランキング (XP)", color=0xffd700)
        
        ranking_text = ""
        for i, (uid, stats) in enumerate(sorted_users, 1):
            # メダルの付与
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"` {i} `"
            # メンション形式でユーザーを表示
            ranking_text += f"{medal} | <@{uid}> ― **{stats['xp']}** XP\n"

        embed.description = ranking_text if ranking_text else "記録なし"
        embed.set_footer(text="国家統計局 📊")
        await it.response.send_message(embed=embed)

    # --- /money_ranking ---
    @app_commands.command(name="money_ranking", description="国家長者番付（資金保有量上位10名）")
    async def money_ranking(self, it: discord.Interaction):
        all_users = self.ledger.data
        sorted_users = sorted(all_users.items(), key=lambda x: x[1].get("money", 0), reverse=True)[:10]

        embed = discord.Embed(title="💰 国家長者番付", color=0x2ecc71)
        
        ranking_text = ""
        for i, (uid, stats) in enumerate(sorted_users, 1):
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"` {i} `"
            ranking_text += f"{medal} | <@{uid}> ― **{stats['money']}** 資金\n"

        embed.description = ranking_text if ranking_text else "記録なし"
        embed.set_footer(text="中央銀行 資産調査部 🏦")
        await it.response.send_message(embed=embed)

async def setup(bot):
    pass
