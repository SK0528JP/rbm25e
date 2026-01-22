import discord
from discord.ext import commands
from datetime import datetime, timedelta, timezone

# main.py の JST 設定と同期
JST = timezone(timedelta(hours=9), 'JST')

class Ryokuho(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.target_user_id = 1128950351362535456
        self.target_channel_id = 1367349493116440639

    def format_duration(self, seconds):
        """秒数を 〇時間〇分 の形式に変換"""
        if seconds <= 0:
            return "0分"
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}時間{minutes}分"

    def calculate_stats(self, user_data):
        """Ledger内の全ログから期間ごとの統計を計算"""
        now = datetime.now(JST)
        
        # 判定基準日時の設定
        start_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start_week = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        start_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        start_year = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

        logs = user_data.get("online_logs", [])
        
        stats = {
            "今日": {"count": 0, "sec": 0},
            "今週": {"sec": 0},
            "今月": {"sec": 0},
            "今年": {"sec": 0}
        }

        for log in logs:
            try:
                # ISO文字列をJSTのdatetimeに変換
                login_at = datetime.fromisoformat(log["login_at"])
                if login_at.tzinfo is None:
                    login_at = login_at.replace(tzinfo=JST)
                    
                sec = log["duration_sec"]

                # 各期間の集計
                if login_at >= start_year:
                    stats["今年"]["sec"] += sec
                if login_at >= start_month:
                    stats["今月"]["sec"] += sec
                if login_at >= start_week:
                    stats["今週"]["sec"] += sec
                if login_at >= start_today:
                    stats["今日"]["sec"] += sec
                    stats["今日"]["count"] += 1
            except (ValueError, KeyError):
                continue

        return stats

    @commands.Cog.listener()
    async def on_presence_update(self, before, after):
        # 指定ユーザーかつステータスの実質的な変化（オンライン化/オフライン化）のみ検知
        if after.id != self.target_user_id or before.status == after.status:
            return

        # Ledgerシステムが未接続なら中止
        if not self.bot.ledger:
            return

        user_data = self.bot.ledger.get_user(after.id)
        channel = self.bot.get_channel(self.target_channel_id)

        # --- [ログイン検知] ---
        if after.status == discord.Status.online:
            # 統計メッセージの生成
            stats = self.calculate_stats(user_data)
            count_today = stats["今日"]["count"] + 1
            
            msg = (
                f"📊 **りょくほのオンライン統計**\n"
                f"・本日のログイン回数: **{count_today}回目**\n"
                f"・今日の総オンライン時間: {self.format_duration(stats['今日']['sec'])}\n"
                f"・今週の合計: {self.format_duration(stats['今週']['sec'])}\n"
                f"・今月の合計: {self.format_duration(stats['今月']['sec'])}\n"
                f"・今年の合計: {self.format_duration(stats['今年']['sec'])}"
            )
            
            # セッション開始時刻を保存
            user_data["active_session_start"] = datetime.now(JST).isoformat()
            
            if channel:
                await channel.send(f"☢｜りょくほがオンラインになりました。\n{msg}")
            
            # オンライン開始時点でも保存（再起動で開始時刻が消えるのを防ぐ）
            self.bot.ledger.save()

        # --- [ログアウト検知] ---
        elif before.status == discord.Status.online and after.status != discord.Status.online:
            start_str = user_data.pop("active_session_start", None)
            
            if start_str:
                try:
                    start_dt = datetime.fromisoformat(start_str)
                    if start_dt.tzinfo is None:
                        start_dt = start_dt.replace(tzinfo=JST)
                    
                    # 滞在時間を秒で計算
                    duration = int((datetime.now(JST) - start_dt).total_seconds())
                    
                    # データの蓄積
                    if "online_logs" not in user_data:
                        user_data["online_logs"] = []
                    
                    user_data["online_logs"].append({
                        "login_at": start_str,
                        "duration_sec": max(0, duration)
                    })
                    
                    # 即時Gistへ同期
                    self.bot.ledger.save()
                    print(f"💾 [Ryokuho] Log Saved: {duration}s added to Ledger.")
                except Exception as e:
                    print(f"❌ [Ryokuho] Logout calculation error: {e}")

async def setup(bot):
    await bot.add_cog(Ryokuho(bot))
