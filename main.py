import os
import sys
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

# 定数・権限設定
THEME_COLOR = 0xCC0000  # ソビエト・レッド
JST = timezone(timedelta(hours=9))
ADMIN_ROLE_ID = 1453336556961140866  # @BOT開発者（特権階級）

# ===== 権限チェック用デコレータ =====
def is_developer():
    async def predicate(it: discord.Interaction) -> bool:
        role = discord.utils.get(it.user.roles, id=ADMIN_ROLE_ID)
        if role:
            return True
        # 権限がない場合のUI
        embed = discord.Embed(title="🚫 アクセス拒否", description="貴公にはこの高度な国家機密にアクセスする権限がない。", color=0x333333)
        await it.response.send_message(embed=embed, ephemeral=True)
        return False
    return app_commands.check(predicate)

# ===== 国家元帳（Gist API 永続化ストレージ） =====
class SovietLedger:
    def __init__(self):
        self.data = {}
        self.lock = asyncio.Lock()
        self.is_connected = False
        self._load()

    def _load(self):
        if not GITHUB_TOKEN or not GIST_ID:
            print("⚠️ 警告: 永続化設定がありません。")
            self.is_connected = False
            return
        try:
            headers = {"Authorization": f"token {GITHUB_TOKEN}"}
            res = requests.get(f"https://api.github.com/gists/{GIST_ID}", headers=headers)
            if res.status_code == 200:
                files = res.json().get("files", {})
                content = files.get("soviet_ledger.json", {}).get("content", "{}")
                self.data = json.loads(content)
                self.is_connected = True
                print("✅ Gist接続確立: 正常")
            else:
                print(f"❌ Gist接続失敗: {res.status_code}")
                self.is_connected = False
        except Exception as e:
            print(f"❌ Gistエラー: {e}")
            self.is_connected = False

    def _save(self):
        if not GITHUB_TOKEN or not GIST_ID: return
        try:
            headers = {"Authorization": f"token {GITHUB_TOKEN}"}
            payload = {"files": {"soviet_ledger.json": {"content": json.dumps(self.data, ensure_ascii=False, indent=4)}}}
            requests.patch(f"https://api.github.com/gists/{GIST_ID}", headers=headers, json=payload)
        except Exception as e:
            print(f"❌ 保存エラー: {e}")

    # データ操作メソッド群
    def get_user(self, user_id: str):
        uid = str(user_id)
        if uid not in self.data:
            self.data[uid] = {"xp": 0, "money": 0, "last": 0}
        u = self.data[uid]
        return {"xp": int(u.get("xp", 0)), "money": int(u.get("money", 0)), "last": float(u.get("last", 0))}

    def get_rank(self, user_id: str, key: str):
        # 数値として正しくソート
        sorted_list = sorted(self.data.items(), key=lambda x: (int(x[1].get(key, 0)), x[0]), reverse=True)
        for i, (uid, _) in enumerate(sorted_list):
            if uid == str(user_id): return i + 1
        return "圏外"

    async def add_xp(self, user_id: str):
        uid = str(user_id)
        now = datetime.now(timezone.utc).timestamp()
        async with self.lock:
            u = self.get_user(uid)
            if now - u["last"] < 3: return # クールダウン
            # 辞書を直接更新
            if uid not in self.data: self.data[uid] = u
            self.data[uid]["xp"] = u["xp"] + 2
            self.data[uid]["last"] = now
            self._save()

    async def transfer(self, sender_id: str, receiver_id: str, amount: int):
        s_uid, r_uid = str(sender_id), str(receiver_id)
        if s_uid == r_uid: return False, "自分自身への送金は無意味だ。"
        async with self.lock:
            s = self.get_user(s_uid)
            r = self.get_user(r_uid)
            if s["money"] < amount: return False, "資金が不足している。"
            
            # メモリ上のデータを更新
            if s_uid not in self.data: self.data[s_uid] = s
            if r_uid not in self.data: self.data[r_uid] = r
            
            self.data[s_uid]["money"] = s["money"] - amount
            self.data[r_uid]["money"] = r["money"] + amount
            self._save()
            return True, s["money"]

ledger = SovietLedger()

# ===== Bot定義 =====
class SovietBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.all(), status=discord.Status.idle,
                         activity=discord.Activity(type=discord.ActivityType.playing, name="🎵 労働歌"))
    async def setup_hook(self):
        await self.tree.sync()

bot = SovietBot()

