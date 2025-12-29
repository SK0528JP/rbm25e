import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from datetime import datetime

class Economy(commands.Cog):
    def __init__(self, bot, ledger):
        self.bot = bot
        self.ledger = ledger
        self.lock = asyncio.Lock()  # データ競合防止用

    # --- デザイン定数 ---
    COLOR_NORDIC_GREEN = 0xA8B5A2  # 落ち着いたセージグリーン
    COLOR_NORDIC_SLATE = 0x94a3b8  # 洗練されたブルーグレー
    COLOR_SOFT_ERROR = 0xe2e2e2    # 威圧感のないライトグレー
    FOOTER_TEXT = "Financial Services Suite | rb.m25"

    @app_commands.command(name="pay", description="指定したユーザーへ資産を安全に送金します")
    @app_commands.describe(target="送金相手のユーザー", amount="送金する金額（cr）")
    async def pay(self, it: discord.Interaction, target: discord.Member, amount: int):
        """ユーザー間送金機能：北欧モダンUI"""
        
        # 1. バリデーション（UX：エラーは自分にだけ見える）
        if target.bot:
            return await it.response.send_message(
                embed=discord.Embed(description="ボットへの送金は承認されませんでした。", color=self.COLOR_SOFT_ERROR),
                ephemeral=True
            )
        
        if target.id == it.user.id:
            return await it.response.send_message(
                embed=discord.Embed(description="自身への送金はできません。", color=self.COLOR_SOFT_ERROR),
                ephemeral=True
            )
            
        if amount <= 0:
            return await it.response.send_message(
                embed=discord.Embed(description="1cr以上の有効な金額を入力してください。", color=self.COLOR_SOFT_ERROR),
                ephemeral=True
            )

        # 2. ロジック実行（データ整合性を確保）
        async with self.lock:
            u_sender = self.ledger.get_user(it.user.id)
            current_balance = u_sender.get("money", 0)

            if current_balance < amount:
                return await it.response.send_message(
                    embed=discord.Embed(
                        description=f"残高が不足しています。\n現在の所持金: `{current_balance:,} cr`", 
                        color=self.COLOR_SOFT_ERROR
                    ),
                    ephemeral=True
                )

            # 更新処理
            u_target = self.ledger.get_user(target.id)
            u_sender["money"] = current_balance - amount
            u_target["money"] = u_target.get("money", 0) + amount
            
            # Gistへの保存（I/Oブロッキング回避）
            try:
                await asyncio.to_thread(self.ledger.save)
            except Exception as e:
                # 失敗時のロールバック的な表示（簡易版）
                return await it.response.send_message(
                    embed=discord.Embed(description="システムエラー：取引を完了できませんでした。", color=self.COLOR_SOFT_ERROR),
                    ephemeral=True
                )

        # 3. 成功時UIデザイン
        embed = discord.Embed(
            title="Transaction Receipt",
            description="送金リクエストが正常に承認されました。",
            color=self.COLOR_NORDIC_GREEN,
            timestamp=datetime.now()
        )
        
        # モノトーンのコードブロックで情報を構造化
        embed.add_field(
            name="Sender", 
            value=f"```\n{it.user.display_name}\n```", 
            inline=True
        )
        embed.add_field(
            name="Recipient", 
            value=f"```\n{target.display_name}\n```", 
            inline=True
        )
        
        # 金額を強調し、余白を感じさせるレイアウト
        embed.add_field(
            name="Amount Transferred", 
            value=f"## {amount:,} cr", 
            inline=False
        )

        embed.set_footer(text=self.FOOTER_TEXT)
        if it.guild and it.guild.icon:
            embed.set_footer(text=self.FOOTER_TEXT, icon_url=it.guild.icon.url)
        
        await it.response.send_message(embed=embed)

    @app_commands.command(name="balance", description="現在の資産と貢献度を確認します")
    async def balance(self, it: discord.Interaction):
        """資産確認：カード型UI"""
        user_data = self.ledger.get_user(it.user.id)
        money = user_data.get("money", 0)
        xp = user_data.get("xp", 0)
        
        embed = discord.Embed(
            title=f"Portfolio: {it.user.display_name}",
            color=self.COLOR_NORDIC_SLATE,
            timestamp=datetime.now()
        )
        
        # 情報をリスト形式で整理
        embed.add_field(name="Current Balance", value=f"**{money:,}** cr", inline=False)
        embed.add_field(name="Total Contribution", value=f"**{xp:,}** points", inline=False)
        
        embed.set_footer(text="Official Financial Report")
        
        await it.response.send_message(embed=embed)

async def setup(bot):
    # main.pyからインスタンスを取得する際の標準的な構成
    from __main__ import ledger_instance
    await bot.add_cog(Economy(bot, ledger_instance))
