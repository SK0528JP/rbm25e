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

# インテント設定
intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.message_content = True

# タイムゾーン & テーマカラー
JST = timezone(timedelta(hours=9))
THEME_COLOR = 0xCC0000 

# データ保存用ファイル名
DATA_FILE = "soviet_data.json"

# ===== 名言リスト (アーカイブ) =====
# フォーマット: {"text": "名言本文", "author": "発言者", "faction": "勢力"}
QUOTES_ARCHIVE = [
    # ソビエト連邦
    {"text": "学習し、学習し、そして学習することだ。", "author": "ウラジーミル・レーニン", "faction": "ソビエト連邦"},
    {"text": "一人の死は悲劇だが、数百万人の死は統計上の数字に過ぎない。", "author": "ヨシフ・スターリン", "faction": "ソビエト連邦"},
    {"text": "幹部がすべてを決定する。", "author": "ヨシフ・スターリン", "faction": "ソビエト連邦"},
    {"text": "地球は青かった。", "author": "ユーリ・ガガーリン", "faction": "ソビエト連邦"},
    {"text": "信頼せよ、だが検証せよ。", "author": "ロシアのことわざ", "faction": "ソビエト連邦"},
    {"text": "不可能なことなどない。不可能なのは、我々がそう思い込んでいるだけだ。", "author": "ミハイル・トゥハチェフスキー", "faction": "ソビエト連邦"},

    # ドイツ（軍事・哲学・戦略）
    {"text": "汗を流せば流すほど、血を流さずに済む。", "author": "エルヴィン・ロンメル", "faction": "ドイツ"},
    {"text": "計画がその通りに進むことなど、実戦では稀である。", "author": "ヘルムート・フォン・モルトケ", "faction": "ドイツ"},
    {"text": "戦いにおいては、精神的な要素と物理的な要素の比率は３対１である。", "author": "ナポレオン（ドイツ軍事思想に影響）", "faction": "軍事格言"},
    {"text": "嘘も百回言えば真実となる。", "author": "プロパガンダの格言", "faction": "ドイツ"},
    {"text": "兵士諸君、君たちの栄光は、君たちの犠牲の中にある。", "author": "エーリッヒ・フォン・マンシュタイン", "faction": "ドイツ"},
    {"text": "危険な状況では、何もしないことが最大の誤りである。", "author": "ハインツ・グデーリアン", "faction": "ドイツ"},

    # スウェーデン王国
    {"text": "主は我が守りなり。", "author": "グスタフ2世アドルフ", "faction": "スウェーデン王国"},
    {"text": "私は私の兵士たちが何を食べるかを知るまでは食事をとらない。", "author": "カール12世", "faction": "スウェーデン王国"},
    {"text": "北方の獅子は眠らない。", "author": "伝承", "faction": "スウェーデン王国"},
    {"text": "平和なときにこそ、戦争の準備をせよ。", "author": "スウェーデン民間防衛読本", "faction": "スウェーデン王国"},
]

# ===== Botクラス ===== 
class SovietBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.last_signal_hour = -1 
        self.user_data = {} # ユーザーデータをメモリに保持

    async def setup_hook(self):
        self.load_data() # 起動時にデータを読み込む
        try:
            await self.tree.sync()
            print("--- 指令システムの同期完了 ---")
        except Exception as e:
            print(f"同期失敗: {e}")

    # --- データ保存・読込 ---
    def load_data(self):
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
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.user_data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"データ保存エラー: {e}")

    # --- 経験値加算ロジック ---
    async def add_xp(self, user_id: str):
        # データ構造: {"user_id": {"xp": 100, "last_msg": timestamp}}
        now = datetime.now().timestamp()
        
        if user_id not in self.user_data:
            self.user_data[user_id] = {"xp": 0, "last_msg": 0}
        
        # クールダウン（連投対策: 5秒に1回のみ加算）
        last_time = self.user_data[user_id].get("last_msg", 0)
        if now - last_time < 5:
            return

        # ランダムでXP付与 (10〜20)
        xp_gain = random.randint(10, 20)
        self.user_data[user_id]["xp"] += xp_gain
        self.user_data[user_id]["last_msg"] = now
        
        self.save_data()

