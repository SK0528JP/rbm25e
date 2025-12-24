import os
import asyncio
import random
import json
from datetime import datetime
from typing import Optional

import discord
from discord.ext import commands
from discord import app_commands

# ===== 基本設定 =====
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
DATA_FILE = "soviet_ledger.json"
THEME_COLOR = 0xCC0000

# ===== 歴史的アーカイブ（名言） =====
QUOTES_ARCHIVE = [
    {"text": "学習し、学習し、そして学習することだ。", "author": "ウラジーミル・レーニン"},
    {"text": "一人の死は悲劇だが、数百万人の死は統計上の数字に過ぎない。", "author": "ヨシフ・スターリン"},
    {"text": "地球は青かった。", "author": "ユーリ・ガガーリン"},
    {"text": "信頼せよ、だが検証せよ。", "author": "ロシアのことわざ"}
]

# ===== 国家元帳（データ一元管理クラス） =====
class SovietLedger:
    def __init__(self):
        self.data = {}
        self.lock = asyncio.Lock()
        self._load()

    def _load(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    self.data = json.load(f)
            except: self.data = {}
        else: self.data = {}

    def _save(self):
        try:
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"元帳保存失敗: {e}")

    def get_user(self, user_id: str):
        uid = str(user_id)
        if uid not in self.data:
            self.data[uid] = {"xp": 0, "money": 0, "last": 0}
        u = self.data[uid]
        u["xp"] = int(u.get("xp", 0))
        u["money"] = int(u.get("money", 0))
        u["last"] = float(u.get("last", 0))
        return u

    def get_rank(self, user_id: str, key: str):
        """特定のキーにおけるユーザーの現在の順位を取得"""
        sorted_list = sorted(self.data.items(), key=lambda x: (int(x[1].get(key, 0)), x[0]), reverse=True)
        for i, (uid, _) in enumerate(sorted_list):
            if uid == str(user_id):
                return i + 1
        return "圏外"

    async def add_xp(self, user_id: str):
        uid = str(user_id)
        now = datetime.now().timestamp()
        async with self.lock:
            u = self.get_user(uid)
            if now - u["last"] < 3: return
            u["xp"] += 2
            u["last"] = now
            self._save()

    async def exchange(self, user_id: str, amount: int):
        uid = str(user_id)
        async with self.lock:
            u = self.get_user(uid)
            if u["xp"] < amount: return False, u["xp"]
            u["xp"] -= amount
            u["money"] += amount
            self._save()
            return True, u["money"]

    async def transfer(self, sender_id: str, receiver_id: str, amount: int):
        s_uid, r_uid = str(sender_id), str(receiver_id)
        if s_uid == r_uid: return False, "自己送金不可"
        async with self.lock:
            s = self.get_user(s_uid)
            r = self.get_user(r_uid)
            if s["money"] < amount: return False, "資金不足"
            s["money"] -= amount
            r["money"] += amount
            self._save()
            return True, s["money"]

ledger = SovietLedger()

# ===== UIコンポーネント: じゃんけん View =====
class JankenView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    async def handle_play(self, interaction: discord.Interaction, user_hand: str):
        bot_hand = random.choice(["✊", "✌️", "✋"])
        if user_hand == bot_hand: res, col = "引き分け", 0x808080
        elif (user_hand=="✊" and bot_hand=="✌️") or (user_hand=="✌️" and bot_hand=="✋") or (user_hand=="✋" and bot_hand=="✊"):
            res, col = "勝利", 0x00FF00
        else: res, col = "敗北", 0x000000
        embed = discord.Embed(title="☭ 戦略的決着報告書", color=col)
        embed.description = f"同志 {user_hand} vs 国家 {bot_hand}\n判定: **{res}**"
        for child in self.children: child.disabled = True
        await interaction.response.edit_message(view=self)
        await interaction.followup.send(embed=embed)

    @discord.ui.button(label="✊", style=discord.ButtonStyle.danger)
    async def rock(self, it, b): await self.handle_play(it, "✊")
    @discord.ui.button(label="✌️", style=discord.ButtonStyle.danger)
    async def sciss(self, it, b): await self.handle_play(it, "✌️")
    @discord.ui.button(label="✋", style=discord.ButtonStyle.danger)
    async def paper(self, it, b): await self.handle_play(it, "✋")

# ===== Botクラス定義 =====
class SovietBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=discord.Intents.all(),
            status=discord.Status.idle,
            activity=discord.Activity(type=discord.ActivityType.playing, name="🎵 労働中")
        )
    async def setup_hook(self):
        await self.tree.sync()

bot = SovietBot()

# ===== 指令コマンド群 =====

@bot.tree.command(name="user", description="指定した同志の全記録を照会する")
@app_commands.describe(target="照会する同志")
async def user_info(it: discord.Interaction, target: Optional[discord.Member] = None):
    target = target or it.user
    u = ledger.get_user(target.id)
    xp_rank = ledger.get_rank(target.id, "xp")
    money_rank = ledger.get_rank(target.id, "money")
    
    # 最終活動時刻のフォーマット
    last_act = datetime.fromtimestamp(u["last"]).strftime('%Y/%m/%d %H:%M:%S') if u["last"] > 0 else "記録なし"
    join_date = target.joined_at.strftime('%Y/%m/%d') if target.joined_at else "不明"

    embed = discord.Embed(title=f"☭ 国家アーカイブ：{target.display_name} 照会結果", color=THEME_COLOR)
    embed.set_thumbnail(url=target.display_avatar.url)
    
    embed.add_field(name="🎖️ 貢献度 (XP)", value=f"**{u['xp']}** pt (第 {xp_rank} 位)", inline=True)
    embed.add_field(name="💰 保有資金 ($)", value=f"**${u['money']}** (第 {money_rank} 位)", inline=True)
    embed.add_field(name="📅 サーバー入隊日", value=join_date, inline=True)
    embed.add_field(name="🕒 最終労働時刻", value=last_act, inline=False)
    
    embed.set_footer(text=f"照会ID: {target.id}")
    await it.response.send_message(embed=embed)

