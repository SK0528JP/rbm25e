import os
import asyncio
import random
import json
import requests
from datetime import datetime, timedelta, timezone
from typing import Optional

import discord
from discord.ext import commands
from discord import app_commands

# ===== 基本設定 =====
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GITHUB_TOKEN = os.getenv("MY_GITHUB_TOKEN")
GIST_ID = os.getenv("GIST_ID")
THEME_COLOR = 0xCC0000
JST = timezone(timedelta(hours=9))

# ===== 国家元帳（Gist API 永続化ストレージ） =====
class SovietLedger:
    def __init__(self):
        self.data = {}
        self.lock = asyncio.Lock()
        self._load()

    def _load(self):
        if not GITHUB_TOKEN or not GIST_ID:
            print("⚠️ 警告: 環境変数が未設定です。一時モードで動作します。")
            return
        try:
            headers = {"Authorization": f"token {GITHUB_TOKEN}"}
            res = requests.get(f"https://api.github.com/gists/{GIST_ID}", headers=headers)
            if res.status_code == 200:
                files = res.json().get("files", {})
                content = files.get("soviet_ledger.json", {}).get("content", "{}")
                self.data = json.loads(content)
                print("✅ 国家元帳を Gist からロードしました。")
            else:
                print(f"❌ ロード失敗: {res.status_code}")
        except Exception as e:
            print(f"❌ ロードエラー: {e}")

    def _save(self):
        if not GITHUB_TOKEN or not GIST_ID: return
        try:
            headers = {"Authorization": f"token {GITHUB_TOKEN}"}
            payload = {"files": {"soviet_ledger.json": {"content": json.dumps(self.data, ensure_ascii=False, indent=4)}}}
            res = requests.patch(f"https://api.github.com/gists/{GIST_ID}", headers=headers, json=payload)
            if res.status_code == 200:
                print("💾 国家元帳を Gist へ同期しました。")
        except Exception as e:
            print(f"❌ 同期エラー: {e}")

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
        sorted_list = sorted(self.data.items(), key=lambda x: (int(x[1].get(key, 0)), x[0]), reverse=True)
        for i, (uid, _) in enumerate(sorted_list):
            if uid == str(user_id): return i + 1
        return "圏外"

    async def add_xp(self, user_id: str):
        uid = str(user_id)
        now = datetime.now(timezone.utc).timestamp()
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

# ===== ボット定義 =====
class SovietBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all(), status=discord.Status.idle,
                         activity=discord.Activity(type=discord.ActivityType.playing, name="🎵 労働中"))
    async def setup_hook(self):
        await self.tree.sync()

bot = SovietBot()

# ===== 指令コマンド群 =====
@bot.tree.command(name="user", description="同志の全記録を照会")
async def user_info(it: discord.Interaction, target: Optional[discord.Member] = None):
    t = target or it.user
    u = ledger.get_user(t.id)
    xp_rank, m_rank = ledger.get_rank(t.id, "xp"), ledger.get_rank(t.id, "money")
    last_act = datetime.fromtimestamp(u["last"], tz=timezone.utc).astimezone(JST).strftime('%Y/%m/%d %H:%M:%S') if u["last"] > 0 else "記録なし"
    join_date = t.joined_at.astimezone(JST).strftime('%Y/%m/%d') if t.joined_at else "不明"
    e = discord.Embed(title=f"☭ 国家アーカイブ：{t.display_name}", color=THEME_COLOR)
    e.set_thumbnail(url=t.display_avatar.url)
    e.add_field(name="🎖️ XP", value=f"**{u['xp']}** (第{xp_rank}位)", inline=True)
    e.add_field(name="💰 資金", value=f"**${u['money']}** (第{m_rank}位)", inline=True)
    e.add_field(name="📅 入隊日", value=join_date, inline=True)
    e.add_field(name="🕒 最終労働(JST)", value=f"`{last_act}`", inline=False)
    await it.response.send_message(embed=e)

@bot.tree.command(name="status", description="自身の労働手帳")
async def status(it: discord.Interaction):
    u = ledger.get_user(it.user.id)
    e = discord.Embed(title=f"☭ {it.user.display_name} の労働手帳", color=THEME_COLOR)
    e.add_field(name="XP", value=f"{u['xp']} pt", inline=True)
    e.add_field(name="資金", value=f"${u['money']}", inline=True)
    e.set_thumbnail(url=it.user.display_avatar.url)
    await it.response.send_message(embed=e)