# ===== 共通UI関数 =====
def create_embed(title: str, description: str = "", color: int = THEME_COLOR, thumbnail: str = None) -> discord.Embed:
    embed = discord.Embed(title=title, description=description, color=color)
    if thumbnail: embed.set_thumbnail(url=thumbnail)
    return embed

# ===== 一般コマンド =====

@bot.tree.command(name="ping", description="通信インフラとアーカイブ接続状況を確認する")
async def ping(it: discord.Interaction):
    # レイテンシ計測
    latency_ms = round(bot.latency * 1000)
    
    # 色とステータスの判定
    if latency_ms < 100:
        status_color = 0x00FF00  # 緑
        status_text = "🟢 極めて良好"
    elif latency_ms < 300:
        status_color = 0xFFA500  # 黄
        status_text = "🟡 注意"
    else:
        status_color = 0xFF0000  # 赤
        status_text = "🔴 警戒レベル"

    # アーカイブ接続判定
    gist_status = "✅ 接続中" if ledger.is_connected else "❌ 切断 (データ揮発の危険あり)"

    embed = discord.Embed(title="📡 国家通信網ステータス報告", color=status_color)
    embed.add_field(name="通信遅延 (Latency)", value=f"**{latency_ms}ms**", inline=True)
    embed.add_field(name="インフラ状態", value=status_text, inline=True)
    embed.add_field(name="アーカイブ接続 (Gist)", value=gist_status, inline=False)
    embed.set_footer(text=f"Check Time: {datetime.now(JST).strftime('%H:%M:%S')}")
    
    await it.response.send_message(embed=embed)

@bot.tree.command(name="user", description="同志の個人記録を照会する")
async def user_info(it: discord.Interaction, target: Optional[discord.Member] = None):
    t = target or it.user
    u = ledger.get_user(t.id)
    xp_rank = ledger.get_rank(t.id, "xp")
    money_rank = ledger.get_rank(t.id, "money")
    
    last_act = datetime.fromtimestamp(u["last"], tz=timezone.utc).astimezone(JST).strftime('%Y/%m/%d %H:%M') if u["last"] > 0 else "記録なし"
    join_date = t.joined_at.astimezone(JST).strftime('%Y/%m/%d') if t.joined_at else "不明"

    embed = create_embed(f"☭ 国家アーカイブ：{t.display_name}", thumbnail=t.display_avatar.url)
    embed.add_field(name="🎖️ 貢献度 (XP)", value=f"**{u['xp']:,} pt**\n(国内第 {xp_rank} 位)", inline=True)
    embed.add_field(name="💰 保有資金", value=f"**${u['money']:,}**\n(国内第 {money_rank} 位)", inline=True)
    embed.add_field(name="📅 入隊日", value=join_date, inline=True)
    embed.add_field(name="🕒 最終労働", value=last_act, inline=True)
    
    await it.response.send_message(embed=embed)

@bot.tree.command(name="status", description="自身の労働手帳を確認する")
async def status(it: discord.Interaction):
    u = ledger.get_user(it.user.id)
    embed = create_embed(f"📔 労働手帳：{it.user.display_name}", thumbnail=it.user.display_avatar.url)
    embed.add_field(name="貢献度", value=f"**{u['xp']:,}** pt", inline=True)
    embed.add_field(name="資金", value=f"**${u['money']:,}**", inline=True)
    await it.response.send_message(embed=embed)

@bot.tree.command(name="ranking", description="貢献度(XP)ランキング上位を表示")
async def ranking(it: discord.Interaction):
    top = sorted(ledger.data.items(), key=lambda x: (int(x[1].get('xp',0)), x[0]), reverse=True)[:10]
    
    desc = ""
    for i, (uid, d) in enumerate(top, 1):
        medal = "🥇" if i==1 else "🥈" if i==2 else "🥉" if i==3 else f"`#{i}`"
        desc += f"{medal} <@{uid}> : **{d.get('xp',0):,}** pt\n"
    
    embed = create_embed("🏆 労働英雄ランキング", desc if desc else "記録なし")
    await it.response.send_message(embed=embed)

@bot.tree.command(name="money_ranking", description="資金ランキング上位を表示")
async def money_ranking(it: discord.Interaction):
    top = sorted(ledger.data.items(), key=lambda x: (int(x[1].get('money',0)), x[0]), reverse=True)[:10]
    
    desc = ""
    for i, (uid, d) in enumerate(top, 1):
        medal = "👑" if i==1 else f"`#{i}`"
        desc += f"{medal} <@{uid}> : **${d.get('money',0):,}**\n"
    
    embed = create_embed("💰 国家長者番付", desc if desc else "記録なし", color=0xFFD700)
    await it.response.send_message(embed=embed)

