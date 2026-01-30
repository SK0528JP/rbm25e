import discord
from discord.ext import commands
from datetime import datetime, timedelta, timezone

# JST (日本標準時) 定義
JST = timezone(timedelta(hours=9), 'JST')

class Ryokuho(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 監視対象ユーザーIDリスト
        self.target_user_ids = [
            1128950351362535456, # ryokuho
            719498030549696582,  # sera
            1315637350772244532, # satuki
            973500097675558913,  # eiki
            1105119266086342757, # ogi
            943574149048205392,  # aoto
            840821281838202880,  # sho
            929653926494621766,  # aoba
            844162909919772683   # hiro
        ]
        self.target_channel_id = 1367349493116440639
        
        # 連投防止用キャッシュ (UserID: LastNotificationTime)
        self.cooldowns = {}

    def format_duration(self, seconds):
        """秒数を人間が読みやすい形式に変換"""
        if seconds <= 0: return "0分"
        hours, remainder = divmod(seconds, 3600)
        minutes, _ = divmod(remainder, 60)
        return f"{hours}時間 {minutes}分" if hours > 0 else f"{minutes}分"

    def get_device_info(self, member):
        """オンライン端末情報の取得"""
        devices = []
        if member.desktop_status != discord.Status.offline: devices.append("💻 PC")
        if member.mobile_status != discord.Status.offline: devices.append("📱 スマホ")
        if member.web_status != discord.Status.offline: devices.append("🌐 ブラウザ")
        return " + ".join(devices) if devices else "不明"

    def get_status_style(self, status):
        """ステータスに応じた色とテキストを返す"""
        styles = {
            discord.Status.online: (0x43b581, "オンライン (Online)"),
            discord.Status.idle: (0xfaa61a, "退席中 (Idle)"),
            discord.Status.dnd: (0xf04747, "取り込み中 (DnD)")
        }
        # 未定義の場合はオフライン扱い
        return styles.get(status, (0x747f8d, "オフライン"))

    def calculate_stats(self, user_data):
        """統計データの計算"""
        now = datetime.now(JST)
        # 各期間の開始時点を計算
        start_today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        start_week = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
        start_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        start_year = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

        logs = user_data.get("online_logs", [])
        stats = {"今日": {"count": 0, "sec": 0}, "今週": {"sec": 0}, "今月": {"sec": 0}, "今年": {"sec": 0}}

        for log in logs:
            try:
                # タイムゾーン情報を安全に付与
                login_at = datetime.fromisoformat(log["login_at"])
                if login_at.tzinfo is None:
                    login_at = login_at.replace(tzinfo=JST)
                
                sec = log["duration_sec"]
                
                if login_at >= start_year: stats["今年"]["sec"] += sec
                if login_at >= start_month: stats["今月"]["sec"] += sec
                if login_at >= start_week: stats["今週"]["sec"] += sec
                if login_at >= start_today:
                    stats["今日"]["sec"] += sec
                    stats["今日"]["count"] += 1
            except (ValueError, KeyError):
                continue
        return stats

    @commands.Cog.listener()
    async def on_presence_update(self, before, after):
        """ステータス更新検知イベント"""
        
        # 1. ターゲット確認 & ステータス自体の変化がない場合は即終了
        if after.id not in self.target_user_ids or before.status == after.status:
            return

        now = datetime.now(JST)

        # ---------------------------------------------------------
        # 【活動開始 (Login / Active)】
        # ---------------------------------------------------------
        # オフライン状態から、オンライン/退席中/取り込み中のいずれかに変化した場合
        if before.status == discord.Status.offline and after.status != discord.Status.offline:
            
            # --- [連投防止ガード: 5秒ルール] ---
            # 前回の通知から5秒以内であれば、重複通知とみなして無視する
            last_time = self.cooldowns.get(after.id)
            if last_time and (now - last_time).total_seconds() < 5:
                return

            # 通知時刻を更新
            self.cooldowns[after.id] = now

            # Ledgerシステムチェック
            if not self.bot.ledger: return
            user_data = self.bot.ledger.get_user(after.id)
            
            # セッション開始時刻の記録 (重複書き込み防止)
            if "active_session_start" not in user_data:
                user_data["active_session_start"] = now.isoformat()

            # 統計計算とUI作成
            stats = self.calculate_stats(user_data)
            color, status_text = self.get_status_style(after.status)
            device_text = self.get_device_info(after)

            embed = discord.Embed(
                title=f"🚀 {after.display_name} 活動開始",
                description=f"状態: **{status_text}**",
                color=color,
                timestamp=now
            )
            embed.set_thumbnail(url=after.display_avatar.url)
            embed.add_field(name="📱 使用端末", value=f"```\n{device_text}\n```", inline=False)
            
            st_text = (
                f"**今日:** {stats['今日']['count'] + 1}回目 / {self.format_duration(stats['今日']['sec'])}\n"
                f"**今週:** {self.format_duration(stats['今週']['sec'])}\n"
                f"**今月:** {self.format_duration(stats['今月']['sec'])}\n"
                f"**今年:** {self.format_duration(stats['今年']['sec'])}"
            )
            embed.add_field(name="⏱️ 統計", value=st_text, inline=False)
            embed.set_footer(text="Ryokuho System", icon_url=self.bot.user.display_avatar.url)

            # 送信
            channel = self.bot.get_channel(self.target_channel_id)
            if channel:
                await channel.send(embed=embed)
            
            # 即時保存 (Bot再起動対策)
            self.bot.ledger.save()

        # ---------------------------------------------------------
        # 【活動終了 (Logout)】
        # ---------------------------------------------------------
        # オフラインになった場合
        elif after.status == discord.Status.offline:
            
            # ログアウト時はクールダウンをリセット（即座の再ログインに備えるなら消す、誤作動防止なら残す）
            # ここでは自然な再ログインを検知できるよう削除します
            self.cooldowns.pop(after.id, None)
            
            if not self.bot.ledger: return
            user_data = self.bot.ledger.get_user(after.id)
            start_str = user_data.pop("active_session_start", None)
            
            if start_str:
                try:
                    start_dt = datetime.fromisoformat(start_str)
                    if start_dt.tzinfo is None:
                        start_dt = start_dt.replace(tzinfo=JST)
                        
                    duration = int((now - start_dt).total_seconds())
                    
                    if "online_logs" not in user_data:
                        user_data["online_logs"] = []
                    
                    # ログ保存
                    user_data["online_logs"].append({
                        "login_at": start_str,
                        "duration_sec": max(0, duration)
                    })
                    
                    self.bot.ledger.save()
                    print(f"💾 [Log] {after.display_name}: {duration}秒 (Saved)")
                except Exception as e:
                    print(f"❌ [Log Error] {e}")

async def setup(bot):
    await bot.add_cog(Ryokuho(bot))
