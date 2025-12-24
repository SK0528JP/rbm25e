import os
import random
import json
import threading
from datetime import datetime, timezone, timedelta
from typing import Optional

import discord
from discord.ext import commands
from discord import app_commands

# ===== 基本設定 =====
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

THEME_COLOR = 0xCC0000 
DATA_FILE = "soviet_data.json"

# 書き込み競合を防ぐためのロックオブジェクト
data_lock = threading.Lock()

# ===== 歴史的アーカイブ =====
QUOTES_ARCHIVE = [
    {"text": "学習し、学習し、そして学習することだ。", "author": "ウラジーミル・レーニン"},
    {"text": "一人の死は悲劇だが、数百万人の死は統計上の数字に過ぎない。", "author": "ヨシフ・スターリン"},
    {"text": "地球は青かった。", "author": "ユーリ・ガガーリン"},
    {"text": "汗を流せば流すほど、血を流さずに済む。", "author": "エルヴィン・ロンメル"},
    {"text": "信頼せよ、だが検証せよ。", "author": "ロシアのことわざ"}
]

# ===== Botクラス ===== 
class SovietBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!", 
            intents=intents,
            status=discord.Status.idle,
            activity=discord.Activity(type=discord.ActivityType.playing, name="🎵 労働中")
        )
        self.user_data = {}

    async def setup_hook(self):
        self.load_data()
        try:
            await self.tree.sync()
            print("--- 経済改革版システム（排他制御） 同期完了 ---")
        except Exception as e:
            print(f"同期失敗: {e}")

    def load_data(self):
        """スレッドセーフなデータ読み込み"""
        with data_lock:
            if os.path.exists(DATA_FILE):
                try:
                    with open(DATA_FILE, "r", encoding="utf-8") as f:
                        self.user_data = json.load(f)
                except: self.user_data = {}
            else: self.user_data = {}

    def save_data(self):
        """スレッドセーフなデータ保存"""
        with data_lock:
            try:
                with open(DATA_FILE, "w", encoding="utf-8") as f:
                    json.dump(self.user_data, f, ensure_ascii=False, indent=4)
            except Exception as e:
                print(f"セーブエラー: {e}")

    def get_user(self, user_id: str):
        uid = str(user_id)
        if uid not in self.user_data:
            self.user_data[uid] = {"xp": 0, "money": 0, "last_msg": 0}
        return self.user_data[uid]

    async def add_xp(self, user_id: str):
        now = datetime.now().timestamp()
        uid = str(user_id)
        
        # ロードして最新状態を確保
        self.load_data()
        
        u = self.get_user(uid)
        # クールダウン（連投による不正取得防止 3秒）
        if now - u.get("last_msg", 0) < 3:
            return

        # 要請通り、1メッセージにつき 2pt 固定
        u["xp"] += 2
        u["last_msg"] = now
        
        self.save_data()

bot = SovietBot()

# ===== 経済コマンド =====

@bot.tree.command(name="exchange", description="保有XPを資金($)に換金する")
@app_commands.describe(amount="換金するXP量")
async def exchange(interaction: discord.Interaction, amount: int):
    bot.load_data()
    uid = str(interaction.user.id)
    u = bot.get_user(uid)

    if amount <= 0:
        return await interaction.response.send_message("❌ 数値が不正だ。", ephemeral=True)
    if u["xp"] < amount:
        return await interaction.response.send_message(f"❌ XP不足。保有: {u['xp']}", ephemeral=True)

    u["xp"] -= amount
    u["money"] += amount
    bot.save_data()
    
    embed = discord.Embed(title="☭ 国家銀行・換金証明書", color=0x00FF00)
    embed.description = f"同志 {interaction.user.mention}\n**-{amount} XP** ➔ **+${amount}**"
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="pay", description="送金する")
async def pay(interaction: discord.Interaction, receiver: discord.Member, amount: int):
    if receiver.bot or amount <= 0:
        return await interaction.response.send_message("❌ 無効な操作だ。", ephemeral=True)

    bot.load_data()
    s = bot.get_user(str(interaction.user.id))
    r = bot.get_user(str(receiver.id))

    if s["money"] < amount:
        return await interaction.response.send_message("❌ 資金不足。", ephemeral=True)

    s["money"] -= amount
    r["money"] += amount
    bot.save_data()
    await interaction.response.send_message(f"💰 {interaction.user.mention} ➔ {receiver.mention} へ **${amount}** 送金した。")

