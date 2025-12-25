import os
import sys
import asyncio
import random
import json
import requests
import traceback
from datetime import datetime, timedelta, timezone
from typing import Optional

import discord
from discord.ext import commands
from discord import app_commands

# ==========================================
# ☭ CONFIGURATION (国家設定)
# ==========================================
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GITHUB_TOKEN = os.getenv("MY_GITHUB_TOKEN")
GIST_ID = os.getenv("GIST_ID")

# 色設定（ソビエト・レッド）
THEME_COLOR = 0xCC0000 
COLOR_SUCCESS = 0x00FF00
COLOR_WARNING = 0xFFA500
COLOR_DANGER = 0xFF0000
COLOR_GOLD = 0xFFD700
COLOR_BLACK = 0x000000

# 時刻設定（JST）
JST = timezone(timedelta(hours=9))

# 権限設定（管理者ロールID）
ADMIN_ROLE_ID = 1453336556961140866

# アーカイブファイル名
DATA_FILE_NAME = "soviet_ledger.json"

# ==========================================
# ☭ UTILITIES (補助機能)
# ==========================================

def is_developer():
    """管理者権限チェック"""
    async def predicate(it: discord.Interaction) -> bool:
        role = discord.utils.get(it.user.roles, id=ADMIN_ROLE_ID)
        if role:
            return True
        # 権限なし時の冷徹な拒絶
        embed = discord.Embed(description="❌ 貴公にはこの権限を行使する資格がない。", color=COLOR_BLACK)
        await it.response.send_message(embed=embed, ephemeral=True)
        return False
    return app_commands.check(predicate)

def create_embed(title: str, description: str = "", color: int = THEME_COLOR, thumbnail: str = None) -> discord.Embed:
    """統一Embed生成"""
    embed = discord.Embed(title=title, description=description, color=color)
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)
    return embed

# ==========================================
# ☭ DATA PERSISTENCE (Gist永続化)
# ==========================================

class SovietLedger:
    def __init__(self):
        self.data = {}
        self.lock = asyncio.Lock()
        self.is_connected = False
        self._load()

    def _load(self):
        if not GITHUB_TOKEN or not GIST_ID:
            print("⚠️ 警告: 永続化設定欠落。一時モードで動作。")
            self.is_connected = False
            return
        try:
            headers = {"Authorization": f"token {GITHUB_TOKEN}"}
            res = requests.get(f"https://api.github.com/gists/{GIST_ID}", headers=headers, timeout=10)
            if res.status_code == 200:
                content = res.json()["files"][DATA_FILE_NAME]["content"]
                self.data = json.loads(content)
                self.is_connected = True
                print("✅ 国家元帳ロード完了 (Gist)")
            else:
                print(f"❌ ロード失敗: {res.status_code}")
                self.is_connected = False
        except Exception:
            self.data = {}
            self.is_connected = False

    def _save(self):
        if not self.is_connected: return
        try:
            headers = {"Authorization": f"token {GITHUB_TOKEN}"}
            payload = {"files": {DATA_FILE_NAME: {"content": json.dumps(self.data, ensure_ascii=False, indent=4)}}}
            requests.patch(f"https://api.github.com/gists/{GIST_ID}", headers=headers, json=payload, timeout=5)
        except Exception as e:
            print(f"❌ 保存エラー: {e}")

    def get_user(self, user_id):
        uid = str(user_id)
        if uid not in self.data:
            self.data[uid] = {"xp": 0, "money": 0, "last": 0}
        return self.data[uid]

    def get_rank(self, user_id, key):
        sorted_list = sorted(self.data.items(), key=lambda x: (int(x[1].get(key, 0)), x[0]), reverse=True)
        for i, (uid, _) in enumerate(sorted_list):
            if uid == str(user_id): return i + 1
        return "圏外"

    async def add_xp(self, user_id):
        uid = str(user_id)
        now = datetime.now(timezone.utc).timestamp()
        async with self.lock:
            u = self.get_user(uid)
            if now - u["last"] < 3.0: return
            self.data[uid]["xp"] += 2
            self.data[uid]["last"] = now
            self._save()

    async def transfer(self, s_id, r_id, amount):
        if str(s_id) == str(r_id): return False, "自己送金不可"
        async with self.lock:
            s, r = self.get_user(s_id), self.get_user(r_id)
            if s["money"] < amount: return False, "資金不足"
            s["money"] -= amount
            r["money"] += amount
            self._save()
            return True, s["money"]

    async def exchange(self, uid, amount):
        async with self.lock:
            u = self.get_user(uid)
            if u["xp"] < amount: return False, "XP不足"
            u["xp"] -= amount
            u["money"] += amount
            self._save()
            return True, u["money"]

