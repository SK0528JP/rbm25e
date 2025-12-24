import os
import asyncio
import random
import json
from datetime import datetime, timezone, timedelta

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

# ===== 名言データベース =====
QUOTES_ARCHIVE = [
    {"text": "学習し、学習し、そして学習することだ。", "author": "ウラジーミル・レーニン", "faction": "ソビエト連邦"},
    {"text": "一人の死は悲劇だが、数百万人の死は統計上の数字に過ぎない。", "author": "ヨシフ・スターリン", "faction": "ソビエト連邦"},
    {"text": "幹部がすべてを決定する。", "author": "ヨシフ・スターリン", "faction": "ソビエト連邦"},
    {"text": "地球は青かった。", "author": "ユーリ・ガガーリン", "faction": "ソビエト連邦"},
    {"text": "信頼せよ、だが検証せよ。", "author": "ロシアのことわざ", "faction": "ソビエト連邦"},
    {"text": "汗を流せば流すほど、血を流さずに済む。", "author": "エルヴィン・ロンメル", "faction": "ドイツ"},
    {"text": "計画がその通りに進むことなど、実戦では稀である。", "author": "ヘルムート・フォン・モルトケ", "faction": "ドイツ"},
    {"text": "主は我が守りなり。", "author": "グスタフ2世アドルフ", "faction": "スウェーデン王国"},
    {"text": "私は私の兵士たちが何を食べるかを知るまでは食事をとらない。", "author": "カール12世", "faction": "スウェーデン王国"}
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
            print("--- 全指令システムの同期を完了した ---")
        except Exception as e:
            print(f"同期失敗: {e}")

    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    self.user_data = json.load(f)
            except:
                self.user_data = {}
        else:
            self.user_data = {}

    def save_data(self):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.user_data, f, ensure_ascii=False, indent=4)

    async def add_xp(self, user_id: str):
        now = datetime.now().timestamp()
        if user_id not in self.user_data:
            self.user_data[user_id] = {"xp": 0, "last_msg": 0}
        
        if now - self.user_data[user_id].get("last_msg", 0) < 5:
            return

        self.user_data[user_id]["xp"] += random.randint(10, 20)
        self.user_data[user_id]["last_msg"] = now
        self.save_data()

bot = SovietBot()

# ===== じゃんけん View クラス =====
class JankenView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    async def play(self, interaction: discord.Interaction, user_hand: str):
        bot_hand = random.choice(["グー", "チョキ", "パー"])
        hands_emoji = {"グー": "✊", "チョキ": "✌️", "パー": "✋"}
        
        if user_hand == bot_hand:
            result_text, footer = "引き分け", "両者譲らず。交渉は継続される。"
        elif (
            (user_hand == "グー" and bot_hand == "チョキ") or
            (user_hand == "チョキ" and bot_hand == "パー") or
            (user_hand == "パー" and bot_hand == "グー")
        ):
            result_text, footer = "勝利", "お見事です、同志！ 人民の勝利だ！"
        else:
            result_text, footer = "敗北", "資本主義的な軟弱さが露見したな。出直したまえ。"

        embed = discord.Embed(title="☭ 戦略的決着の結果", color=THEME_COLOR)
        embed.add_field(name="同志の手", value=f"{hands_emoji[user_hand]} {user_hand}", inline=True)
        embed.add_field(name="国家の手", value=f"{hands_emoji[bot_hand]} {bot_hand}", inline=True)
        embed.add_field(name="判定", value=f"**{result_text}**", inline=False)
        embed.set_footer(text=footer)
        await interaction.response.send_message(embed=embed)

    @discord.ui.button(label="強行突破", style=discord.ButtonStyle.danger, emoji="✊")
    async def rock(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.play(interaction, "グー")
 
    @discord.ui.button(label="分断工作", style=discord.ButtonStyle.danger, emoji="✌️")
    async def scissors(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.play(interaction, "チョキ")

    @discord.ui.button(label="包囲作戦", style=discord.ButtonStyle.danger, emoji="✋")
    async def paper(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.play(interaction, "パー")

# ===== イベント =====
@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="同志の勤務態度"))
    print(f"同志 {bot.user} が現線に復帰した。")
    if not time_signal.is_running():
        time_signal.start()

@bot.event
async def on_message(message):
    if message.author.bot: return
    await bot.add_xp(str(message.author.id))
    await bot.process_commands(message)

# ===== コマンド群 =====

@bot.tree.command(name="ping", description="通信状況の確認")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f"通信良好。遅延: **{latency}ms**", ephemeral=True)

@bot.tree.command(name="janken", description="国家との戦略的決着（じゃんけん）を行う")
async def janken(interaction: discord.Interaction):
    embed = discord.Embed(title="☭ 戦略的選択", description="同志よ、次の一手を選択せよ。", color=THEME_COLOR)
    await interaction.response.send_message(embed=embed, view=JankenView())

@bot.tree.command(name="omikuji", description="本日の配給物資を受け取る")
async def omikuji(interaction: discord.Interaction):
    fortunes = [
        {"r": "労働英雄級 (大吉)", "i": "特級ウォッカ", "d": "党は同志を高く評価している！"},
        {"r": "模範労働者 (中吉)", "i": "追加のジャガイモ", "d": "ノルマ達成おめでとう。"},
        {"r": "一般的市民 (小吉)", "i": "ビーツのスープ", "d": "平穏こそが最大の幸福である。"},
        {"r": "要注意人物 (末吉)", "i": "塩のみ", "d": "生産性が低下している。自己批判せよ。"},
        {"r": "シベリア送り (凶)", "i": "片道切符", "d": "反革命的な態度だ。再教育が必要だ。"}
    ]
    f = random.choice(fortunes)
    embed = discord.Embed(title="☭ 配給結果通報", color=THEME_COLOR)
    embed.add_field(name="判定", value=f["r"], inline=False)
    embed.add_field(name="物資", value=f["i"], inline=True)
    embed.set_footer(text=f["d"])
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="meigen", description="歴史的金言を表示する")
async def meigen(interaction: discord.Interaction):
    quote = random.choice(QUOTES_ARCHIVE)
    embed = discord.Embed(title="📜 歴史的記録アーカイブ", color=THEME_COLOR)
    embed.add_field(name="格言", value=f"```\n{quote['text']}\n```", inline=False)
    embed.add_field(name="発言者", value=f"**{quote['author']}** ({quote['faction']})")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="ranking", description="貢献度ランキングを表示する")
async def ranking(interaction: discord.Interaction):
    sorted_users = sorted(bot.user_data.items(), key=lambda x: x[1]["xp"], reverse=True)[:10]
    embed = discord.Embed(title="☭ 貢献度ランキング", color=THEME_COLOR)
    lines = [f"#{i+1} <@{u_id}>: {d['xp']} XP" for i, (u_id, d) in enumerate(sorted_users)]
    embed.description = "\n".join(lines) if lines else "記録なし"
    await interaction.response.send_message(embed=embed)

# ===== 時報 =====
@tasks.loop(seconds=60)
async def time_signal():
    now = datetime.now(JST)
    if now.minute == 0 and bot.last_signal_hour != now.hour:
        bot.last_signal_hour = now.hour
        for guild in bot.guilds:
            if guild.system_channel:
                try: await guild.system_channel.send(f"⏰ **定時放送**: {now.hour:02d}:00")
                except: pass

bot.run(TOKEN)
