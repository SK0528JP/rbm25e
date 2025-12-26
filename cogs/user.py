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

        # 2. データの収集
        u_data = self.ledger.get_user(user_obj.id)
        avatar_url = user_obj.display_avatar.url
        
        # 色の設定（メンバーなら最高位ロールの色、そうでなければデフォルト）
        color = user_obj.color if is_member else 0x94a3b8

        embed = discord.Embed(title=f"🔍 ユーザー精密調査レポート", color=color)
        embed.set_thumbnail(url=avatar_url)
        
        # プロフィール画像をタップで拡大できるようにリンクを貼る
        embed.description = f"**[{user_obj.name}#{user_obj.discriminator}]( {avatar_url} )** のプロファイル"

        # --- フィールド1: アカウント基本情報 ---
        creation_time = f"<t:{int(user_obj.created_at.timestamp())}:D> (<t:{int(user_obj.created_at.timestamp())}:R>)"
        basic_info = (
            f"**ID**: `{user_obj.id}`\n"
            f"**タイプ**: {'🤖 ボット' if user_obj.bot else '👤 ユーザー'}\n"
            f"**アカウント作成**: {creation_time}"
        )
        embed.add_field(name="📌 基本データ", value=basic_info, inline=False)

        # --- フィールド2: サーバー内情報 (メンバーの場合のみ) ---
        if is_member:
            join_time = f"<t:{int(user_obj.joined_at.timestamp())}:D> (<t:{int(user_obj.joined_at.timestamp())}:R>)"
            roles = [role.mention for role in reversed(user_obj.roles) if role.name != "@everyone"]
            role_str = " ".join(roles[:10]) + ("..." if len(roles) > 10 else "")
            
            member_info = (
                f"**ニックネーム**: {user_obj.nick if user_obj.nick else 'なし'}\n"
                f"**サーバー参加**: {join_time}\n"
                f"**主要ロール**: {role_str if role_str else 'なし'}"
            )
            embed.add_field(name="🏠 サーバー内ステータス", value=member_info, inline=False)

        # --- フィールド3: Rb m/25 システムデータ ---
        sys_info = (
            f"💰 **保有資産**: {u_data.get('money', 0):,} cr\n"
            f"✨ **貢献度 (XP)**: {u_data.get('xp', 0):,} XP\n"
            f"📅 **システム登録**: `{u_data.get('joined_at', '記録なし')}`"
        )
        embed.add_field(name="💎 Rb m/25 内部データ", value=sys_info, inline=False)

        # --- フッター: 特権情報 ---
        badges = []
        if user_obj.public_flags.staff: badges.append("Discord Staff")
        if user_obj.public_flags.partner: badges.append("Partner")
        if user_obj.public_flags.hypesquad: badges.append("HypeSquad Events")
        # 他にも多数ありますが、主要なものを判定可能
        
        footer_text = f"権限区分: {'✅ システム管理者' if user_obj.id == 840821281838202880 else '👤 一般ユーザー'}"
        if badges:
            footer_text += f" | Badges: {', '.join(badges)}"
        
        embed.set_footer(text=footer_text)

        await it.followup.send(embed=embed)

async def setup(bot):
    from __main__ import ledger_instance
    await bot.add_cog(User(bot, ledger_instance))
