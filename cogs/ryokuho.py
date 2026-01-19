import discord
from discord.ext import commands
from datetime import datetime, timedelta, timezone

# 日本標準時 (main.pyと合わせる)
JST = timezone(timedelta(hours=9), 'JST')

class Ryokuho(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.target_user_id = 1128950351362535456
        self.target_channel_id = 1367349493116440639

    def format_duration(self, seconds):
        """秒数を 〇時間〇分 に変換"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}時間{minutes}分"

    def get_stats(self, user_data):
        """Ledgerのデータから統計を計算"""
        now = datetime.now(JST)
        
        # 各期間の開始時間を計算
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
                # 記録された時刻をJSTとして読み込み
                login_at = datetime.fromisoformat(log["login_at"])
                sec = log["duration_sec"]

                if login_at >= start_year: stats["今年"]["sec"] += sec
                if login_at >= start_month: stats["今月"]["sec"] += sec
                if login_at >= start_week: stats["今週"]["sec"] += sec
                if login_at >= start_today:
                    stats["今日"]["sec"] += sec
                    stats["今日"]["count"] += 1
            except:
                continue

        return (
            f"📊 **りょくほのオンライン統計**\n"
            f"・本日のログイン回数: **{stats['今日']['count'] + 1}回目**\n"
            f"・今日の総オンライン時間: {self.format_duration(stats['今日']['sec'])}\n"
            f"・今週の合計: {self.format_duration(stats['今週']['sec'])}\n"
            f"・今月の合計: {self.format_duration(stats['今月']['sec'])}\n"
            f"・今年の合計: {self.format_duration(stats['今年']['sec'])}"
        )

    @commands.Cog.listener()
    async def on_presence_update(self, before, after):
        # 指定ユーザー以外は無視
        if after.id != self.target_user_id:
            return

        # Ledgerが有効でない場合は何もしない
        if not self.bot.ledger:
            return

        user_data = self.bot.ledger.get_user(after.id)
        channel = self.bot.get_channel(self.target_channel_id)

        # 【オンラインになった時】
        if before.status != discord.Status.online and after.status == discord.Status.online:
            # 統計メッセージを作成
            stats_msg = self.get_stats(user_data)
            
            # ログイン開始時刻を記録
            user_data["active_session_start"] = datetime.now(JST).isoformat()
            
            if channel:
                await channel.send(f"@here りょくほがオンラインになりました。\n{stats_msg}")

        # 【オフラインになった時】
        elif before.status == discord.Status.online and after.status != discord.Status.online:
            start_time_str = user_data.pop("active_session_start", None)
            
            if start_time_str:
                start_time = datetime.fromisoformat(start_time_str)
                duration = int((datetime.now(JST) - start_time).total_seconds())
                
                # ログをリストに追加
                if "online_logs" not in user_data:
                    user_data["online_logs"] = []
                
                user_data["online_logs"].append({
                    "login_at": start_time_str,
                    "duration_sec": duration
                })
                
                # main.pyのauto_saveタスクが10分おきにGistへ保存するが、
                # 即時保存したい場合はここで self.bot.ledger.save() を呼ぶことも可能

async def setup(bot):
    await bot.add_cog(Ryokuho(bot))
