import discord
from discord.ext import commands
from discord import app_commands

class User(commands.Cog):
    def __init__(self, bot, ledger):
        self.bot = bot
        self.ledger = ledger

    @app_commands.command(name="user", description="ユーザーの全公開情報を最大限に調査・表示します")
    @app_commands.describe(target="ユーザーのメンション、またはユーザーIDを入力してください")
    async def user_info(self, it: discord.Interaction, target: str = None):
        """
        指定したユーザーの公開情報を限界まで取得し、詳細なプロファイルを作成します。
        """
        await it.response.defer()

        user_obj = None
        is_member = False

        # 1. ターゲットの特定
        if target is None:
            user_obj = it.user
            is_member = True
        else:
            clean_id = target.replace("<@", "").replace(">", "").replace("!", "").replace("&", "")
            if clean_id.isdigit():
                try:
                    # サーバー内メンバーとして取得試行
                    if it.guild:
                        user_obj = it.guild.get_member(int(clean_id))
                    
                    if user_obj:
                        is_member = True
                    else:
                        # サーバー外のユーザーをAPIから直接取得
                        user_obj = await self.bot.fetch_user(int(clean_id))
                except Exception:
                    user_obj = None
            else:
                await it.followup.send("❌ 有効なユーザーID、またはメンションを入力してください。", ephemeral=True)
                return

        if user_obj is None:
            await it.followup.send("❌ ユーザーを特定できませんでした。IDが正しいか確認してください。", ephemeral=True)
            return

        # 2. データの収集 (Rb m/25 Economy)
        u_data = self.ledger.get_user(user_obj.id)
        avatar_url = user_obj.display_avatar.url
        
        # 色の設定（メンバーなら最高位ロールの色、そうでなければデフォルト）
        # 北欧デザイン的スレートグレーをデフォルトに
        color = user_obj.color if is_member and user_obj.color.value != 0 else 0x4C566A

        embed = discord.Embed(title=f"🔍 ユーザー精密調査レポート", color=color)
        embed.set_thumbnail(url=avatar_url)
        embed.description = f"**[{user_obj.name}]( {avatar_url} )** のプロファイル詳細"

        # --- フィールド1: アカウント基本情報 ---
        creation_time = f"<t:{int(user_obj.created_at.timestamp())}:D> (<t:{int(user_obj.created_at.timestamp())}:R>)"
        
        # フラグ（バッジ）の取得
        badges = []
        flags = user_obj.public_flags
        if flags.staff: badges.append("Discord Staff")
        if flags.partner: badges.append("Partner")
        if flags.hypesquad: badges.append("HypeSquad")
        if flags.bug_hunter: badges.append("Bug Hunter")
        if flags.active_developer: badges.append("Active Dev")
        if flags.verified_bot: badges.append("Verified Bot")
        
        badge_str = ", ".join(badges) if badges else "なし"

        basic_info = (
            f"**ID**: `{user_obj.id}`\n"
            f"**タイプ**: {'🤖 ボット' if user_obj.bot else '👤 ユーザー'}\n"
            f"**アカウント作成**: {creation_time}\n"
            f"**公的バッジ**: {badge_str}"
        )
        embed.add_field(name="📌 基本データ", value=basic_info, inline=False)

        # --- フィールド2: サーバー内情報 & ステータス (メンバーの場合のみ) ---
        if is_member:
            # 参加日
            join_time = f"<t:{int(user_obj.joined_at.timestamp())}:D> (<t:{int(user_obj.joined_at.timestamp())}:R>)"
            
            # ロール
            roles = [role.mention for role in reversed(user_obj.roles) if role.name != "@everyone"]
            role_str = " ".join(roles[:8]) + ("..." if len(roles) > 8 else "")
            
            # 権限チェック
            key_perms = []
            perms = user_obj.guild_permissions
            if perms.administrator: key_perms.append("⚡ 管理者")
            elif perms.manage_guild: key_perms.append("🛡️ サーバー管理")
            if perms.ban_members: key_perms.append("🚫 BAN権限")
            if perms.manage_messages: key_perms.append("💬 メッセージ管理")
            perm_str = ", ".join(key_perms) if key_perms else "一般権限"

            # 接続ステータスと端末
            status_map = {
                discord.Status.online: "🟢 オンライン",
                discord.Status.idle: "🌙 退席中",
                discord.Status.dnd: "🔴 取り込み中",
                discord.Status.offline: "⚪ オフライン",
                discord.Status.invisible: "⚪ オフライン(隠れ)"
            }
            current_status = status_map.get(user_obj.status, "不明")
            
            # 端末特定 (オンライン系の場合のみ有効)
            devices = []
            if str(user_obj.status) != "offline":
                if user_obj.desktop_status != discord.Status.offline: devices.append("💻 PC")
                if user_obj.mobile_status != discord.Status.offline: devices.append("📱 Mobile")
                if user_obj.web_status != discord.Status.offline: devices.append("🌐 Web")
            device_str = " / ".join(devices) if devices else ""

            member_info = (
                f"**サーバー参加**: {join_time}\n"
                f"**主要ロール**: {role_str if role_str else 'なし'}\n"
                f"**権限レベル**: {perm_str}\n"
                f"**ステータス**: {current_status} {device_str}"
            )
            embed.add_field(name="🏠 サーバー・プレゼンス情報", value=member_info, inline=False)

            # --- フィールド2.5: アクティビティ (現在何をしているか) ---
            if user_obj.activities:
                activity_lines = []
                for act in user_obj.activities:
                    if isinstance(act, discord.Spotify):
                        activity_lines.append(f"🎵 **Spotify**: {act.title} - {act.artist}")
                    elif isinstance(act, discord.Game):
                        activity_lines.append(f"🎮 **Game**: {act.name}")
                    elif isinstance(act, discord.Streaming):
                        activity_lines.append(f"📡 **Streaming**: {act.name}")
                    elif isinstance(act, discord.CustomActivity):
                        emoji = f"{act.emoji} " if act.emoji else ""
                        activity_lines.append(f"📝 **Status**: {emoji}{act.name}")
                    else:
                        activity_lines.append(f"🔹 {act.name}")
                
                if activity_lines:
                    embed.add_field(name="🚀 現在のアクティビティ", value="\n".join(activity_lines), inline=False)

        # --- フィールド3: Rb m/25 システムデータ ---
        sys_info = (
            f"💰 **保有資産**: {u_data.get('money', 0):,} cr\n"
            f"✨ **貢献度 (XP)**: {u_data.get('xp', 0):,} XP\n"
            f"📅 **システム登録**: `{u_data.get('joined_at', '記録なし')}`"
        )
        embed.add_field(name="💎 Rb m/25 内部データ", value=sys_info, inline=False)

        # --- フッター ---
        footer_text = f"Rb m/25 Tactical System | User ID: {user_obj.id}"
        if user_obj.id == 840821281838202880:
             footer_text = "⚠️ Rb m/25 System Administrator | " + footer_text
        
        embed.set_footer(text=footer_text)

        await it.followup.send(embed=embed)

async def setup(bot):
    # main.py の ledger_instance を参照
    from __main__ import ledger_instance
    await bot.add_cog(User(bot, ledger_instance))
