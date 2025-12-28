import discord
from discord import app_commands
from discord.ext import commands
import aiohttp

class WarThunder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 新しいAPIのベースURL
        self.base_url = "https://www.wtvehiclesapi.sgambe.serv00.net/api/v1"

    @app_commands.command(name="wt", description="War Thunder兵器データベース検索")
    @app_commands.describe(name="検索したい兵器名（例: tiger, m1 abrams, a6m）")
    async def wt(self, interaction: discord.Interaction, name: str):
        # 1. 3秒ルール回避のため即座に応答（考え中...を表示）
        await interaction.response.defer()

        # 2. 新APIの検索エンドポイントを使用
        # パラメータで絞り込むため、通信量が極めて少なくなります
        search_url = f"{self.base_url}/vehicles/search"
        params = {"name": name}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(search_url, params=params, timeout=10) as resp:
                    if resp.status == 200:
                        results = await resp.json()
                        
                        if not results:
                            return await interaction.followup.send(f"❌ `{name}` に一致する兵器は見つかりませんでした。")

                        # 複数ヒットした場合は最初の1件を表示（あるいはリスト化）
                        # このAPIはリストで返ってくるため、0番目を取得
                        data = results[0]
                        
                        embed = discord.Embed(
                            title=f"📊 兵器データ: {data.get('name')}",
                            color=discord.Color.blue()
                        )
                        
                        # APIのフィールド名に合わせて抽出
                        embed.add_field(name="国家", value=data.get('country', '不明').upper(), inline=True)
                        embed.add_field(name="BR", value=data.get('br', '不明'), inline=True)
                        embed.add_field(name="ランク", value=data.get('rank', '不明'), inline=True)
                        embed.add_field(name="タイプ", value=data.get('type', '不明'), inline=True)

                        # 画像URLの処理
                        if data.get('image_url'):
                            embed.set_image(url=data['image_url'])

                        embed.set_footer(text=f"ID: {data.get('identifier')} | Rb m/25E Data Terminal")
                        
                        await interaction.followup.send(embed=embed)
                    else:
                        await interaction.followup.send(f"⚠️ APIエラー (Status: {resp.status})")
        except Exception as e:
            await interaction.followup.send(f"⚠️ 通信に失敗しました。APIが一時的にオフラインの可能性があります。")

async def setup(bot):
    await bot.add_cog(WarThunder(bot))
