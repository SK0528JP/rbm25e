import discord
from discord.ext import commands
from discord import app_commands
import random
from typing import Optional

class JankenView(discord.ui.View):
    def __init__(self, ledger, user_id):
        super().__init__(timeout=60)
        self.ledger = ledger
        self.user_id = user_id

    @discord.ui.button(label="Rock", style=discord.ButtonStyle.secondary, emoji="✊")
    async def rock(self, it: discord.Interaction, button: discord.ui.Button):
        await self.process_janken(it, "Rock")

    @discord.ui.button(label="Scissors", style=discord.ButtonStyle.secondary, emoji="✌️")
    async def scissors(self, it: discord.Interaction, button: discord.ui.Button):
        await self.process_janken(it, "Scissors")

    @discord.ui.button(label="Paper", style=discord.ButtonStyle.secondary, emoji="✋")
    async def paper(self, it: discord.Interaction, button: discord.ui.Button):
        await self.process_janken(it, "Paper")

    async def process_janken(self, it: discord.Interaction, user_choice):
        if it.user.id != self.user_id:
            await it.response.send_message("ご本人以外は操作できません。", ephemeral=True)
            return
        
        choices = ["Rock", "Scissors", "Paper"]
        bot_choice = random.choice(choices)
        
        if user_choice == bot_choice:
            result, color = "Draw", 0x94a3b8
        elif (user_choice == "Rock" and bot_choice == "Scissors") or \
             (user_choice == "Scissors" and bot_choice == "Paper") or \
             (user_choice == "Paper" and bot_choice == "Rock"):
            reward = 10
            u = self.ledger.get_user(it.user.id)
            u["money"] += reward
            self.ledger.save()
            result, color = "Win", 0x88a096
        else:
            result, color = "Loss", 0x475569

        embed = discord.Embed(title="Simulation Result", color=color)
        embed.add_field(name="User", value=user_choice, inline=True)
        embed.add_field(name="System", value=bot_choice, inline=True)
        embed.add_field(name="Outcome", value=f"**{result}**", inline=False)
        embed.set_footer(text="Interactive Module")
        
        await it.response.edit_message(content=None, embed=embed, view=None)

class Entertainment(commands.Cog):
    def __init__(self, bot, ledger):
        self.bot = bot
        self.ledger = ledger

    @app_commands.command(name="janken", description="簡易対戦シミュレーション。")
    async def janken(self, it: discord.Interaction):
        view = JankenView(self.ledger, it.user.id)
        embed = discord.Embed(title="Game Session", description="手を選択してください。", color=0x94a3b8)
        await it.response.send_message(embed=embed, view=view)

    @app_commands.command(name="omikuji", description="本日の診断。")
    async def omikuji(self, it: discord.Interaction):
        fortunes = ["Excellent", "Great", "Good", "Normal", "Bad"]
        items = ["Coffee", "Notebook", "Fresh Fruit", "Green Tea"]
        
        embed = discord.Embed(title="Daily Forecast", color=0x88a096)
        embed.add_field(name="Result", value=random.choice(fortunes), inline=True)
        embed.add_field(name="Item", value=random.choice(items), inline=True)
        embed.set_footer(text="Wellness Support")
        await it.response.send_message(embed=embed)

    @app_commands.command(name="comment", description="匿名投稿。")
    async def comment(self, it: discord.Interaction, text: str, image: Optional[discord.Attachment] = None, embed_mode: bool = False):
        await it.response.send_message("メッセージを送信しました。", ephemeral=True)
        if embed_mode:
            embed = discord.Embed(description=text, color=0xf1f5f9)
            embed.set_author(name="Anonymous Message")
            if image: embed.set_image(url=image.url)
            await it.channel.send(embed=embed)
        else:
            content = f"💬 **Anonymous**\n{text}"
            if image: content += f"\n{image.url}"
            await it.channel.send(content=content)

async def setup(bot): pass