@bot.tree.command(name="money_ranking", description="保有資金ランキング")
async def money_ranking(interaction: discord.Interaction):
    bot.load_data()
    # 数値変換して安定ソート
    sorted_users = sorted(bot.user_data.items(), key=lambda x: (int(x[1].get("money", 0)), x[0]), reverse=True)[:10]
    embed = discord.Embed(title="☭ 国家富裕層ランキング", color=0xFFD700)
    text = "\n".join([f"💰 <@{u_id}>: **${d.get('money', 0)}**" for u_id, d in sorted_users])
    embed.description = text or "記録なし"
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="ranking", description="貢献度(XP)ランキング")
async def ranking(interaction: discord.Interaction):
    bot.load_data()
    sorted_users = sorted(bot.user_data.items(), key=lambda x: (int(x[1].get("xp", 0)), x[0]), reverse=True)[:10]
    embed = discord.Embed(title="☭ 労働英雄ランキング", color=THEME_COLOR)
    text = "\n".join([f"🥇 <@{u_id}>: **{d.get('xp', 0)}** pt" for u_id, d in sorted_users])
    embed.description = text or "記録なし"
    u = bot.get_user(str(interaction.user.id))
    embed.set_footer(text=f"あなたの貢献度: {u['xp']} pt")
    await interaction.response.send_message(embed=embed)

# ===== 娯楽・声明コマンド =====

@bot.tree.command(name="roulette")
async def roulette(it, options: str):
    cl = options.replace("　", " ").split()
    if len(cl) < 2: return await it.response.send_message("❌ 2つ以上必要だ。", ephemeral=True)
    await it.response.send_message(embed=discord.Embed(title="☭ 国家意思決定", description=f"🏆 **{random.choice(cl)}**", color=THEME_COLOR))

@bot.tree.command(name="comment")
async def comment(it, content: str, image: Optional[discord.Attachment] = None, use_embed: bool = False):
    content = content.replace("\\n", "\n")
    if use_embed:
        e = discord.Embed(description=content, color=THEME_COLOR)
        e.set_author(name="☭ 国家公式声明", icon_url=bot.user.display_avatar.url)
        if image: e.set_image(url=image.url)
        await it.channel.send(embed=e)
    else:
        f = await image.to_file() if image else None
        await it.channel.send(content=content, file=f)
    await it.response.send_message("配信完了。", ephemeral=True)

@bot.tree.command(name="janken")
async def janken(it):
    class JV(discord.ui.View):
        def __init__(self): super().__init__(timeout=60)
        async def p(self, it, uh):
            bh = random.choice(["✊", "✌️", "✋"])
            msg = "引き分け" if uh==bh else "勝利" if (uh=="✊" and bh=="✌️") or (uh=="✌️" and bh=="✋") or (uh=="✋" and bh=="✊") else "敗北"
            e = discord.Embed(title="☭ 決着", description=f"同志 {uh} vs 国家 {bh}\n判定: **{msg}**", color=THEME_COLOR)
            for c in self.children: c.disabled = True
            await it.response.edit_message(view=self); await it.followup.send(embed=e)
        @discord.ui.button(label="✊")
        async def r(self, it, b): await self.p(it, "✊")
        @discord.ui.button(label="✌️")
        async def s(self, it, b): await self.p(it, "✌️")
        @discord.ui.button(label="✋")
        async def w(self, it, b): await self.p(it, "✋")
    await it.response.send_message(embed=discord.Embed(title="☭ 戦略的決着", color=THEME_COLOR), view=JV())

@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.idle, activity=discord.Activity(type=discord.ActivityType.playing, name="🎵 労働中"))
    print(f"同志 {bot.user} 稼働。排他制御を適用済み。")

@bot.event
async def on_message(message):
    if message.author.bot: return
    await bot.add_xp(str(message.author.id))
    await bot.process_commands(message)

bot.run(TOKEN)
