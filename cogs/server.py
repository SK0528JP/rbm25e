import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime

class ServerInfo(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="server", description="サーバーの詳細情報を調査・表示します。")
    @app_commands.describe(guild_id="調査対象のサーバーID（未入力で現在のサーバー）")
    async def server_info(self, interaction: discord.Interaction, guild_id: str = None):
        # 1. ターゲットサーバーの特定
        if guild_id:
            try:
                # 整数に変換可能かチェック
                target_id = int(guild_id)
                guild = self.bot.get_guild(target_id)
            except ValueError:
                return await interaction.response.send_message("❌ 無効なID形式です。数字のみを入力してください。", ephemeral=True)
            
            if not guild:
                return await interaction.response.send_message("❌ 指定されたIDのサーバーに機体（Bot）が所属していないため、アクセス権がありません。", ephemeral=True)
        else:
            guild = interaction.guild
            if not guild:
                return await interaction.response.send_message("❌ ここはサーバー内ではありません。IDを指定するか、サーバー内で実行してください。", ephemeral=True)

        # 2. 情報の収集
        created_at = guild.created_at.strftime("%Y/%m/%d %H:%M:%S")
        owner = guild.owner.mention if guild.owner else "不明"
        
        # メンバー数の集計（権限が必要な場合があるため安全に取得）
        member_count = guild.member_count
        # guild.membersが取得可能な場合のみBot数をカウント、不可なら"?"
        if guild.chunked or len(guild.members) > 0:
            bot_count = sum(1 for member in guild.members if member.bot)
            human_count = member_count - bot_count
            member_stats = f"総計: **{member_count}**\n人間: **{human_count}** / Bot: **{bot_count}**"
        else:
            member_stats = f"総計: **{member_count}**\n(詳細不明)"
        
        # チャンネル・ロール・絵文字
        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        roles_count = len(guild.roles)
        emoji_count = len(guild.emojis)
        
        # ブースト状況
        boost_level = guild.premium_tier
        boost_count = guild.premium_subscription_count

        # 3. Embedの構築
        embed = discord.Embed(
            title=f"📡 サーバー情報調査報告: {guild.name}",
            color=0x5865f2,
            timestamp=datetime.now()
        )

        # アイコン処理 (1024pxの最高画質を指定)
        if guild.icon:
            icon_url = guild.icon.with_size(1024).url
            embed.set_thumbnail(url=icon_url) # 右上の小窓
            embed.set_image(url=icon_url)     # 下部の拡大表示
        
        # バナーがあれば表示
        if guild.banner:
            embed.set_image(url=guild.banner.with_size(1024).url)

        embed.add_field(name="🆔 サーバーID", value=f"`{guild.id}`", inline=True)
        embed.add_field(name="👑 オーナー", value=owner, inline=True)
        embed.add_field(name="📅 設立日時", value=f"`{created_at}` (JST)", inline=False)
        
        embed.add_field(name="👥 メンバー構成", value=member_stats, inline=True)
        embed.add_field(name="💬 チャンネル", value=f"テキスト: **{text_channels}**\nボイス: **{voice_channels}**", inline=True)
        
        embed.add_field(name="🛡️ セキュリティ/機能", value=f"ロール数: **{roles_count}**\n絵文字数: **{emoji_count}**\n認証レベル: **{guild.verification_level}**", inline=True)
        embed.add_field(name="💎 ブースト状況", value=f"レベル: **{boost_level}**\n数: **{boost_count}**", inline=True)

        # サーバー特有の機能（バニティURL、コミュニティ設定など）
        if guild.features:
            features_str = " / ".join(guild.features)
            # 文字数が長すぎる場合の制限
            if len(features_str) > 500:
                features_str = features_str[:497] + "..."
            embed.add_field(name="🚀 サーバー機能", value=f"```\n{features_str}\n```", inline=False)

        embed.set_footer(text=f"調査員: {interaction.user.name}", icon_url=interaction.user.display_avatar.url)

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(ServerInfo(bot))
