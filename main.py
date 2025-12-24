import os
import asyncio
import random
import json
from datetime import datetime, timezone, timedelta
from typing import Optional

import discord
from discord.ext import commands, tasks
from discord import app_commands

# ===== 基本設定 =====
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.message_content = True

JST = timezone(timedelta(hours=9))
THEME_COLOR = 0xCC0000 
DATA_FILE = "soviet_data.json"

# ===== 名言アーカイブ =====
QUOTES_ARCHIVE = [
    {"text": "学習し、学習し、そして学習することだ。", "author": "ウラジーミル・レーニン", "faction": "ソビエト連邦"},
    {"text": "一人の死は悲劇だが、数百万人の死は統計上の数字に過ぎない。", "author": "ヨシフ・スターリン", "faction": "ソビエト連邦"},
    {"text": "地球は青かった。", "author": "ユーリ・ガガーリン", "faction": "ソビエト連邦"},
    {"text": "汗を流せば流すほど、血を流さずに済む。", "author": "エルヴィン・ロンメル", "faction": "ドイツ"},
    {"text": "計画がその通りに進むことなど、実戦では稀である。", "author": "ヘルムート・フォン・モルトケ", "faction": "ドイツ"},
    {"text": "主は我が守りなり。", "author": "グスタフ2世アドルフ", "faction": "スウェーデン王国"},
    {"text": "平和なときにこそ、戦争の準備をせよ。", "author": "スウェーデン民間防衛読本", "faction": "スウェーデン王国"},
    {"text": "信頼せよ、だが検証せよ。", "author": "ロシアのことわざ", "faction": "ソビエト連邦"}
]

# ===== Botクラス ===== 
class SovietBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.last_signal_hour = -1 
        self.user_data = {}

    async def setup_hook(self):
        self.load_data()
        try:
            await self.tree.sync()
            print("--- 国家指令システムの同期が完了した ---")
        except Exception as e:
            print(f"同期失敗、直ちに技術局へ報告せよ: {e}")

    def load_data(self):
        """ユーザーデータの読み込み"""
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    self.user_data = json.load(f)
            except Exception as e:
                print(f"データ読み込みエラー: {e}")
                self.user_data = {}
        else:
            self.user_data = {}

    def save_data(self):
        """ユーザーデータの保存"""
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.user_data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"データ保存エラー: {e}")

    async def add_xp(self, user_id: str):
        """国家への貢献度(XP)を加算"""
        now = datetime.now().timestamp()
        if user_id not in self.user_data:
            self.user_data[user_id] = {"xp": 0, "last_msg": 0}
        
        # クールダウン (5秒)
        if now - self.user_data[user_id].get("last_msg", 0) < 5:
            return

        gain = random.randint(10, 20)
        self.user_data[user_id]["xp"] += gain
        self.user_data[user_id]["last_msg"] = now
        self.save_data()

bot = SovietBot()

# ===== UI部品: じゃんけん View =====
class JankenView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    async def handle_play(self, interaction: discord.Interaction, user_hand: str):
        bot_hand = random.choice(["グー", "チョキ", "パー"])
        hands_emoji = {"グー": "✊", "チョキ": "✌️", "パー": "✋"}
        
        if user_hand == bot_hand:
            res, color, foot = "引き分け", 0x808080, "両者譲らず。交渉は継続される。"
        elif ((user_hand == "グー" and bot_hand == "チョキ") or
              (user_hand == "チョキ" and bot_hand == "パー") or
              (user_hand == "パー" and bot_hand == "グー")):
            res, color, foot = "勝利", 0x00FF00, "お見事です、同志！ 人民の勝利だ！"
        else:
            res, color, foot = "敗北", 0x000000, "資本主義的な軟弱さが露見したな。再教育が必要だ。"

        embed = discord.Embed(title="☭ 戦略的決着報告書", color=color)
        embed.add_field(name="同志の選択", value=f"{hands_emoji[user_hand]} {user_hand}", inline=True)
        embed.add_field(name="国家の選択", value=f"{hands_emoji[bot_hand]} {bot_hand}", inline=True)
        embed.add_field(name="判定", value=f"**{res}**", inline=False)
        embed.set_footer(text=foot)
        
        # ボタンを無効化して更新
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(embed=embed)

    @discord.ui.button(label="強行突破", style=discord.ButtonStyle.danger, emoji="✊")
    async def rock(self, it, btn): await self.handle_play(it, "グー")
    @discord.ui.button(label="分断工作", style=discord.ButtonStyle.danger, emoji="✌️")
    async def sciss(self, it, btn): await self.handle_play(it, "チョキ")
    @discord.ui.button(label="包囲作戦", style=discord.ButtonStyle.danger, emoji="✋")
    async def paper(self, it, btn): await self.handle_play(it, "パー")

# ===== イベント =====
@bot.event
async def on_ready():
    # ステータスを「退席中」、メッセージを「労働中」に設定
    await bot.change_presence(
        status=discord.Status.idle,
        activity=discord.Activity(type=discord.ActivityType.playing, name="🎵 労働中")
    )
    print(f"同志 {bot.user} は現線にて労働に従事している。")
    if not time_signal.is_running():
        time_signal.start()

