import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime

class Gallery(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="img_save", description="画像を名前をつけて保存します（画像を添付してください）")
    @app_commands.describe(name="保存する際の名前")
    async def img_save(self, interaction: discord.Interaction, name: str, attachment: discord.Attachment):
        await interaction.response.defer()

        # 画像かどうかチェック
        if not attachment.content_type or not attachment.content_type.startswith("image"):
            await interaction.followup.send("❌ 画像ファイルを添付してください。")
            return

        if not self.bot.ledger:
            await interaction.followup.send("❌ Ledgerが有効ではありません。")
            return

        # Ledgerに保存（全ユーザー共通のギャラリーにする場合）
        if "image_gallery" not in self.bot.ledger.data:
            self.bot.ledger.data["image_gallery"] = {}
        
        # 既に名前が存在するかチェック
        if name in self.bot.ledger.data["image_gallery"]:
            await interaction.followup.send(f"⚠️ 名前 `{name}` は既に使われています。別の名前にするか、削除してから保存してください。")
            return

        # 保存
        self.bot.ledger.data["image_gallery"][name] = attachment.url
        self.bot.ledger.save()

        embed = discord.Embed(
            title="📸 画像保存完了",
            description=f"名前: **{name}** で保存しました。",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=attachment.url)
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="img_load", description="保存された画像を名前で呼び出します")
    async def img_load(self, interaction: discord.Interaction, name: str):
        gallery = self.bot.ledger.data.get("image_gallery", {})
        url = gallery.get(name)

        if not url:
            await interaction.response.send_message(f"❌ 名前 `{name}` に紐づく画像は見つかりませんでした。", ephemeral=True)
            return

        embed = discord.Embed(title=f"🖼️ {name}", color=discord.Color.green())
        embed.set_image(url=url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="img_del", description="保存された画像を削除します")
    async def img_del(self, interaction: discord.Interaction, name: str):
        gallery = self.bot.ledger.data.get("image_gallery", {})
        
        if name in gallery:
            del self.bot.ledger.data["image_gallery"][name]
            self.bot.ledger.save()
            await interaction.response.send_message(f"✅ 画像 `{name}` を削除しました。")
        else:
            await interaction.response.send_message(f"❌ 名前 `{name}` は存在しません。", ephemeral=True)

    @app_commands.command(name="img_list", description="保存されている画像名の一覧を表示します")
    async def img_list(self, interaction: discord.Interaction):
        gallery = self.bot.ledger.data.get("image_gallery", {})
        
        if not gallery:
            await interaction.response.send_message("📁 ギャラリーは現在空です。")
            return

        names = "\n".join([f"・ {n}" for n in gallery.keys()])
        embed = discord.Embed(
            title="📁 保存済み画像一覧",
            description=names,
            color=discord.Color.light_grey()
        )
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Gallery(bot))
