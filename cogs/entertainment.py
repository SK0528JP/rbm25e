import discord
from discord.ext import commands
from discord import app_commands
import random

class Entertainment(commands.Cog):
    def __init__(self, bot, ledger):
        self.bot = bot
        self.ledger = ledger

    @app_commands.command(name="janken", description="じゃんけんで遊びます（勝利で10cr獲得）")
    @app_commands.describe(choice="自分の手を選んでください")
    @app_commands.choices(choice=[
        app_commands.Choice(name="👊 グー", value="rock"),
        app_commands.Choice(name="✋ パー", value="paper"),
        app_commands.Choice(name="✌️ チョキ", value="scissors"),
    ])
    async def janken(self, it: discord.Interaction, choice: app_commands.Choice[str]):
        # ボットの手を決定
        bot_choice = random.choice(["rock", "paper", "scissors"])
        hands = {
            "rock": "👊 (グー)",
            "paper": "✋ (パー)",
            "scissors": "✌️ (チョキ)"
        }

        # 勝敗判定ロジック
        if choice.value == bot_choice:
            result_text = "結果は **あいこ** です。"
            color = 0x94a3b8 # グレー
            reward_msg = ""
        elif (choice.value == "rock" and bot_choice == "scissors") or \
             (choice.value == "paper" and bot_choice == "rock") or \
             (choice.value == "scissors" and bot_choice == "paper"):
            result_text = "おめでとうございます！ **あなたの勝ち** です！"
            color = 0x2ecc71 # 緑
            # 勝利報酬の付与
            u = self.ledger.get_user(it.user.id)
            u["money"] += 10
            self.ledger.save()
            reward_msg = "💰 報酬として **10 cr** を付与しました。"
        else:
            result_text = "残念... **あなたの負け** です。"
            color = 0xe74c3c # 赤
            reward_msg = ""

        embed = discord.Embed(title="Rb m/25 娯楽ユニット | じゃんけん", color=color)
        embed.add_field(name="あなた", value=hands[choice.value], inline=True)
        embed.add_field(name="ボット", value=hands[bot_choice], inline=True)
        embed.add_field(name="判定", value=result_text, inline=False)
        
        if reward_msg:
            embed.set_footer(text=reward_msg)
        else:
            embed.set_footer(text="Rb m/25 Entertainment Unit")

        await it.response.send_message(embed=embed)

    @app_commands.command(name="fortune", description="今日のおみくじを引きます")
    async def fortune(self, it: discord.Interaction):
        # おみくじの結果リスト
        results = [
            "✨ 大吉 (超幸運)", 
            "🍃 中吉", 
            "🌱 小吉", 
            "☀ 吉", 
            "☁ 末吉", 
            "👣 凶"
        ]
        res = random.choice(results)
        
        embed = discord.Embed(
            title="Rb m/25 娯楽ユニット | おみくじ", 
            description=f"今日の結果は... **{res}** です！",
            color=0x6366f1
        )
        embed.set_footer(text="Rb m/25 Entertainment Unit")
        
        await it.response.send_message(embed=embed)

async def setup(bot):
    from __main__ import ledger_instance
    await bot.add_cog(Entertainment(bot, ledger_instance))
