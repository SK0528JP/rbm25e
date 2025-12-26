import discord
from discord.ext import commands
from discord import app_commands

class Economy(commands.Cog):
    def __init__(self, bot, ledger):
        self.bot = bot
        self.ledger = ledger

    @app_commands.command(name="ranking", description="サーバー内のランキングを表示します")
    @app_commands.choices(type=[
        app_commands.Choice(name="貢献度 (XP)", value="xp"),
        app_commands.Choice(name="資産 (Credits)", value="money"),
    ])
    async def ranking(self, it: discord.Interaction, type: str = "xp"):
        # 1. 応答を保留する（3秒ルールを回避）
        await it.response.defer()

        all_users = self.ledger.data
        
        if not all_users:
            await it.followup.send("📊 まだランキングデータが蓄積されていません。")
            return

        # 2. データのソート（上位10名）
        sorted_users = sorted(
            all_users.items(), 
            key=lambda x: x[1].get(type, 0), 
            reverse=True
        )[:10]

        title = "貢献度ランキング (XP)" if type == "xp" else "資産ランキング (Credits)"
        embed = discord.Embed(
            title=f"🏆 {title}", 
            description="上位10名のデータを表示しています。", 
            color=0x94a3b8
        )
        
        rank_text = ""
        for i, (uid_str, stats) in enumerate(sorted_users, 1):
            uid = int(uid_str)
            
            # 3. メンバー名の取得（高速化ロジック）
            # キャッシュから検索
            member = it.guild.get_member(uid)
            if member:
                name = member.display_name
            else:
                # キャッシュにいなければ bot.get_user を試す（APIを叩かない）
                user = self.bot.get_user(uid)
                name = user.display_name if user else f"User_{uid_str[:4]}"
            
            val = stats.get(type, 0)
            unit = "XP" if type == "xp" else "cr"
            
            rank_text += f"`{i}位` **{name}** : {val:,} {unit}\n"
        
        embed.add_field(name="順位 / ユーザー / スコア", value=rank_text or "表示可能なデータがありません。", inline=False)
        embed.set_footer(text="Rb m/25 Financial Services")
        
        # 4. 保留していた応答を送信
        await it.followup.send(embed=embed)

    @app_commands.command(name="pay", description="他のユーザーに資産を送金します")
    @app_commands.describe(target="送金相手", amount="送る金額")
    async def pay(self, it: discord.Interaction, target: discord.Member, amount: int):
        if target.bot:
            await it.response.send_message("❌ ボットに送金することはできません。", ephemeral=True)
            return

        if amount <= 0:
            await it.response.send_message("❌ 1cr以上の金額を指定してください。", ephemeral=True)
            return

        u_sender = self.ledger.get_user(it.user.id)
        
        # 残高チェック
        if u_sender.get("money", 0) < amount:
            await it.response.send_message(f"❌ 残高が不足しています。（現在の所持金: {u_sender.get('money', 0)} cr）", ephemeral=True)
            return

        # 送金処理
        u_target = self.ledger.get_user(target.id)
        u_sender["money"] = u_sender.get("money", 0) - amount
        u_target["money"] = u_target.get("money", 0) + amount
        
        # Gistへの保存
        self.ledger.save()

        embed = discord.Embed(title="✅ 送金が完了しました", color=0x88a096)
        embed.add_field(name="送り主", value=it.user.display_name, inline=True)
        embed.add_field(name="受取人", value=target.display_name, inline=True)
        embed.add_field(name="送金額", value=f"**{amount:,}** cr", inline=False)
        embed.set_footer(text="Rb m/25 Financial Services")
        
        await it.response.send_message(embed=embed)

async def setup(bot):
    from __main__ import ledger_instance
    await bot.add_cog(Economy(bot, ledger_instance))