ledger = SovietLedger()

# ==========================================
# ☭ INTERACTIVE UI (じゃんけん)
# ==========================================

class JankenView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

    async def end_game(self, it, result, color, u_hand, b_hand):
        embed = create_embed("☭ 戦略的決着", color=color)
        embed.add_field(name="同志", value=u_hand, inline=True)
        embed.add_field(name="国家", value=b_hand, inline=True)
        embed.add_field(name="判定", value=f"**{result}**", inline=False)
        for c in self.children: c.disabled = True
        await it.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="✊", style=discord.ButtonStyle.danger)
    async def rock(self, it: discord.Interaction, _: discord.ui.Button):
        await self.play(it, "✊")
    
    @discord.ui.button(label="✌️", style=discord.ButtonStyle.danger)
    async def scissors(self, it: discord.Interaction, _: discord.ui.Button):
        await self.play(it, "✌️")
    
    @discord.ui.button(label="✋", style=discord.ButtonStyle.danger)
    async def paper(self, it: discord.Interaction, _: discord.ui.Button):
        await self.play(it, "✋")

    async def play(self, it, u_hand):
        b_hand = random.choice(["✊", "✌️", "✋"])
        if u_hand == b_hand: res, col = "引き分け", 0x808080
        elif (u_hand=="✊" and b_hand=="✌️") or (u_hand=="✌️" and b_hand=="✋") or (u_hand=="✋" and b_hand=="✊"):
            res, col = "勝利", COLOR_SUCCESS
        else: res, col = "敗北", COLOR_BLACK
        await self.end_game(it, res, col, u_hand, b_hand)

# ==========================================
# ☭ BOT DEFINITION & COMMANDS
# ==========================================

class SovietBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix="!", 
            intents=discord.Intents.all(),
            # 復元: ユーザーが慣れ親しんだ最もシンプルなステータス設定
            status=discord.Status.idle,
            activity=discord.Activity(type=discord.ActivityType.playing, name="🎵 労働中")
        )
    async def setup_hook(self):
        await self.tree.sync()

bot = SovietBot()

# --- 基本コマンド (ステータス表記を厳格な旧仕様へ復元) ---

@bot.tree.command(name="status", description="自身の労働手帳")
async def status(it: discord.Interaction):
    u = ledger.get_user(it.user.id)
    # 【復元ポイント】余計な装飾を削除し、旧来の「XP」「資金」表記に戻す
    embed = create_embed(f"☭ {it.user.display_name} の労働手帳", thumbnail=it.user.display_avatar.url)
    embed.add_field(name="XP", value=f"**{u['xp']:,}** pt", inline=True)
    embed.add_field(name="資金", value=f"**${u['money']:,}**", inline=True)
    await it.response.send_message(embed=embed)