@bot.tree.command(name="status", description="自身の労働手帳を確認する")
async def status(it: discord.Interaction):
    u = ledger.get_user(it.user.id)
    embed = discord.Embed(title=f"☭ {it.user.display_name} の労働手帳", color=THEME_COLOR)
    embed.add_field(name="貢献度(XP)", value=f"{u['xp']} pt", inline=True)
    embed.add_field(name="保有資金($)", value=f"${u['money']}", inline=True)
    embed.set_thumbnail(url=it.user.display_avatar.url)
    await it.response.send_message(embed=embed)

@bot.tree.command(name="ranking", description="貢献度ランキングを表示")
async def ranking(it: discord.Interaction):
    top = sorted(ledger.data.items(), key=lambda x: (int(x[1].get('xp',0)), x[0]), reverse=True)[:10]
    desc = "\n".join([f"🥇 <@{uid}>: **{d['xp']}** pt" for uid, d in top])
    await it.response.send_message(embed=discord.Embed(title="☭ 労働英雄ランキング", description=desc or "記録なし", color=THEME_COLOR))

@bot.tree.command(name="money_ranking", description="保有資金ランキングを表示")
async def money_ranking(it: discord.Interaction):
    top = sorted(ledger.data.items(), key=lambda x: (int(x[1].get('money',0)), x[0]), reverse=True)[:10]
    desc = "\n".join([f"💰 <@{uid}>: **${d['money']}**" for uid, d in top])
    await it.response.send_message(embed=discord.Embed(title="☭ 国家富裕層ランキング", description=desc or "記録なし", color=0xFFD700))

@bot.tree.command(name="exchange", description="XPを資金に換金")
async def exchange(it: discord.Interaction, amount: int):
    if amount <= 0: return await it.response.send_message("❌ 不正な数値だ。", ephemeral=True)
    success, val = await ledger.exchange(it.user.id, amount)
    if success: await it.response.send_message(f"✅ 換金成功。現在の所持金: **${val}**")
    else: await it.response.send_message(f"❌ XP不足（現在: {val} XP）", ephemeral=True)

@bot.tree.command(name="pay", description="資金を送金")
async def pay(it: discord.Interaction, receiver: discord.Member, amount: int):
    success, res = await ledger.transfer(it.user.id, receiver.id, amount)
    if success: await it.response.send_message(f"💰 {it.user.mention} ➔ {receiver.mention} へ **${amount}** 送金完了。")
    else: await it.response.send_message(f"❌ {res}", ephemeral=True)

@bot.tree.command(name="roulette")
async def roulette(it: discord.Interaction, options: str):
    cl = options.replace("　", " ").split()
    if len(cl) < 2: return await it.response.send_message("❌ 2つ以上必要だ。", ephemeral=True)
    await it.response.send_message(embed=discord.Embed(title="☭ 国家意思決定", description=f"🏆 **{random.choice(cl)}**", color=THEME_COLOR))

@bot.tree.command(name="omikuji")
async def omikuji(it: discord.Interaction):
    f = random.choice([
        {"r": "労働英雄(大吉)", "i": "特級ウォッカ", "c": 0xFFD700},
        {"r": "模範的市民(中吉)", "i": "追加のジャガイモ", "c": 0xCC0000},
        {"r": "一般的労働者(小吉)", "i": "スープ", "c": 0xCC0000},
        {"r": "要注意人物(末吉)", "i": "パン", "c": 0x8B4513},
        {"r": "シベリア(凶)", "i": "片道切符", "c": 0x0000FF}
    ])
    e = discord.Embed(title="☭ 配給物資通達書", color=f["c"])
    e.add_field(name="判定", value=f["r"], inline=True)
    e.add_field(name="支給品", value=f["i"], inline=True)
    await it.response.send_message(embed=e)

@bot.tree.command(name="janken")
async def janken(it: discord.Interaction):
    await it.response.send_message(embed=discord.Embed(title="☭ 戦略的決着", color=THEME_COLOR), view=JankenView())

@bot.tree.command(name="meigen")
async def meigen(it: discord.Interaction):
    q = random.choice(QUOTES_ARCHIVE)
    await it.response.send_message(embed=discord.Embed(title="📜 引用", description=f"```\n{q['text']}\n```", color=THEME_COLOR).set_footer(text=q['author']))

@bot.tree.command(name="comment")
async def comment(it: discord.Interaction, content: str, image: Optional[discord.Attachment] = None, use_embed: bool = False):
    msg = content.replace("\\n", "\n")
    if use_embed:
        e = discord.Embed(description=msg, color=THEME_COLOR).set_author(name="☭ 公式声明", icon_url=bot.user.display_avatar.url)
        if image: e.set_image(url=image.url)
        await it.channel.send(embed=e)
    else:
        f = await image.to_file() if image else None
        await it.channel.send(content=msg, file=f)
    await it.response.send_message("完了。", ephemeral=True)

# ===== イベント =====
@bot.event
async def on_message(message):
    if message.author.bot: return
    await ledger.add_xp(message.author.id)
    await bot.process_commands(message)

@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.idle, activity=discord.Activity(type=discord.ActivityType.playing, name="🎵 労働中"))
    print(f"同志 {bot.user}、全機能復元・拡張完了。")

bot.run(TOKEN)
