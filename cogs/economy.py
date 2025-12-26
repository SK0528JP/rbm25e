import discord
from discord.ext import commands
from discord import app_commands
from strings import STRINGS

class Economy(commands.Cog):
    def __init__(self, bot, ledger):
        self.bot = bot
        self.ledger = ledger

    @app_commands.command(name="ranking", description="View rankings / ランキング表示 / Visa rankning")
    @app_commands.choices(type=[
        app_commands.Choice(name="Contribution (XP)", value="xp"),
        app_commands.Choice(name="Wealth (Money)", value="money"),
    ])
    async def ranking(self, it: discord.Interaction, type: str = "xp"):
        u = self.ledger.get_user(it.user.id)
        lang = u.get("lang", "ja")
        s = STRINGS.get(lang, STRINGS["ja"])

        # 1. データが空、または指定したキーが存在しない場合のチェック
        all_users = self.ledger.data
        if not all_users:
            await it.response.send_message("📭 No data recorded yet.", ephemeral=True)
            return

        # 2. ソート処理（エラー耐性を強化）
        try:
            sorted_users = sorted(
                all_users.items(), 
                key=lambda x: x[1].get(type, 0), 
                reverse=True
            )[:10]
        except Exception as e:
            print(f"[CRITICAL ERROR] Sorting failed: {e}")
            await it.response.send_message("❌ System Error: Sorting failed.", ephemeral=True)
            return

        title = s.get("rank_xp_title", "Ranking") if type == "xp" else s.get("rank_money_title", "Wealth Ranking")
        embed = discord.Embed(title=title, description=s.get("rank_desc", "Top contributors"), color=0x94a3b8)
        
        rank_list = ""
        for i, (uid, stats) in enumerate(sorted_users, 1):
            # メンバー情報の取得
            member = it.guild.get_member(int(uid))
            name = member.display_name if member else f"User_{uid[:4]}"
            
            val = stats.get(type, 0)
            unit = "XP" if type == "xp" else "cr"
            
            # 言語別順位表記
            suffix = {"ja": "位", "en": "th", "sv": ":a"}.get(lang, "")
            if lang == "en":
                if i == 1: suffix = "st"
                elif i == 2: suffix = "nd"
                elif i == 3: suffix = "rd"

            rank_list += f"`{i}{suffix}` **{name}** : {val:,} {unit}\n"
        
        embed.add_field(name="Leaderboard", value=rank_list or "---", inline=False)
        embed.set_footer(text=s.get("footer_finance", "Rb m/25 Finance"))
        
        await it.response.send_message(embed=embed)

    @app_commands.command(name="pay", description="Transfer credits / 送金 / Överför")
    @app_commands.describe(target="Recipient", amount="Amount to send")
    async def pay(self, it: discord.Interaction, target: discord.Member, amount: int):
        u_sender = self.ledger.get_user(it.user.id)
        lang = u_sender.get("lang", "ja")
        s = STRINGS.get(lang, STRINGS["ja"])

        if target.bot:
            await it.response.send_message("❌ Cannot transfer to bots.", ephemeral=True)
            return

        if amount <= 0:
            await it.response.send_message("❌ Invalid amount.", ephemeral=True)
            return

        if u_sender["money"] < amount:
            msg = {"ja": "残高不足です。", "en": "Insufficient funds.", "sv": "Otillräckliga medel."}
            await it.response.send_message(f"❌ {msg.get(lang, msg['en'])}", ephemeral=True)
            return

        u_target = self.ledger.get_user(target.id)
        u_sender["money"] -= amount
        u_target["money"] += amount
        self.ledger.save()

        embed = discord.Embed(title=s.get("pay_success", "Success"), color=0x88a096)
        embed.add_field(name="From", value=it.user.display_name, inline=True)
        embed.add_field(name="To", value=target.display_name, inline=True)
        embed.add_field(name="Amount", value=f"**{amount:,}** cr", inline=False)
        await it.response.send_message(embed=embed)

async def setup(bot):
    from __main__ import ledger_instance
    await bot.add_cog(Economy(bot, ledger_instance))
