import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime
import re

# システム定数
MAIN_GUILD_ID = 1372567395419291698
ADMIN_ID = 840821281838202880

class User(commands.Cog):
    def __init__(self, bot, ledger):
        self.bot = bot
        self.ledger = ledger

    # --- ヘルパー: バッジ解析 (完全版) ---
    def get_user_badges(self, user):
        badges = []
        flags = user.public_flags
        
        if flags.staff: badges.append("🛠️ Staff")
        if flags.partner: badges.append("🤝 Partner")
        if flags.hypesquad: badges.append("🔥 HypeSquad Events")
        if flags.hypesquad_bravery: badges.append("🛡️ Bravery")
        if flags.hypesquad_brilliance: badges.append("✨ Brilliance")
        if flags.hypesquad_balance: badges.append("⚖️ Balance")
        if flags.bug_hunter: badges.append("🐛 Bug Hunter (Green)")
        if flags.bug_hunter_level_2: badges.append("🐛 Bug Hunter (Gold)")
        if flags.active_developer: badges.append("💻 Active Developer")
        if flags.verified_bot: badges.append("🤖 Verified Bot")
        if flags.early_supporter: badges.append("🎖️ Early Supporter")
        if flags.early_verified_bot_developer: badges.append("👨‍💻 Early Verified Dev")
        
        if isinstance(user, discord.Member) and user.premium_since:
            badges.append("💎 Server Booster")
        
        return " | ".join(badges) if badges else "一般市民"

    # --- ヘルパー: デバイス特定 ---
    def get_device_status(self, member):
        if not member or member.status == discord.Status.offline:
            return ""
        devices = []
        if member.desktop_status != discord.Status.offline: devices.append("💻 PC")
        if member.mobile_status != discord.Status.offline: devices.append("📱 Mob")
        if member.web_status != discord.Status.offline: devices.append("🌐 Web")
        return f"[{' / '.join(devices)}]" if devices else ""

    @app_commands.command(name="user", description="対象の公開情報・活動状況・資産データを極限まで調査します")
    @app_commands.describe(target="ユーザーID、またはメンション（未入力で自分を調査）")
    async def user_info(self, it: discord.Interaction, target: str = None):
        await it.response.defer()

        user_obj = None
        is_member = False

        # 1. ターゲット解析（Memberオブジェクト取得を最優先）
        if target is None:
            if it.guild:
                user_obj = it.guild.get_member(it.user.id)
            user_obj = user_obj or it.user
            is_member = isinstance(user_obj, discord.Member)
        else:
            clean_id_match = re.search(r'\d+', target)
            if clean_id_match:
                clean_id = int(clean_id_match.group())
                try:
                    if it.guild:
                        user_obj = it.guild.get_member(clean_id)
                    if user_obj:
                        is_member = True
                    else:
                        user_obj = await self.bot.fetch_user(clean_id)
                except:
                    user_obj = None

        if user_obj is None:
            return await it.followup.send("❌ ターゲットを捕捉できませんでした。", ephemeral=True)

        # 2. 資産データ
        u_data = self.ledger.get_user(user_obj.id) if self.ledger else {"money": 0, "xp": 0}

        # 3. 視覚設計（アクセントカラー）
        accent_color = 0x4C566A
        if is_member and user_obj.color.value != 0:
            accent_color = user_obj.color

        embed = discord.Embed(
            title=f"📋 ユーザー調査報告書: {user_obj.global_name or user_obj.name}",
            color=accent_color,
            timestamp=datetime.now()
        )
        embed.set_thumbnail(url=user_obj.display_avatar.url)

        # --- A: 基本識別情報 ---
        created_ts = int(user_obj.created_at.timestamp())
        identity = (
            f"**ID**: `{user_obj.id}`\n"
            f"**アカウント作成**: <t:{created_ts}:D> (<t:{created_ts}:R>)\n"
            f"**バッジ**: {self.get_user_badges(user_obj)}"
        )
        if self.bot.get_guild(MAIN_GUILD_ID) and self.bot.get_guild(MAIN_GUILD_ID).get_member(user_obj.id):
            identity += "\n**所属**: 🚩 瑞典工業設計局（開発拠点）"
        embed.add_field(name="🆔 識別情報", value=identity, inline=False)

        # --- B: サーバー内ステータス (Member限定) ---
        if is_member:
            joined_ts = int(user_obj.joined_at.timestamp())
            roles = [r.mention for r in reversed(user_obj.roles) if r.name != "@everyone"]
            role_str = " ".join(roles[:15]) + ("..." if len(roles) > 15 else "")
            
            # 重要権限の抽出
            perms = user_obj.guild_permissions
            p_list = []
            if perms.administrator: p_list.append("👑管理者")
            if perms.manage_guild: p_list.append("⚙️サーバー管理")
            if perms.manage_roles: p_list.append("🛡️ロール管理")
            if perms.ban_members: p_list.append("🔨BAN権限")
            
            srv_status = (
                f"**参加日時**: <t:{joined_ts}:D> (<t:{joined_ts}:R>)\n"
                f"**ニックネーム**: {user_obj.nick or '未設定'}\n"
                f"**保有権限**: {', '.join(p_list) if p_list else '一般'}\n"
                f"**役職構成**: {role_str if role_str else 'なし'}"
            )
            if user_obj.pending:
                srv_status += "\n**注意**: ⚠️ メンバーシップ審査中"
            embed.add_field(name="🏠 サーバー内ステータス", value=srv_status, inline=False)

            # --- C: リアルタイム活動 ---
            status_map = {
                discord.Status.online: "🟢 Online",
                discord.Status.idle: "🌙 Idle",
                discord.Status.dnd: "🔴 DnD",
                discord.Status.offline: "⚪ Offline"
            }
            device_str = self.get_device_status(user_obj)
            
            activity_list = []
            for act in user_obj.activities:
                if isinstance(act, discord.Spotify):
                    track_url = f"https://open.spotify.com/track/{act.track_id}"
                    activity_list.append(f"🎵 **Spotify**: [{act.title}]({track_url}) - {act.artist}")
                elif isinstance(act, discord.Game):
                    activity_list.append(f"🎮 **Game**: {act.name}")
                elif isinstance(act, discord.Streaming):
                    activity_list.append(f"📡 **Live**: [{act.name}]({act.url})")
                elif isinstance(act, discord.CustomActivity):
                    c_text = (f"{act.emoji} " if act.emoji else "") + (str(act.name) if act.name else "")
                    if c_text: activity_list.append(f"📝 **Status**: {c_text}")

            act_val = f"**状態**: {status_map.get(user_obj.status, '⚪ Offline')} {device_str}\n"
            act_val += "\n".join(activity_list) if activity_list else "アクティビティなし"
            embed.add_field(name="🚀 リアルタイム活動", value=act_val, inline=False)

        # --- D: 資産 & リソース ---
        resource_val = (
            f"**所持金**: `{u_data.get('money', 0):,} cr`\n"
            f"**経験値**: `{u_data.get('xp', 0):,} xp`"
        )
        embed.add_field(name="💎 資産データ", value=resource_val, inline=True)

        # --- E: メディアリンク ---
        links = [f"[Avatar]({user_obj.display_avatar.url})"]
        try:
            full_user = await self.bot.fetch_user(user_obj.id)
            if full_user.banner:
                links.append(f"[Banner]({full_user.banner.url})")
        except: pass
        embed.add_field(name="🔗 メディア", value=" | ".join(links), inline=True)

        # フッター
        footer_label = "⚠️ Rb m/25E 最高管理者" if user_obj.id == ADMIN_ID else "Rb m/25E 調査モジュール"
        embed.set_footer(text=f"{footer_label} | {datetime.now().strftime('%Y-%m-%d %H:%M')}")

        await it.followup.send(embed=embed)

async def setup(bot):
    from __main__ import ledger_instance
    await bot.add_cog(User(bot, ledger_instance))
