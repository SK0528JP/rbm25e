import discord
from discord.ext import commands
from discord import app_commands
from datetime import datetime, timedelta, timezone

# タイムゾーン設定
JST = timezone(timedelta(hours=9), 'JST')

class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_now_jst(self):
        return datetime.now(JST).strftime('%Y-%m-%d %H:%M:%S')

    # --- 共通の表示設定オプション ---
    mode_choices = [
        app_commands.Choice(name="🔒 自分のみ表示 (Private)", value=1),
        app_commands.Choice(name="📢 公開して表示 (Public)", value=0)
    ]

    # --- 1. BAN コマンド ---
    @app_commands.command(name="ban", description="対象ユーザーをサーバーから追放し、再参加を禁止します")
    @app_commands.describe(
        target="追放するユーザー", 
        reason="追放の理由",
        mode="結果の表示モード（デフォルト: 自分のみ）"
    )
    @app_commands.choices(mode=mode_choices)
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, it: discord.Interaction, target: discord.Member, reason: str = "理由なし", mode: app_commands.Choice[int] = None):
        is_ephemeral = True if mode is None or mode.value == 1 else False
        await it.response.defer(ephemeral=is_ephemeral)

        if target.id == it.user.id:
            return await it.followup.send("❌ 自分自身を追放することはできません。")
        if target.top_role >= it.user.top_role:
            return await it.followup.send("❌ 権限不足: あなたと同等以上の役職を持つユーザーを処置できません。")

        try:
            await target.ban(reason=f"執行者: {it.user} | 理由: {reason}")
            
            embed = discord.Embed(title="🔨 執行報告: BAN", color=0xFF0000)
            embed.add_field(name="対象者", value=f"{target.mention} (`{target.id}`)", inline=False)
            embed.add_field(name="理由", value=reason, inline=False)
            embed.set_footer(text=f"執行時刻: {self.get_now_jst()}")
            
            await it.followup.send(embed=embed)
        except Exception as e:
            await it.followup.send(f"❌ 実行エラー: {e}")

    # --- 2. KICK コマンド ---
    @app_commands.command(name="kick", description="対象ユーザーをサーバーから蹴り出します")
    @app_commands.describe(
        target="蹴り出すユーザー", 
        reason="理由",
        mode="結果の表示モード（デフォルト: 自分のみ）"
    )
    @app_commands.choices(mode=mode_choices)
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, it: discord.Interaction, target: discord.Member, reason: str = "理由なし", mode: app_commands.Choice[int] = None):
        is_ephemeral = True if mode is None or mode.value == 1 else False
        await it.response.defer(ephemeral=is_ephemeral)

        if target.id == it.user.id:
            return await it.followup.send("❌ 自分自身をキックすることはできません。")
        if target.top_role >= it.user.top_role:
            return await it.followup.send("❌ 権限不足: あなたと同等以上の役職を持つユーザーを処置できません。")

        try:
            await target.kick(reason=f"執行者: {it.user} | 理由: {reason}")
            
            embed = discord.Embed(title="👢 執行報告: KICK", color=0xFFAA00)
            embed.add_field(name="対象者", value=f"{target.mention} (`{target.id}`)", inline=False)
            embed.add_field(name="理由", value=reason, inline=False)
            embed.set_footer(text=f"執行時刻: {self.get_now_jst()}")
            
            await it.followup.send(embed=embed)
        except Exception as e:
            await it.followup.send(f"❌ 実行エラー: {e}")

    # --- 3. TIMEOUT コマンド ---
    @app_commands.command(name="timeout", description="対象ユーザーを一定時間、発言禁止にします")
    @app_commands.describe(
        target="対象ユーザー", 
        minutes="禁止する分数（1〜40320分）", 
        reason="理由",
        mode="結果の表示モード（デフォルト: 自分のみ）"
    )
    @app_commands.choices(mode=mode_choices)
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timeout(self, it: discord.Interaction, target: discord.Member, minutes: int, reason: str = "理由なし", mode: app_commands.Choice[int] = None):
        is_ephemeral = True if mode is None or mode.value == 1 else False
        await it.response.defer(ephemeral=is_ephemeral)

        if target.id == it.user.id:
            return await it.followup.send("❌ 自分自身をタイムアウトさせることはできません。")
        if target.top_role >= it.user.top_role:
            return await it.followup.send("❌ 権限不足: あなたと同等以上の役職を持つユーザーを処置できません。")
        if not (1 <= minutes <= 40320):
            return await it.followup.send("❌ 分数は1分から28日（40320分）の間で指定してください。")

        try:
            duration = timedelta(minutes=minutes)
            await target.timeout(duration, reason=f"執行者: {it.user} | 理由: {reason}")
            
            embed = discord.Embed(title="🔇 執行報告: TIMEOUT", color=0x5E81AC)
            embed.add_field(name="対象者", value=f"{target.mention} (`{target.id}`)", inline=True)
            embed.add_field(name="期間", value=f"{minutes} 分間", inline=True)
            embed.add_field(name="解除予定", value=f"<t:{int((datetime.now() + duration).timestamp())}:R>", inline=False)
            embed.add_field(name="理由", value=reason, inline=False)
            embed.set_footer(text=f"執行時刻: {self.get_now_jst()}")
            
            await it.followup.send(embed=embed)
        except Exception as e:
            await it.followup.send(f"❌ 実行エラー: {e}")

    # --- 権限エラーハンドリング ---
    @ban.error
    @kick.error
    @timeout.error
    async def mod_error(self, it: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.MissingPermissions):
            await it.response.send_message("❌ 実行権限がありません（メンバーの管理、またはBAN/KICK権限が必要です）。", ephemeral=True)
        else:
            # 既にdeferされている可能性があるため followupを使用
            try:
                await it.followup.send(f"⚠️ エラーが発生しました: {error}", ephemeral=True)
            except:
                await it.response.send_message(f"⚠️ エラーが発生しました: {error}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
