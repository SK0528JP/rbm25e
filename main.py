import os
import asyncio
import random
from datetime import datetime, timezone, timedelta

import discord
from discord.ext import commands, tasks
from discord import app_commands

# ===== 基本設定 =====
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

# インテント設定（メッセージ内容の検閲許可）
intents = discord.Intents.default()
intents.guilds = True
intents.messages = True
intents.message_content = True

# タイムゾーン（JST）
JST = timezone(timedelta(hours=9))

# テーマカラー（ソビエト・レッド）
THEME_COLOR = 0xCC0000 

# ===== Botクラス定義 ===== 
class SovietBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)
        self.last_signal_hour = -1 # 定時報告の重複防止用

    async def setup_hook(self):
        try:
            await self.tree.sync()
            print("--- 指令システムの同期完了 (Slash commands synced) ---")
        except Exception as e:
            print(f"同期失敗、技術局に報告せよ: {e}")

bot = SovietBot()

# ===== 起動イベント =====
@bot.event
async def on_ready():
    # 状態表示: 「第5カ年計画を遂行中」
    await bot.change_presence(
        status=discord.Status.online,
        activity=discord.Activity(
            type=discord.ActivityType.playing, 
            name="☭ 第5カ年計画"
        )
    )
    print(f"同志 {bot.user} が接続しました (ID: {bot.user.id})")
    
    # 定時連絡網の稼働確認
    if not time_signal.is_running():
        time_signal.start()

# ===== /ping (通信確認) =====
@bot.tree.command(name="ping", description="モスクワ中央局との通信遅延を確認する")
async def ping(interaction: discord.Interaction):
    latency = round(bot.latency * 1000)
    
    embed = discord.Embed(title="☭ 通信状況報告", color=THEME_COLOR)
    embed.add_field(name="通信状態", value="良好", inline=True)
    embed.add_field(name="応答速度", value=f"**{latency}ms**", inline=True)
    embed.set_footer(text="技術局による監視中")

    await interaction.response.send_message(embed=embed, ephemeral=True)

# ===== /omikuji (本日の配給) =====
@bot.tree.command(name="omikuji", description="本日の運勢（配給物資）を受け取る")
async def omikuji(interaction: discord.Interaction):
    # 運勢の定義
    fortunes = [
        {"result": "労働英雄級 (大吉)", "item": "特級ウォッカと黒パン", "desc": "党は同志の多大なる貢献を称賛している！"},
        {"result": "模範的労働者 (中吉)", "item": "追加のジャガイモ配給", "desc": "ノルマ達成おめでとう。明日も励むように。"},
        {"result": "一般的市民 (小吉)", "item": "ビーツのスープ", "desc": "平穏こそが最大の幸福である。列に並べ。"},
        {"result": "要注意人物 (末吉)", "item": "塩のみ", "desc": "生産性が低下している。自己批判が必要だ。"},
        {"result": "シベリア送り (凶)", "item": "片道切符", "desc": "反革命的な態度が見受けられる。再教育が必要だ。"}
    ]
    
    # ランダム選出
    fortune = random.choice(fortunes)
    
    embed = discord.Embed(title="☭ 本日の配給結果", description=f"同志 {interaction.user.mention} への通達", color=THEME_COLOR)
    embed.add_field(name="階級判定", value=f"**{fortune['result']}**", inline=False)
    embed.add_field(name="支給物資", value=fortune['item'], inline=True)
    embed.add_field(name="党からのコメント", value=fortune['desc'], inline=False)
    
    await interaction.response.send_message(embed=embed)

# ===== じゃんけん (戦略的決着) =====
class JankenView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    async def play(self, interaction: discord.Interaction, user_hand: str):
        # BOTの手を決定
        bot_hand = random.choice(["グー", "チョキ", "パー"])
        hands_emoji = {"グー": "✊", "チョキ": "✌️", "パー": "✋"}
        
        # 勝敗判定
        if user_hand == bot_hand:
            result_text = "引き分け"
            msg = "両者譲らず。交渉は継続される。"
        elif (
            (user_hand == "グー" and bot_hand == "チョキ") or
            (user_hand == "チョキ" and bot_hand == "パー") or
            (user_hand == "パー" and bot_hand == "グー")
        ):
            result_text = "勝利"
            msg = "お見事です、同志！ 人民の勝利だ！"
        else:
            result_text = "敗北"
            msg = "資本主義的な軟弱さが露見したな。出直したまえ。"

        embed = discord.Embed(title="☭ 戦略的決着の結果", color=THEME_COLOR)
        embed.add_field(name="同志の手", value=f"{hands_emoji[user_hand]} {user_hand}", inline=True)
        embed.add_field(name="国家の手", value=f"{hands_emoji[bot_hand]} {bot_hand}", inline=True)
        embed.add_field(name="判定", value=f"**{result_text}**", inline=False)
        embed.set_footer(text=msg)

        await interaction.response.send_message(embed=embed)

    @discord.ui.button(label="強行突破 (グー)", style=discord.ButtonStyle.danger, emoji="✊")
    async def rock(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.play(interaction, "グー")
 
    @discord.ui.button(label="分断工作 (チョキ)", style=discord.ButtonStyle.danger, emoji="✌️")
    async def scissors(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.play(interaction, "チョキ")

    @discord.ui.button(label="包囲作戦 (パー)", style=discord.ButtonStyle.danger, emoji="✋")
    async def paper(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.play(interaction, "パー")

@bot.tree.command(name="janken", description="国家との戦略的決着（じゃんけん）を行う")
async def janken(interaction: discord.Interaction):
    embed = discord.Embed(
        title="☭ 戦略的選択",
        description="同志よ、次の一手を選択せよ。\n敗北は許されない。",
        color=THEME_COLOR
    )
    await interaction.response.send_message(embed=embed, view=JankenView())

# ===== 定時連絡（時報） =====
@tasks.loop(seconds=60)
async def time_signal():
    now_jst = datetime.now(JST)
    
    if now_jst.minute == 0:
        if bot.last_signal_hour != now_jst.hour:
            await broadcast_signal(now_jst.hour)
            bot.last_signal_hour = now_jst.hour

async def broadcast_signal(hour: int):
    embed = discord.Embed(title="☭ 定時放送", description=f"親愛なる同志諸君、**{hour:02d}:00** となった。", color=THEME_COLOR)
    
    if hour == 0:
        embed.add_field(name="指令", value="日付が変わった。明日も生産ノルマ達成のために休息せよ。", inline=False)
    elif hour == 9:
        embed.add_field(name="指令", value="労働開始時刻だ。栄光のために働け！", inline=False)
    elif hour == 12:
        embed.add_field(name="指令", value="配給の時間だ。列を乱すな。", inline=False)
    else:
        embed.add_field(name="状態", value="現在は平常通り稼働中である。", inline=False)

    for guild in bot.guilds:
        channel = guild.system_channel
        if channel:
            try:
                await channel.send(embed=embed)
            except Exception as e:
                print(f"放送失敗 ({guild.name}): {e}")

# ===== 起動プロセス =====
bot.run(TOKEN)