@bot.event
async def on_message(message):
    if message.author.bot: return
    await bot.add_xp(str(message.author.id))
    await bot.process_commands(message)

# ===== コマンド群 =====

@bot.tree.command(name="comment", description="国家の声明としてメッセージを配信する")
@app_commands.describe(content="声明の内容 (\\nで改行)", image="添付画像 (任意)", use_embed="埋め込み形式を適用する")
async def comment(interaction: discord.Interaction, content: str, image: Optional[discord.Attachment] = None, use_embed: bool = False):
    content = content.replace("\\n", "\n")
    
    if use_embed:
        embed = discord.Embed(description=content, color=THEME_COLOR)
        embed.set_author(name="☭ 国家公式声明", icon_url=bot.user.display_avatar.url)
        if image: embed.set_image(url=image.url)
        await interaction.channel.send(embed=embed)
    else:
        file = await image.to_file() if image else None
        await interaction.channel.send(content=content, file=file)
    
    await interaction.response.send_message("声明の配信を完了した。", ephemeral=True)

@bot.tree.command(name="ping", description="通信インフラの状況を確認する")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    embed = discord.Embed(title="☭ 通信状況報告書", description=f"モスクワ中央局との遅延: **{latency}ms**", color=THEME_COLOR)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="janken", description="国家との戦略的決着（じゃんけん）を行う")
async def janken(interaction: discord.Interaction):
    embed = discord.Embed(title="☭ 戦略的決着", description="同志よ、次の一手を選択せよ。国家は君の忠誠を見ている。", color=THEME_COLOR)
    await interaction.response.send_message(embed=embed, view=JankenView())

@bot.tree.command(name="omikuji", description="本日の配給物資と運勢を受け取る")
async def omikuji(interaction: discord.Interaction):
    fortunes = [
        {"r": "労働英雄級 (大吉)", "i": "特級ウォッカと黒パン", "c": 0xFFD700, "d": "君は祖国の誇りだ！"},
        {"r": "模範的労働者 (中吉)", "i": "追加のジャガイモ配給", "c": 0xCC0000, "d": "ノルマ達成を称賛する。"},
        {"r": "一般的市民 (小吉)", "i": "温かいビーツのスープ", "c": 0xCC0000, "d": "堅実な労働こそが勝利の鍵だ。"},
        {"r": "要注意人物 (末吉)", "i": "古びた塩パン", "c": 0x8B4513, "d": "生産性の向上に努めるように。"},
        {"r": "シベリア送り (凶)", "i": "極北への片道切符", "c": 0x0000FF, "d": "再教育キャンプでの内省を勧告する。"}
    ]
    f = random.choice(fortunes)
    embed = discord.Embed(title="☭ 配給物資通達書", color=f["c"])
    embed.add_field(name="階級判定", value=f"**{f['r']}**", inline=False)
    embed.add_field(name="支給品", value=f["i"], inline=True)
    embed.set_footer(text=f["d"])
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="meigen", description="歴史的アーカイブより指導者の金言を引用する")
async def meigen(interaction: discord.Interaction):
    quote = random.choice(QUOTES_ARCHIVE)
    embed = discord.Embed(title="📜 歴史的記録アーカイブ", description=f"```\n{quote['text']}\n```", color=THEME_COLOR)
    embed.add_field(name="発言者", value=quote["author"], inline=True)
    embed.add_field(name="勢力", value=quote["faction"], inline=True)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="ranking", description="国家への貢献度（XP）ランキングを表示する")
async def ranking(interaction: discord.Interaction):
    sorted_users = sorted(bot.user_data.items(), key=lambda x: x[1]["xp"], reverse=True)[:10]
    embed = discord.Embed(title="☭ 労働英雄・貢献度ランキング", color=THEME_COLOR)
    
    ranking_text = ""
    for i, (u_id, d) in enumerate(sorted_users):
        medal = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else f"#{i+1}"
        ranking_text += f"{medal} <@{u_id}>: **{d['xp']}** 貢献pt\n"
    
    embed.description = ranking_text if ranking_text else "記録された労働実績がない。"
    my_xp = bot.user_data.get(str(interaction.user.id), {}).get("xp", 0)
    embed.set_footer(text=f"あなたの現在の貢献度: {my_xp} ポイント")
    await interaction.response.send_message(embed=embed)

# ===== 時報タスク =====
@tasks.loop(seconds=60)
async def time_signal():
    now = datetime.now(JST)
    if now.minute == 0 and bot.last_signal_hour != now.hour:
        bot.last_signal_hour = now.hour
        embed = discord.Embed(title="⏰ 定時放送", description=f"時刻は **{now.hour:02d}:00** となった。同志諸君、労働に励め。", color=THEME_COLOR)
        for guild in bot.guilds:
            if guild.system_channel:
                try: await guild.system_channel.send(embed=embed)
                except: pass

bot.run(TOKEN)
