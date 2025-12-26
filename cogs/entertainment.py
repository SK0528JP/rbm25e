import discord
from discord.ext import commands
from discord import app_commands
import random
from typing import Optional

# --- じゃんけん専用：ボタンUIとロジック ---
class JankenView(discord.ui.View):
    def __init__(self, ledger, user_id):
        super().__init__(timeout=60)
        self.ledger = ledger
        self.user_id = user_id

    @discord.ui.button(label="グー", style=discord.ButtonStyle.primary, emoji="✊")
    async def rock(self, it: discord.Interaction, button: discord.ui.Button):
        await self.process_janken(it, "グー")

    @discord.ui.button(label="チョキ", style=discord.ButtonStyle.success, emoji="✌️")
    async def scissors(self, it: discord.Interaction, button: discord.ui.Button):
        await self.process_janken(it, "チョキ")

    @discord.ui.button(label="パー", style=discord.ButtonStyle.danger, emoji="✋")
    async def paper(self, it: discord.Interaction, button: discord.ui.Button):
        await self.process_janken(it, "パー")

    async def process_janken(self, it: discord.Interaction, user_choice):
        if it.user.id != self.user_id:
            await it.response.send_message("❌ これは君の勝負ではない！", ephemeral=True)
            return
        
        bot_choice = random.choice(["グー", "チョキ", "パー"])
        
        if user_choice == bot_choice:
            result = "引き分けだ。労働に戻れ。"
            color = 0x808080 
        elif (user_choice == "グー" and bot_choice == "チョキ") or \
             (user_choice == "チョキ" and bot_choice == "パー") or \
             (user_choice == "パー" and bot_choice == "グー"):
            reward = 10
            u = self.ledger.get_user(it.user.id)
            u["money"] += reward
            self.ledger.save()
            result = f"君の勝ちだ！報奨金として **{reward} 資金** を授与する。"
            color = 0xffd700 
        else:
            result = "私の勝ちだ。修行が足りんぞ。"
            color = 0xff0000 

        embed = discord.Embed(title="✊✌️✋ じゃんけん結果報告", color=color)
        embed.add_field(name="同志の選択", value=user_choice, inline=True)
        embed.add_field(name="国家の選択", value=bot_choice, inline=True)
        embed.add_field(name="最終判定", value=f"**{result}**", inline=False)
        embed.set_footer(text="中央競技委員会 🏆")
        
        await it.response.edit_message(content=None, embed=embed, view=None)

# --- Cog本体 ---
class Entertainment(commands.Cog):
    def __init__(self, bot, ledger):
        self.bot = bot
        self.ledger = ledger

    @app_commands.command(name="janken", description="国家代表と真剣勝負（勝てば報酬あり）")
    async def janken(self, it: discord.Interaction):
        view = JankenView(self.ledger, it.user.id)
        embed = discord.Embed(
            title="✊✌️✋ 国家対抗じゃんけん大会",
            description="勝利すれば国庫よりささやかな報酬が支払われる。\nいざ、手を選べ！",
            color=0x00aaff
        )
        await it.response.send_message(embed=embed, view=view)

    @app_commands.command(name="omikuji", description="今日の運勢と配給物資の受取")
    async def omikuji(self, it: discord.Interaction):
        fortunes = ["大吉 (革命的成功)", "吉 (順調な労働)", "中吉", "小吉", "末吉", "凶 (再教育が必要)"]
        items = ["高級ウォッカ", "特製ピロシキ", "マトリョーシカ", "栄養黒パン", "温かいボルシチ"]
        
        embed = discord.Embed(title="🥠 国家公式おみくじ", color=0xff0000)
        embed.add_field(name="今日の運勢", value=f"**{random.choice(fortunes)}**", inline=True)
        embed.add_field(name="特別配給品", value=random.choice(items), inline=True)
        embed.set_footer(text="国家配給局 📦")
        await it.response.send_message(embed=embed)

    @app_commands.command(name="meigen", description="歴史的偉人の教訓を引用")
    async def meigen(self, it: discord.Interaction):
        quotes = [
            ("一歩前進、二歩後退", "ウラジーミル・レーニン"),
            ("地球は青かった", "ユーリ・ガガーリン"),
            ("勝利は我々に、未来は労働者に", "国家スローガン"),
            ("量には質がある", "ヨシフ・スターリン"),
            ("困難を克服して星々へ", "宇宙開発局")
        ]
        q, author = random.choice(quotes)
        embed = discord.Embed(title="📖 歴史的教訓", description=f"### 「{q}」", color=0xcc0000)
        embed.set_footer(text=f"― {author}")
        await it.response.send_message(embed=embed)

    @app_commands.command(name="roulette", description="国家が君の迷いに決着をつける（スペース区切り）")
    async def roulette(self, it: discord.Interaction, choices: str):
        c_list = choices.split()
        if not c_list:
            await it.response.send_message("❌ 報告：選択肢が空だ。判定不能。", ephemeral=True)
            return
        
        result = random.choice(c_list)
        embed = discord.Embed(title="🎲 国家的意志決定", color=0x333333)
        embed.description = f"厳正なる抽選の結果、国家は以下の案を採択した：\n\n## **{result}**"
        embed.set_footer(text="中央決定委員会 ⚖️")
        await it.response.send_message(embed=embed)

    @app_commands.command(name="comment", description="匿名で声明を発表する")
    @app_commands.describe(
        text="発表する内容", 
        image="添付する画像（任意）", 
        embed_mode="はい：公式声明形式（埋め込み）、いいえ：通常テキスト形式（デフォルト）"
    )
    async def comment(
        self, 
        it: discord.Interaction, 
        text: str, 
        image: Optional[discord.Attachment] = None,
        embed_mode: bool = False
    ):
        # 1. 実行者のみに受理報告（匿名性を守るため）
        await it.response.send_message("📨 報告：声明を受理した。匿名で配信する。", ephemeral=True)

        # 2. チャンネルに投稿（投稿者はボットになる）
        if embed_mode:
            embed = discord.Embed(description=f"### {text}", color=0xff0000)
            embed.set_author(name="📜 国家公式声明（匿名）", icon_url=self.bot.user.display_avatar.url)
            if image:
                embed.set_image(url=image.url)
            embed.set_footer(text="※この声明は中央匿名化処理を受けています")
            await it.channel.send(embed=embed)
        else:
            content = f"📢 **【匿名声明】**\n{text}"
            if image:
                content += f"\n{image.url}"
            await it.channel.send(content=content)

async def setup(bot):
    pass
