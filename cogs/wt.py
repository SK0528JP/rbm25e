import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import asyncio

# 定数
COUNTRIES = {
    "usa": "🇺🇸 USA", "germany": "🇩🇪 Germany", "ussr": "🇷🇺 USSR",
    "britain": "🇬🇧 Britain", "japan": "🇯🇵 Japan", "china": "🇨🇳 China",
    "italy": "🇮🇹 Italy", "france": "🇫🇷 France", "sweden": "🇸🇪 Sweden", "israel": "🇮🇱 Israel"
}
CATEGORIES = {
    "tanks": "🚜 陸上兵器", "planes": "✈️ 航空機", 
    "ships": "🚢 艦艇", "helicopters": "🚁 ヘリコプター"
}

class WarThunder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_base = "https://www.wtvehiclesapi.repository.guru/api/vehicles"

    @app_commands.command(name="wt", description="War Thunder兵器カタログ")
    @app_commands.describe(country="国家を選択", category="兵器カテゴリを選択")
    @app_commands.choices(
        country=[app_commands.Choice(name=v, value=k) for k, v in COUNTRIES.items()],
        category=[app_commands.Choice(name=v, value=k) for k, v in CATEGORIES.items()]
    )
    async def wt(self, interaction: discord.Interaction, country: str, category: str):
        # 1. まず即座に応答を返し、「処理中」の状態にする（これで3秒ルールを突破）
        await interaction.response.send_message(f"📡 {COUNTRIES[country]} の {CATEGORIES[category]} データを照会中... 少々お待ちください。", ephemeral=True)
        
        # 2. 通信処理を開始
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{self.api_base}/{category}", timeout=15) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        # 指定国家の兵器だけ抽出
                        filtered = {k: v for k, v in data.items() if v.get('country') == country}
                        
                        if not filtered:
                            return await interaction.edit_original_response(content=f"❌ {COUNTRIES[country]} の {CATEGORIES[category]} データは見つかりませんでした。")
                        
                        # セレクトメニューを作成
                        options = []
                        for v_id, v_info in list(filtered.items())[:25]:
                            name = v_info.get('name', v_id)[:50]
                            options.append(discord.SelectOption(label=name, value=v_id))
                        
                        view = discord.ui.View()
                        select = discord.ui.Select(placeholder="具体的な兵器を選択してください...", options=options)
                        
                        async def select_callback(it: discord.Interaction):
                            await it.response.defer()
                            veh_id = select.values[0]
                            res = data.get(veh_id)
                            if res:
                                embed = discord.Embed(title=f"📊 {res.get('name', veh_id)}", color=0x2ecc71)
                                embed.add_field(name="BR", value=res.get('br', '??'), inline=True)
                                embed.add_field(name="Rank", value=res.get('rank', '??'), inline=True)
                                embed.add_field(name="Country", value=res.get('country', '??').upper(), inline=True)
                                if 'image_url' in res:
                                    embed.set_image(url=res['image_url'])
                                await it.followup.send(embed=embed)

                        select.callback = select_callback
                        view.add_item(select)
                        
                        # 3. 処理が終わったら、最初のメッセージを書き換えてUIを表示
                        await interaction.edit_original_response(content=f"✅ 照会完了。{COUNTRIES[country]} {CATEGORIES[category]} リスト:", view=view)
                    else:
                        await interaction.edit_original_response(content="⚠️ APIサーバーから応答がありませんでした。")
            except Exception as e:
                await interaction.edit_original_response(content=f"⚠️ 通信中にエラーが発生しました。")

async def setup(bot):
    await bot.add_cog(WarThunder(bot))