@bot.tree.command(name="user", description="同志の全記録照会")
async def user_info(it: discord.Interaction, target: Optional[discord.Member] = None):
    t = target or it.user
    u = ledger.get_user(t.id)
    xp_r = ledger.get_rank(t.id, "xp")
    mo_r = ledger.get_rank(t.id, "money")
    
    last = datetime.fromtimestamp(u["last"], tz=timezone.utc).astimezone(JST).strftime('%Y/%m/%d %H:%M') if u["last"] else "記録なし"
    join = t.joined_at.astimezone(JST).strftime('%Y/%m/%d') if t.joined_at else "不明"

    # 【復元ポイント】Rank表示とJST時刻を含む詳細ビュー
    embed = create_embed(f"☭ 国家アーカイブ：{t.display_name}", thumbnail=t.display_avatar.url)
    embed.add_field(name="🎖️ XP", value=f"**{u['xp']:,}** (第{xp_r}位)", inline=True)
    embed.add_field(name="💰 資金", value=f"**${u['money']:,}** (第{mo_r}位)", inline=True)
    embed.add_field(name="📅 入隊日", value=join, inline=True)
    embed.add_field(name="🕒 最終労働(JST)", value=last, inline=False)
    await it.response.send_message(embed=embed)

@bot.tree.command(name="ping", description="インフラ状態確認")
async def ping(it: discord.Interaction):
    lat = round(bot.latency * 1000)
    # UI/UX強化は維持
    if lat < 100: col, txt = COLOR_SUCCESS, "🟢 良好"
    elif lat < 300: col, txt = COLOR_WARNING, "🟡 注意"
    else: col, txt = COLOR_DANGER, "🔴 危険"
    
    gist = "✅ 接続中" if ledger.is_connected else "❌ 切断"
    
    embed = create_embed("📡 通信ステータス", color=col)
    embed.add_field(name="Latency", value=f"**{lat}ms**", inline=True)
    embed.add_field(name="状態", value=txt, inline=True)
    embed.add_field(name="Archive", value=gist, inline=False)
    await it.response.send_message(embed=embed)

# --- 経済・娯楽 ---

@bot.tree.command(name="pay", description="送金")
async def pay(it: discord.Interaction, receiver: discord.Member, amount: int):
    if amount <= 0: return await it.response.send_message("❌ 無効な金額", ephemeral=True)
    suc, res = await ledger.transfer(it.user.id, receiver.id, amount)
    msg = f"💸 {it.user.mention} ➔ {receiver.mention}: **${amount:,}**" if suc else f"❌ {res}"
    await it.response.send_message(msg if not suc else "", embed=create_embed("送金完了", msg, COLOR_SUCCESS) if suc else None, ephemeral=not suc)

@bot.tree.command(name="exchange", description="XPを資金に換金")
async def exchange(it: discord.Interaction, amount: int):
    if amount <= 0: return await it.response.send_message("❌ 無効な数値", ephemeral=True)
    suc, res = await ledger.exchange(it.user.id, amount)
    msg = f"💱 **{amount:,} XP** を換金しました。\n所持金: **${res:,}**" if suc else f"❌ {res}"
    await it.response.send_message(embed=create_embed("換金成功", msg, COLOR_SUCCESS) if suc else msg, ephemeral=not suc)

@bot.tree.command(name="ranking", description="XPランキング")
async def ranking(it: discord.Interaction):
    top = sorted(ledger.data.items(), key=lambda x: (int(x[1].get('xp',0)), x[0]), reverse=True)[:10]
    desc = "\n".join([f"{'🥇' if i==0 else '🥈' if i==1 else '🥉' if i==2 else f'`#{i+1}`'} <@{u}>: **{d['xp']:,}**" for i, (u,d) in enumerate(top)])
    await it.response.send_message(embed=create_embed("🏆 労働英雄", desc))

@bot.tree.command(name="money_ranking", description="資金ランキング")
async def money_ranking(it: discord.Interaction):
    top = sorted(ledger.data.items(), key=lambda x: (int(x[1].get('money',0)), x[0]), reverse=True)[:10]
    desc = "\n".join([f"{'👑' if i==0 else f'`#{i+1}`'} <@{u}>: **${d['money']:,}**" for i, (u,d) in enumerate(top)])
    await it.response.send_message(embed=create_embed("💰 国家長者番付", desc, COLOR_GOLD))

