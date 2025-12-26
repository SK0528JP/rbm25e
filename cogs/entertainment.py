import discord
from discord.ext import commands
from discord import app_commands
import random
from typing import Optional

# --- じゃんけん用ボタンUI ---
class JankenView(discord.ui.View):
    def __init__(self, ledger, user_id):
        super().__init__(timeout=60)
        self.ledger = ledger
        self.user_id = user_id

    @discord.ui.button(label="グー", style=discord.ButtonStyle.primary)
    async def rock(self, it: discord.Interaction, button: discord.ui.Button):
        await self.process_janken(it, "グー")

    @discord.ui.button(label="チョキ", style=discord.ButtonStyle.success)
    async def scissors(self, it: discord.Interaction, button: discord.ui.Button):
        await self.process_janken(it, "チョキ")

    @discord.ui.button(label="パー", style=discord.ButtonStyle.danger)
    async def paper(self, it: discord.Interaction, button: discord.ui.Button):
        await self.process_janken(it, "パー")

    async def process_janken(self, it: discord.Interaction, user_choice):
        if it.user.id != self.user_id:
            await it.response.send_message("❌ これは君の勝負ではない！", ephemeral=True)
            return
        
        bot_choice = random.choice(["グー", "チョキ", "パー"])
        result = ""
        if user_choice == bot_choice:
            result = "引き分けだ。労働に戻れ。"
        elif (user_choice == "グー" and bot_choice == "チョキ") or \
             (user_choice == "チョキ" and bot_choice == "パー") or \
             (user_choice == "パー" and bot_choice == "グー"):
            reward = 10
            u = self.ledger.get_user(it.user.id)
            u["money"] += reward
            self.ledger.save()
            result = f"君の勝ちだ！報奨金として **{reward} 資金** を授与する。"
        else:
            result = "私の勝ちだ。修行が足りんぞ。"

        await it.response.edit_message(content=f"君：{user_choice} 🛰️ 私：{bot_choice}\n**結果：{result}**", view=None)

# --- Cog本体 ---
class Entertainment(commands.Cog):
    def __init__(self, bot, ledger):
        self.bot = bot
        self.ledger = ledger

    @app_commands.command(name="janken", description="国家代表と真剣勝負（勝てば資金授与）")
    async def janken(self, it: discord.Interaction):
        view = JankenView(self.ledger, it.user.id)
        await it.response.send_message("✊✌️✋ いざ尋常に勝負！手を選べ：", view=view)

    @app_commands.command(name="omikuji", description="今日の運勢と配給物資を確認")
    async def omikuji(self, it: discord.Interaction):
        fortunes = ["大吉 (革命的成功)", "吉 (順調な労働)", "中吉", "小吉", "末吉", "凶 (再教育が必要)"]
        items = ["ウォッカ", "ピロシキ", "マトリョーシカ", "黒パン", "ボルシチ"]
        res = f"🥠 運勢：**{random.choice(fortunes)}**\n📦 今日の配給：**{random.choice(items)}**"
        await it.response.send_message(res)

    @app_commands.command(name="meigen", description="歴史的偉人の名言を引用")
    async def meigen(self, it: discord.Interaction):
        quotes = [
            "「一歩前進、二歩後退」— レーニン",
            "「地球は青かった」— ガガーリン",
            "「勝利は我々に、未来は労働者に」",
            "「量には質がある」— スターリン"
        ]
        await it.response.send_message(f"📖 **歴史の教訓：**\n{random.choice(quotes)}")

    @app_commands.command(name="roulette", description="国家が君の迷いに決着をつける（スペース区切りで入力）")
    async def roulette(self, it: discord.Interaction, choices: str):
        c_list = choices.split()
        if not c_list:
            await it.response.send_message("❌ 選択肢を入力せよ。", ephemeral=True)
            return
        result = random.choice(c_list)
        await it.response.send_message(f"🎲 厳正なる抽選の結果、国家は **「{result}」** を採択した！")

    @app_commands.command(name="comment", description="公式声明の発表（画像添付可能）")
    async def comment(self, it: discord.Interaction, text: str, image: Optional[discord.Attachment] = None):
        embed = discord.Embed(description=text, color=0xff0000)
        embed.set_author(name="📜 国家公式声明")
        if image:
            embed.set_image(url=image.url)
        await it.response.send_message(embed=embed)

async def setup(bot):
    pass