bot = SovietBot()

# ===== イベント =====
@bot.event
async def on_ready():
    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Activity(type=discord.ActivityType.watching, name="同志の勤務態度")
    )
    print(f"同志 {bot.user} が接続しました。")
    if not time_signal.is_running():
        time_signal.start()

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # メッセージ送信で経験値を加算
    await bot.add_xp(str(message.author.id))

    # コマンド処理へ
    await bot.process_commands(message)

# ===== /ping =====
@bot.tree.command(name="ping", description="通信状況の確認")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    await interaction.response.send_message(f"通信良好。遅延: **{latency}ms**", ephemeral=True)

# ===== /meigen (歴史的名言) =====
@bot.tree.command(name="meigen", description="歴史的指導者や軍人たちの金言を表示する")
async def meigen(interaction: discord.Interaction):
    quote = random.choice(QUOTES_ARCHIVE)
    
    # 勢力によって色を変える演出（任意）
    color = THEME_COLOR # デフォルト赤
    if quote["faction"] == "ドイツ":
        color = 0x2C2F33 # ダークグレー
    elif quote["faction"] == "スウェーデン王国":
        color = 0x005293 # スウェーデンブルー

    embed = discord.Embed(title="📜 歴史的記録アーカイブ", color=color)
    embed.add_field(name="格言", value=f"```\n{quote['text']}\n```", inline=False)
    embed.add_field(name="発言者", value=f"**{quote['author']}**", inline=True)
    embed.add_field(name="所属", value=f"{quote['faction']}", inline=True)
    embed.set_footer(text="歴史から学び、生産に活かせ。")

    await interaction.response.send_message(embed=embed)

# ===== /ranking (貢献度ランキング) =====
@bot.tree.command(name="ranking", description="国家への貢献度（XP）ランキングを表示する")
async def ranking(interaction: discord.Interaction):
    # XPでソート
    sorted_users = sorted(
        bot.user_data.items(), 
        key=lambda item: item[1]["xp"], 
        reverse=True
    )
    
    # 上位10名を表示
    top_10 = sorted_users[:10]
    
    embed = discord.Embed(
        title="☭ スタハノフ運動 貢献度ランキング",
        description="最も勤勉な労働者（同志）たちを称える。",
        color=THEME_COLOR
    )

    text_list = []
    for rank, (user_id, data) in enumerate(top_10, 1):
        xp = data["xp"]
        
        # 順位に応じたメダル
        medal = "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"**#{rank}**"
        
        # ユーザー名の取得（キャッシュになければID表示）
        user = interaction.guild.get_member(int(user_id))
        user_name = user.display_name if user else f"不明な同志 ({user_id})"
        
        text_list.append(f"{medal} **{user_name}**: {xp} 貢献ポイント")

    if not text_list:
        embed.description = "まだ記録されたデータがない。"
    else:
        embed.add_field(name="上位の同志", value="\n".join(text_list), inline=False)
    
    # 自分の順位を表示
    my_xp = bot.user_data.get(str(interaction.user.id), {}).get("xp", 0)
    embed.set_footer(text=f"あなたの貢献度: {my_xp} ポイント")

    await interaction.response.send_message(embed=embed)

# ===== 時報 =====
@tasks.loop(seconds=60)
async def time_signal():
    now_jst = datetime.now(JST)
    if now_jst.minute == 0:
        if bot.last_signal_hour != now_jst.hour:
            await send_time_signal(now_jst.hour)
            bot.last_signal_hour = now_jst.hour

async def send_time_signal(hour: int):
    embed = discord.Embed(title="☭ 定時報告", description=f"現在時刻 **{hour:02d}:00**", color=THEME_COLOR)
    for guild in bot.guilds:
        channel = guild.system_channel
        if channel:
            try:
                await channel.send(embed=embed)
            except:
                pass

# ===== 起動 =====
bot.run(TOKEN)