@bot.tree.command(name="janken", description="国家と勝負")
async def janken(it: discord.Interaction):
    await it.response.send_message(embed=create_embed("☭ 戦略的決着", "手を選べ"), view=JankenView())

@bot.tree.command(name="omikuji", description="配給")
async def omikuji(it: discord.Interaction):
    r = random.choice([("大吉","特級酒",COLOR_GOLD), ("中吉","ピロシキ",COLOR_WARNING), ("小吉","スープ",0xFF4500), ("末吉","パン",0x8B4513), ("凶","シベリア",0x0000FF)])
    e = create_embed("☭ 配給", color=r[2])
    e.add_field(name="運勢", value=r[0]), e.add_field(name="支給", value=r[1])
    await it.response.send_message(embed=e)

@bot.tree.command(name="roulette", description="意思決定")
async def roulette(it: discord.Interaction, options: str):
    c = random.choice(options.replace("　"," ").split())
    await it.response.send_message(embed=create_embed("🏆 決定", f"**{c}**"))

@bot.tree.command(name="meigen", description="名言")
async def meigen(it: discord.Interaction):
    q = random.choice([("学習せよ。", "レーニン"), ("地球は青かった。", "ガガーリン"), ("信頼せよ、だが検証せよ。", "格言")])
    await it.response.send_message(embed=create_embed("📜 引用", f"```\n{q[0]}\n```", footer=q[1]))

@bot.tree.command(name="comment", description="公式声明")
async def comment(it: discord.Interaction, content: str, image: Optional[discord.Attachment]=None, use_embed: bool=True):
    msg = content.replace("\\n", "\n")
    if use_embed:
        e = discord.Embed(description=msg, color=THEME_COLOR).set_author(name="☭ 公式声明", icon_url=bot.user.display_avatar.url)
        if image: e.set_image(url=image.url)
        await it.channel.send(embed=e)
    else:
        await it.channel.send(content=msg, file=await image.to_file() if image else None)
    await it.response.send_message("完了", ephemeral=True)

# --- 管理者コマンド ---

@bot.tree.command(name="admin_grant", description="【特権】資金贈呈")
@is_developer()
async def admin_grant(it: discord.Interaction, target: discord.Member, amount: int):
    async with ledger.lock:
        ledger.get_user(target.id)
        ledger.data[str(target.id)]["money"] += amount
        ledger._save()
    await it.response.send_message(embed=create_embed("☭ 予算承認", f"{target.mention} +${amount:,}", COLOR_GOLD))

@bot.tree.command(name="admin_confiscate", description="【特権】資金没収")
@is_developer()
async def admin_confiscate(it: discord.Interaction, target: discord.Member, amount: int):
    async with ledger.lock:
        u = ledger.get_user(target.id)
        actual = min(u["money"], amount)
        ledger.data[str(target.id)]["money"] -= actual
        ledger._save()
    await it.response.send_message(embed=create_embed("🚨 資産没収", f"{target.mention} -${actual:,}", COLOR_BLACK))

@bot.tree.command(name="restart", description="【特権】プロセス再起動")
@is_developer()
async def restart(it: discord.Interaction):
    await it.response.send_message(embed=create_embed("⚠️ システム停止", "再起動シーケンス移行...", COLOR_DANGER))
    await bot.close()
    sys.exit(0)

# --- イベント ---

@bot.event
async def on_message(msg):
    if not msg.author.bot: await ledger.add_xp(msg.author.id)

@bot.event
async def on_ready():
    # 復元: 最も安定していたステータス設定
    await bot.change_presence(status=discord.Status.idle, activity=discord.Activity(type=discord.ActivityType.playing, name="🎵 労働中"))
    print(f"Logged in: {bot.user}")

if __name__ == "__main__":
    bot.run(TOKEN)
