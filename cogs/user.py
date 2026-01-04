import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta, timezone
import re

# システム定数
MAIN_GUILD_ID = 1372567395419291698
ADMIN_ID = 840821281838202880

class User(commands.Cog):
    def __init__(self, bot, ledger):
        self.bot = bot
        self.ledger = ledger

    # --- ヘルパー: 公開バッジ解析 (全ユーザー共通) ---
    def get_user_badges(self, user):
        badges = []
        flags = user.public_flags
        
        if flags.staff: badges.append("🛠️ Staff")
        if flags.partner: badges.append("🤝 Partner")
        if flags.hypesquad: badges.append("🔥 HypeSquad Events")
        if flags.hypesquad_bravery: badges.append("🛡️ Bravery")
        if flags.hypesquad_brilliance: badges.append("✨ Brilliance")
        if flags.hypesquad_balance: badges.append("⚖️ Balance")
        if flags.bug_hunter: badges.append("🐛 Bug Hunter")
        if flags.bug_hunter_level_2: badges.append("🐛 Bug Hunter Gold")
        if flags.active_developer: badges.append("💻 Active Developer")
        if flags.verified_bot: badges.append("🤖 Verified Bot")
        if flags.early_supporter: badges.append("🎖️ Early Supporter")
        if flags.early_verified_bot_developer: badges.append("👨‍💻 Early Verified Dev")
        
        # Memberオブジェクトの場合のみブースト判定が可能
        if isinstance(user, discord.Member) and user.premium_since:
            badges.append("💎 Server Booster")
        
        return " | ".join(badges) if badges else "一般ユーザー"

    # --- ヘルパー: デバイス特定 ---
    def get_device_status(self, member):
        if not member or member.status == discord.Status.offline:
            return ""
        devices = []
        if member.desktop_status != discord.Status.offline: devices.append("💻 PC")
        if member.mobile_status != discord.Status.offline: devices.append("📱 モバイル")
        if member.web_status != discord.Status.offline: devices.append("🌐 Web")
        return f"[{' / '.join(devices)}]" if devices else ""

    @app_commands.command(name="user", description="対象の公開情報・活動状況・資産データを調査します")
    @app_commands.describe(
        target="ユーザーID、またはメンション（未入力で自分を調査）",
        mode="結果の表示モード（デフォルト: 自分のみ）"
    )
    @app_commands.choices(mode=[
        app_commands.Choice(name="🔒 自分のみ表示 (Private)", value=1),
        app_commands.Choice(name="📢 公開して表示 (Public)", value=0)
    ])
    async def user_info(self, it: discord.Interaction, target: str = None, mode: app_commands.Choice[int] = None):
        # modeが未指定の場合はデフォルトで「自分のみ(1)」とする
        is_ephemeral = True
        if mode and mode.value == 0:
            is_ephemeral = False

        await it.response.defer(ephemeral=is_ephemeral)

        user_obj = None
        full_user = None

        # 1. ターゲット解析（広域検索対応）
        try:
            if target is None:
                user_obj = it.guild.get_member(it.user.id) if it.guild else it.user
            else:
                clean_id_match = re.search(r'\d+', target)
                if clean_id_match:
                    target_id = int(clean_id_match.group())
                    # サーバー内検索を試行
                    if it.guild:
                        user_obj = it.guild.get_member(target_id)
                    # サーバー外、またはDMの場合はAPIから取得
                    if user_obj is None:
                        user_obj = await self.bot.fetch_user(target_id)
                else:
                    return await it.followup.send("❌ 有効なユーザーIDまたはメンションを入力してください。", ephemeral=is_ephemeral)
        except Exception as e:
            return await it.followup.send(f"❌ ユーザー情報を取得できませんでした: {e}", ephemeral=is_ephemeral)

        is_member = isinstance(user_obj, discord.Member)
        
        # バナー等の詳細情報を取得するためにAPIを叩く
        try:
            full_user = await self.bot.fetch_user(user_obj.id)
        except:
            full_user = user_obj

        # 2. 資産データ連携
        u_data = self.ledger.get_user(user_obj.id) if self.ledger else {"money": 0, "xp": 0}

        # 3. 視覚設計（アクセントカラー優先）
        accent_color = full_user.accent_color if hasattr(full_user, 'accent_color') and full_user.accent_color else 0x4C566A
        if is_member and user_obj.color.value != 0:
            accent_color = user_obj.color

        embed = discord.Embed(
            title=f"📋 ユーザー情報調査レポート: {full_user.global_name or full_user.name}",
            description=f"ユーザー名: `@{full_user.name}`",
            color=accent_color,
            # タイムスタンプはEmbed標準機能を使うとユーザーのローカル時間に合うが、
            # フッターにJST強制表示をご希望とのことなので、ここは現在時刻を入れずとも良いが
            # 一応メタデータとして入れておく（表示には影響しない）
            timestamp=datetime.now()
        )
        embed.set_thumbnail(url=full_user.display_avatar.url)

        # --- A: 基本識別情報 (全サーバー共通取得可能) ---
        created_ts = int(full_user.created_at.timestamp())
        identity = (
            f"**ID**: `{full_user.id}`\n"  # ` ` で囲むことでコピーしやすく
            f"**アカウント作成**: <t:{created_ts}:D> (<t:{created_ts}:R>)\n"
            f"**公開バッジ**: {self.get_user_badges(full_user)}"
        )
        # 本部所属判定 (MAIN_GUILD_ID)
        main_guild = self.bot.get_guild(MAIN_GUILD_ID)
        if main_guild and main_guild.get_member(full_user.id):
            identity += "\n**所属**: 🚩 瑞典技術設計局"
        embed.add_field(name="🆔 識別情報", value=identity, inline=False)

        # --- B: サーバー内ステータス (共通サーバーにいる場合のみ) ---
        if is_member:
            joined_ts = int(user_obj.joined_at.timestamp())
            roles = [r.mention for r in reversed(user_obj.roles) if r.name != "@everyone"]
            role_str = " ".join(roles[:10]) + ("..." if len(roles) > 10 else "")
            
            perms = user_obj.guild_permissions
            p_list = []
            if perms.administrator: p_list.append("👑管理者")
            if perms.manage_guild: p_list.append("⚙️サーバー管理")
            if perms.manage_roles: p_list.append("🛡️ロール管理")
            
            srv_status = (
                f"**サーバー参加**: <t:{joined_ts}:D> (<t:{joined_ts}:R>)\n"
                f"**役職構成**: {role_str if role_str else 'なし'}"
            )
            if p_list: srv_status += f"\n**重要権限**: {', '.join(p_list)}"
            if user_obj.pending: srv_status += "\n⚠️ **メンバーシップ審査中**"
            embed.add_field(name="🏠 サーバー内ステータス", value=srv_status, inline=False)

        # --- C: リアルタイム活動 (視聴・音楽・ゲーム対応) ---
        if is_member:
            status_map = {
                discord.Status.online: "🟢 オンライン",
                discord.Status.idle: "🌙 退席中",
                discord.Status.dnd: "🔴 取り込み中",
                discord.Status.offline: "⚪ オフライン"
            }
            device_str = self.get_device_status(user_obj)
            
            activity_list = []
            for act in user_obj.activities:
                # 🎵 Spotify
                if isinstance(act, discord.Spotify):
                    track_url = f"https://open.spotify.com/track/{act.track_id}"
                    activity_list.append(f"🎵 **再生中**: [{act.title}]({track_url}) - {act.artist}")
                # 📡 ストリーミング
                elif isinstance(act, discord.Streaming):
                    activity_list.append(f"📡 **配信中**: [{act.name}]({act.url})")
                # 🎮 ゲーム
                elif isinstance(act, discord.Game):
                    activity_list.append(f"🎮 **プレイ中**: {act.name}")
                # 📺 視聴・その他
                elif isinstance(act, discord.Activity):
                    if act.type == discord.ActivityType.watching:
                        activity_list.append(f"📺 **視聴中**: {act.name}")
                    elif act.type == discord.ActivityType.listening:
                        activity_list.append(f"🎧 **再生中**: {act.name}")
                    else:
                        activity_list.append(f"🚀 **活動中**: {act.name}")
                # 📝 カスタム
                elif isinstance(act, discord.CustomActivity):
                    c_text = (f"{act.emoji} " if act.emoji else "") + (str(act.name) if act.name else "")
                    if c_text: activity_list.append(f"📝 **ステータス**: {c_text}")

            act_val = f"**状態**: {status_map.get(user_obj.status, '⚪ オフライン')} {device_str}\n"
            act_val += "\n".join(activity_list) if activity_list else "アクティビティ非公開"
            embed.add_field(name="🚀 リアルタイム活動", value=act_val, inline=False)
        else:
            embed.add_field(name="🚀 リアルタイム活動", value="⚠️ 共通サーバー外のため非可視", inline=False)

        # --- D: 資産 & メディア ---
        resource_val = f"**所持金**: `{u_data.get('money', 0):,} cr` | **経験値**: `{u_data.get('xp', 0):,} xp`"
        embed.add_field(name="💎 資産データ", value=resource_val, inline=False)

        links = [f"[アイコン]({full_user.display_avatar.url})"]
        if full_user.banner:
            links.append(f"[バナー]({full_user.banner.url})")
        embed.add_field(name="🔗 メディアリンク", value=" | ".join(links), inline=True)

        # フッター設定 (JST対応 & 秒数表示)
        # UTC+9 (JST) のタイムゾーンを定義
        JST = timezone(timedelta(hours=9), 'JST')
        now_jst = datetime.now(JST)
        timestamp_str = now_jst.strftime('%Y-%m-%d %H:%M:%S')

        footer_label = "⚜️ Rb m/25E ユーザー調査モジュール" if full_user.id == ADMIN_ID else "Rb m/25E ユーザー調査モジュール"
        embed.set_footer(text=f"{footer_label} | {timestamp_str}")

        await it.followup.send(embed=embed, ephemeral=is_ephemeral)

async def setup(bot):
    # ledger_instanceはmain.pyで定義されている前提
    from __main__ import ledger_instance
    await bot.add_cog(User(bot, ledger_instance))
