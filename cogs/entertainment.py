import discord
from discord.ext import commands
from discord import app_commands
import random
from typing import Optional

# --- インタラクティブ・コンポーネント：シミュレーションUI ---
class JankenView(discord.ui.View):
    def __init__(self, ledger, user_id):
        super().__init__(timeout=60)
        self.ledger = ledger
        self.user_id = user_id

    @discord.ui.button(label="グー", style=discord.ButtonStyle.secondary, emoji="✊")
    async def rock(self, it: discord.Interaction, button: discord.ui.Button):
        await self.process_janken(it, "グー")

    @discord.ui.button(label="チョキ", style=discord.ButtonStyle.secondary, emoji="✌️")
    async def scissors(self, it: discord.Interaction, button: discord.ui.Button):
        await self.process_janken(it, "チョキ")

    @discord.ui.button(label="パー", style=discord.ButtonStyle.secondary, emoji="✋")
    async def paper(self, it: discord.Interaction, button: discord.ui.Button):
        await self.process_janken(it, "パー")

    async def process_janken(self, it: discord.Interaction, user_choice):
        if it.user.id != self.user_id:
            await it.response.send_message("エラー：この操作は実行者本人のみ有効です。", ephemeral=True)
            return
        
        bot_choice = random.choice(["グー", "チョキ", "パー"])
        
        # 判定
        if user_choice == bot_choice:
            result = "引き分け（Draw）"
            color = 0x95a5a6 # Gray
            detail = "再度試行してください。"
        elif (user_choice == "グー" and bot_choice == "チョキ") or \
             (user_choice == "チョキ" and bot_choice == "パー") or \
             (user_choice == "パー" and bot_choice == "グー"):
            reward = 10
            u = self.ledger.get_user(it.user.id)
            u["money"] += reward
            self.ledger.save()
            result = "勝利（Win）"
            color = 0x2ecc71 # Green
            detail = f"インセンティブとして **{reward} 資金** が付与されました。"
        else:
            result = "敗北（Loss）"
            color = 0xe74c3c # Red
            detail = "次回の試行をお待ちしております。"

        embed = discord.Embed(title="シミュレーション結果報告", color=color)
        embed.add_field(name="ユーザーの選択", value=user_choice, inline=True)
        embed.add_field(name="システムの選択", value=bot_choice, inline=True)
        embed.add_field(name="判定結果", value=f"**{result}**", inline=False)
        embed.description = detail
        embed.set_footer(text="Entertainment Simulation Module")
        
        await it.response.edit_message(content=None, embed=embed, view=None)

# --- Cog本体 ---
class Entertainment(commands.Cog):
    def __init__(self, bot, ledger):
        self.bot = bot
        self.ledger = ledger

    @app_commands.command(name="janken", description="簡易対戦シミュレーションを実行します（勝利特典あり）。")
    async def janken(self, it: discord.Interaction):
        view = JankenView(self.ledger, it.user.id)
        embed = discord.Embed(
            title="対戦シミュレーター",
            description="手を選択してください。勝利時にはアカウントへ資金が反映されます。",
            color=0x34495e
        )
        await it.response.send_message(embed=embed, view=view)

    @app_commands.command(name="omikuji", description="本日の運勢と付随アイテムを算出します。")
    async def omikuji(self, it: discord.Interaction):
        fortunes = ["大吉", "吉", "中吉", "小吉", "末吉", "凶"]
        items = ["コーヒーチケット", "事務用品", "プレミアムランチ券", "リフレッシュアイテム"]
        
        embed = discord.Embed(title="デイリー運勢診断", color=0x9b59b6)
        embed.add_field(name="診断結果", value=f"**{random.choice(fortunes)}**", inline=True)
        embed.add_field(name="推奨アイテム", value=random.choice(items), inline=True)
        embed.set_footer(text="Wellness Support System")
        await it.response.send_message(embed=embed)

    @app_commands.command(name="meigen", description="データベースよりナレッジを引用します。")
    async def meigen(self, it: discord.Interaction):
        quotes = [
            ("一歩前進、二歩後退", "歴史的教訓"),
            ("地球は青かった", "宇宙開発記録"),
            ("量には質がある", "組織運営の視点"),
            ("困難を克服して星々へ", "スローガン")
        ]
        q, category = random.choice(quotes)
        embed = discord.Embed(title="アーカイブ引用", description=f"「{q}」", color=0x7f8c8d)
        embed.set_footer(text=f"カテゴリー：{category}")
        await it.response.send_message(embed=embed)

    @app_commands.command(name="roulette", description="複数の選択肢からランダムに1つを抽出します。")
    async def roulette(self, it: discord.Interaction, choices: str):
        c_list = choices.split()
        if not c_list:
            await it.response.send_message("エラー：選択肢が入力されていません。", ephemeral=True)
            return
        
        result = random.choice(c_list)
        embed = discord.Embed(title="ランダム抽出結果", color=0x34495e)
        embed.description = f"厳正な抽選の結果、以下の項目が選出されました：\n\n**{result}**"
        embed.set_footer(text="Decision Support Tool")
        await it.response.send_message(embed=embed)

    @app_commands.command(name="comment", description="匿名でメッセージを投稿します。")
    @app_commands.describe(
        text="投稿内容", 
        image="添付画像（任意）", 
        embed_mode="埋め込み形式を適用するか選択してください"
    )
    async def comment(
        self, 
        it: discord.Interaction, 
        text: str, 
        image: Optional[discord.Attachment] = None,
        embed_mode: bool = False
    ):
        await it.response.send_message("メッセージを受理しました。匿名にて転送します。", ephemeral=True)

        if embed_mode:
            embed = discord.Embed(description=text, color=0xecf0f1)
            embed.set_author(name="匿名ユーザーからのメッセージ", icon_url=self.bot.user.display_avatar.url)
            if image:
                embed.set_image(url=image.url)
            embed.set_footer(text="Anonymous Communication Service")
            await it.channel.send(embed=embed)
        else:
            content = f"💬 **【匿名投稿】**\n{text}"
            if image:
                content += f"\n{image.url}"
            await it.channel.send(content=content)

async def setup(bot):
    pass
