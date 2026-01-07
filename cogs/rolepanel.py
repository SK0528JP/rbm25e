import discord
from discord.ext import commands
from discord import app_commands
import traceback

# --- 定数設定 ---
CUSTOM_ID_PREFIX = "rb_role:"

class RolePanel(commands.GroupCog, name="panel"):
    def __init__(self, bot):
        self.bot = bot

    # =========================================================================
    # ⚙️ コアシステム: ボタン検知リスナー (永続化の要)
    # =========================================================================
    @commands.Cog.listener()
    async def on_interaction(self, it: discord.Interaction):
        """
        Bot再起動後もボタンが機能するように、Viewクラスではなく
        グローバルなインタラクションイベントでボタン押下を検知します。
        """
        # ボタン、かつIDがこの機能のもの（rb_role:）でなければ無視
        if it.type != discord.InteractionType.component:
            return
        
        custom_id = it.data.get("custom_id", "")
        if not custom_id.startswith(CUSTOM_ID_PREFIX):
            return

        # --- ロール付与・解除処理 ---
        try:
            role_id = int(custom_id.split(":")[1])
            role = it.guild.get_role(role_id)

            if not role:
                # ロールがサーバーから削除されていた場合の処理
                await it.response.send_message("❌ エラー: このロールは既にサーバーから削除されています。", ephemeral=True)
                return

            # Botの権限チェック
            if role >= it.guild.me.top_role:
                await it.response.send_message("❌ エラー: Botの役職より上位のロールは操作できません。", ephemeral=True)
                return

            # 付与/解除トグル
            if role in it.user.roles:
                await it.user.remove_roles(role, reason="RolePanel: User requested removal")
                await it.response.send_message(f"✅ **{role.name}** を解除しました。", ephemeral=True)
            else:
                await it.user.add_roles(role, reason="RolePanel: User requested add")
                await it.response.send_message(f"✅ **{role.name}** を付与しました。", ephemeral=True)

        except discord.Forbidden:
            await it.response.send_message("❌ エラー: 権限不足です。Botに「ロールの管理」権限があるか確認してください。", ephemeral=True)
        except Exception as e:
            print(f"RolePanel Error: {e}")
            await it.response.send_message("❌ 予期せぬエラーが発生しました。", ephemeral=True)

    # =========================================================================
    # 🛠️ コマンドセクション
    # =========================================================================

    # --- 1. パネル作成 (Create) ---
    @app_commands.command(name="create", description="新しいロールパネル（メッセージ）を作成します")
    @app_commands.describe(title="パネルのタイトル", description="説明文", color="埋め込みの色(HEXコードなど、任意)")
    @app_commands.checks.has_permissions(administrator=True)
    async def create(self, it: discord.Interaction, title: str, description: str, color: int = 0x5E81AC):
        embed = discord.Embed(title=title, description=description, color=color)
        embed.set_footer(text="Bot by Rb m/25E Design Bureau")
        
        await it.response.send_message("✅ パネルの土台を作成しました。", ephemeral=True)
        await it.channel.send(embed=embed)

    # --- 2. ボタン追加 (Add) ---
    @app_commands.command(name="add", description="指定したパネルにロールボタンを追加します")
    @app_commands.describe(
        message_id="対象パネルのメッセージID",
        role="追加するロール",
        label="ボタンの表示名（未指定ならロール名）",
        style="ボタンの色"
    )
    @app_commands.choices(style=[
        app_commands.Choice(name="Blurple (青)", value=1),
        app_commands.Choice(name="Grey (灰)", value=2),
        app_commands.Choice(name="Green (緑)", value=3),
        app_commands.Choice(name="Red (赤)", value=4)
    ])
    @app_commands.checks.has_permissions(administrator=True)
    async def add_role(self, it: discord.Interaction, message_id: str, role: discord.Role, label: str = None, style: int = 1):
        # メッセージ取得チェック
        try:
            msg = await it.channel.fetch_message(int(message_id))
        except:
            return await it.response.send_message("❌ メッセージが見つかりません。IDを確認してください。", ephemeral=True)

        if msg.author.id != self.bot.user.id:
            return await it.response.send_message("❌ Botが送信したメッセージ以外は編集できません。", ephemeral=True)

        # 安全装置: 上位ロール対策
        if role >= it.guild.me.top_role:
            return await it.response.send_message("❌ Botより上位のロール、またはBotと同じ順位のロールは追加できません。", ephemeral=True)

        # View再構築ロジック
        view = discord.ui.View(timeout=None)
        
        # 既存ボタンの引き継ぎ
        existing_count = 0
        target_custom_id = f"{CUSTOM_ID_PREFIX}{role.id}"
        
        if msg.components:
            for component in msg.components:
                if isinstance(component, discord.components.ActionRow):
                    for child in component.children:
                        if child.custom_id == target_custom_id:
                            continue # 既に同じロールがある場合はスキップ（上書きのため）
                        
                        # 古いボタンをそのままコピー
                        new_btn = discord.ui.Button(
                            style=child.style,
                            label=child.label,
                            custom_id=child.custom_id,
                            emoji=child.emoji,
                            disabled=child.disabled
                        )
                        view.add_item(new_btn)
                        existing_count += 1
        
        if existing_count >= 25:
            return await it.response.send_message("❌ ボタンの数が上限（25個）に達しています。", ephemeral=True)

        # 新規ボタン作成
        new_button = discord.ui.Button(
            style=discord.ButtonStyle(style),
            label=label if label else role.name,
            custom_id=target_custom_id
        )
        view.add_item(new_button)

        await msg.edit(view=view)
        await it.response.send_message(f"✅ パネルに **{role.name}** を追加しました。", ephemeral=True)

    # --- 3. ボタン削除 (Remove) ---
    @app_commands.command(name="remove", description="指定したパネルからロールボタンを削除します")
    @app_commands.describe(message_id="対象パネルのメッセージID", role="削除するロール")
    @app_commands.checks.has_permissions(administrator=True)
    async def remove_role(self, it: discord.Interaction, message_id: str, role: discord.Role):
        try:
            msg = await it.channel.fetch_message(int(message_id))
        except:
            return await it.response.send_message("❌ メッセージが見つかりません。", ephemeral=True)

        if msg.author.id != self.bot.user.id:
            return await it.response.send_message("❌ Botが送信したメッセージ以外は編集できません。", ephemeral=True)

        view = discord.ui.View(timeout=None)
        target_custom_id = f"{CUSTOM_ID_PREFIX}{role.id}"
        removed = False

        # 既存ボタンから対象以外を再構築
        if msg.components:
            for component in msg.components:
                for child in component.children:
                    if child.custom_id == target_custom_id:
                        removed = True # 対象を発見、スキップ
                        continue
                    
                    new_btn = discord.ui.Button(
                        style=child.style,
                        label=child.label,
                        custom_id=child.custom_id,
                        emoji=child.emoji
                    )
                    view.add_item(new_btn)

        if not removed:
            return await it.response.send_message(f"⚠️ そのロール ({role.name}) のボタンはこのパネルに見つかりませんでした。", ephemeral=True)

        await msg.edit(view=view)
        await it.response.send_message(f"✅ パネルから **{role.name}** を削除しました。", ephemeral=True)

async def setup(bot):
    await bot.add_cog(RolePanel(bot))