@bot.tree.command(name="pay", description="資金を送金する")
async def pay(it: discord.Interaction, receiver: discord.Member, amount: int):
    if amount <= 0:
        return await it.response.send_message("❌ 金額は1以上で指定せよ。", ephemeral=True)
        
    success, result = await ledger.transfer(it.user.id, receiver.id, amount)
    
    if success:
        embed = create_embed("💸 送金完了", color=0x00FF00)
        embed.description = f"{it.user.mention} ➔ {receiver.mention}\n**${amount:,}** を送金した。"
        embed.set_footer(text=f"残高: ${result:,}")
        await it.response.send_message(embed=embed)
    else:
        await it.response.send_message(f"❌ 送金失敗: {result}", ephemeral=True)

@bot.tree.command(name="omikuji", description="本日の配給を受け取る")
async def omikuji(it: discord.Interaction):
    results = [
        {"r": "大吉", "i": "特級ウォッカ 🍾", "c": 0xFFD700},
        {"r": "中吉", "i": "ピロシキ 🥟", "c": 0xFFA500},
        {"r": "小吉", "i": "ボルシチ 🍲", "c": 0xFF4500},
        {"r": "末吉", "i": "黒パン 🍞", "c": 0x8B4513},
        {"r": "凶", "i": "シベリア強制労働 ❄️", "c": 0x0000FF}
    ]
    f = random.choice(results)
    embed = discord.Embed(title="☭ 今日の配給支給", color=f["c"])
    embed.add_field(name="運勢判定", value=f"**{f['r']}**", inline=True)
    embed.add_field(name="支給物資", value=f"**{f['i']}**", inline=True)
    await it.response.send_message(embed=embed)

# ===== 開発者限定コマンド =====

@bot.tree.command(name="admin_grant", description="【特権】資金を贈呈する")
@is_developer()
async def admin_grant(it: discord.Interaction, target: discord.Member, amount: int):
    if amount <= 0: return await it.response.send_message("❌ 正の数を指定せよ。", ephemeral=True)
    async with ledger.lock:
        if str(target.id) not in ledger.data: ledger.get_user(target.id)
        ledger.data[str(target.id)]["money"] += amount
        ledger._save()
    
    embed = create_embed("☭ 特別予算承認", f"{target.mention} へ **${amount:,}** の支給を実行した。", color=0xFFD700)
    embed.set_footer(text=f"承認者: {it.user.display_name}")
    await it.response.send_message(embed=embed)

@bot.tree.command(name="admin_confiscate", description="【特権】資金を没収する")
@is_developer()
async def admin_confiscate(it: discord.Interaction, target: discord.Member, amount: int):
    if amount <= 0: return await it.response.send_message("❌ 正の数を指定せよ。", ephemeral=True)
    async with ledger.lock:
        u = ledger.get_user(target.id)
        actual = min(u["money"], amount)
        ledger.data[str(target.id)]["money"] -= actual
        ledger._save()
        
    embed = create_embed("🚨 資産没収執行", f"{target.mention} から **${actual:,}** を没収した。", color=0x333333)
    embed.set_footer(text=f"執行者: {it.user.display_name}")
    await it.response.send_message(embed=embed)

@bot.tree.command(name="restart", description="【特権】Botプロセスを再起動（停止）する")
@is_developer()
async def restart(it: discord.Interaction):
    """
    GitHub Actions上では、プロセスが終了するとジョブが完了扱いとなります。
    Botを再稼働させるには、GitHub上で「Re-run jobs」を行うか、
    Git Pushで新しいトリガーを引く必要があります。
    """
    embed = create_embed("⚠️ システム再起動シーケンス", color=0xFF0000)
    embed.description = "プロセスを終了します。\nGitHub Actions環境の場合、自動で再起動しない場合があります。\nその場合はGitHubコンソールより手動で起動してください。"
    await it.response.send_message(embed=embed)
    
    print("Command: System Exit initiated by Administrator.")
    await bot.close()
    sys.exit(0)

# ===== イベントハンドラ =====
@bot.event
async def on_message(message):
    if message.author.bot: return
    await ledger.add_xp(message.author.id)
    # テキストコマンドは廃止し、スラッシュコマンドに一本化
    
@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name="☭ 労働の喜び"))
    print(f"同志 {bot.user}、全システム稼働開始。")

if __name__ == "__main__":
    bot.run(TOKEN)