@bot.tree.command(name="ranking", description="XP順位")
async def ranking(it: discord.Interaction):
    top = sorted(ledger.data.items(), key=lambda x: (int(x[1].get('xp',0)), x[0]), reverse=True)[:10]
    desc = "\n".join([f"🥇 <@{uid}>: **{d['xp']}** pt" for uid, d in top])
    await it.response.send_message(embed=discord.Embed(title="☭ 労働英雄", description=desc or "無", color=THEME_COLOR))

@bot.tree.command(name="money_ranking", description="資金順位")
async def money_ranking(it: discord.Interaction):
    top = sorted(ledger.data.items(), key=lambda x: (int(x[1].get('money',0)), x[0]), reverse=True)[:10]
    desc = "\n".join([f"💰 <@{uid}>: **${d['money']}**" for uid, d in top])
    await it.response.send_message(embed=discord.Embed(title="☭ 国家富裕層", description=desc or "無", color=0xFFD700))

@bot.tree.command(name="exchange", description="換金")
async def exchange(it: discord.Interaction, amount: int):
    success, val = await ledger.exchange(it.user.id, amount)
    await it.response.send_message(f"✅ 成功。所持金: ${val}" if success else "❌ XP不足", ephemeral=not success)

@bot.tree.command(name="pay", description="送金")
async def pay(it: discord.Interaction, receiver: discord.Member, amount: int):
    s, r = await ledger.transfer(it.user.id, receiver.id, amount)
    await it.response.send_message(f"💰 {receiver.mention}へ ${amount} 送金。" if s else f"❌ {r}", ephemeral=not s)

@bot.tree.command(name="ping", description="遅延計測")
async def ping(it: discord.Interaction):
    await it.response.send_message(f"📡 応答: {round(bot.latency * 1000)}ms", ephemeral=True)

@bot.tree.command(name="omikuji", description="配給")
async def omikuji(it: discord.Interaction):
    f = random.choice([{"r": "大吉", "i": "特級ウォッカ"}, {"r": "中吉", "i": "追加ジャガイモ"}, {"r": "小吉", "i": "スープ"}, {"r": "末吉", "i": "パン"}, {"r": "凶", "i": "シベリア送り"}])
    await it.response.send_message(embed=discord.Embed(title="☭ 配給物資", description=f"判定: {f['r']}\n支給: {f['i']}", color=THEME_COLOR))

@bot.tree.command(name="roulette", description="決定")
async def roulette(it: discord.Interaction, options: str):
    cl = options.replace("　", " ").split()
    await it.response.send_message(f"🏆 決定：**{random.choice(cl)}**" if len(cl)>1 else "❌ 選択肢不足")

@bot.tree.command(name="meigen", description="金言")
async def meigen(it: discord.Interaction):
    q = random.choice([{"t": "学習せよ。", "a": "レーニン"}, {"t": "地球は青かった。", "a": "ガガーリン"}])
    await it.response.send_message(embed=discord.Embed(title="📜 引用", description=f"```\n{q['t']}\n```", color=THEME_COLOR).set_footer(text=q['a']))

@bot.tree.command(name="comment", description="声明")
async def comment(it: discord.Interaction, content: str, image: Optional[discord.Attachment] = None, use_embed: bool = False):
    msg = content.replace("\\n", "\n")
    if use_embed:
        e = discord.Embed(description=msg, color=THEME_COLOR).set_author(name="☭ 公式声明")
        if image: e.set_image(url=image.url)
        await it.channel.send(embed=e)
    else:
        f = await image.to_file() if image else None
        await it.channel.send(content=msg, file=f)
    await it.response.send_message("配信完了", ephemeral=True)

@bot.event
async def on_message(message):
    if message.author.bot: return
    await ledger.add_xp(message.author.id)
    await bot.process_commands(message)

@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.idle, activity=discord.Activity(type=discord.ActivityType.playing, name="🎵 労働中"))
    print(f"同志 {bot.user}、永続ストレージ同期完了。")

bot.run(TOKEN)

