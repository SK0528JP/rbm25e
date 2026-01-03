import discord
from discord.ext import commands
from discord import app_commands

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 公式サイトのURL
        self.doc_url = "https://sk0528jp.github.io/rbm25e/"

    @app_commands.command(name="help", description="Rb m/25E の利用ガイドと公式サイトを表示します")
    async def help_command(self, it: discord.Interaction):
        # 埋め込みメッセージの設定
        embed = discord.Embed(
            title="📖 Rb m/25E 指導書",
            description=(
                "Rb m/25E の各コマンドの詳細な使い方、仕様、および\n"
                "サーバーへの招待については、公式サイトを確認してください。\n\n"
                f"🔗 **[公式サイトを開く]({self.doc_url})**"
            ),
            color=0x4C566A  # 北欧風のスレートグレー
        )
        
        # 視覚的なアクセントとしてBotのアイコンを表示
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(text="Rb m/25E System Operations")

        # 直感的にアクセスできるようボタンを設置
        view = discord.ui.View()
        view.add_item(discord.ui.Button(
            label="公式サイトを表示", 
            url=self.doc_url, 
            style=discord.ButtonStyle.link
        ))

        # 他のユーザーの邪魔にならないよう、実行者にのみ表示（ephemeral）
        await it.response.send_message(embed=embed, view=view, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Help(bot))
