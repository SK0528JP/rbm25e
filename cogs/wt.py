import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import asyncio

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
        # サーバーに拒否されないためのブラウザ偽装
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        }

    @app_commands.command(name="wt", description="War Thunder兵器カタログ")
    @app_commands.describe(country="国家を選択", category="兵器カテゴリを選択")
    @app_commands.choices(
        country=[app_commands.Choice(name=v, value=k) for k, v in COUNTRIES.items()],
        category=[app_commands.Choice(name=v, value=k) for k, v in CATEGORIES.items()]
    )
    async def wt(self, interaction: discord.Interaction, country: str, category: str):
        # 1. 即座に応答
        await interaction.response.send_message(f"📡 {COUNTRIES[country]} の {CATEGORIES[category]} データを取得中...", ephemeral=True)
        
        url = f"{self.api_base}/{category}"
        data = None

        # 2. 最大3回のリトライ処理
        async with aiohttp.ClientSession(headers=self.headers) as session:
            for attempt in range(3):
                try:
                    async with session.get(url, timeout=15) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            break
                        elif resp.status == 429: # Too Many Requests
                            await asyncio.sleep(2) # 少し待ってリトライ
                        else:
                            continue
                except Exception:
                    await asyncio.sleep(1)
                    continue

        if not data:
            return await interaction.edit_original_response(content="⚠️ サーバーが応答しませんでした。時間を置いて試してください。")

        # 3. フィルタリングとUI構築
        filtered = {k: v for k, v in data.items() if v.get('country') == country}
        if not filtered:
            return await interaction.edit_original_response(content=f"❌ {COUNTRIES[country]} のデータは見つかりませんでした。")

        options = []
        for v_id, v_info in list(filtered.items())[:25]:
            name = v_info.get('name', v_id)[:50]
            options.append(discord.SelectOption(label=name, value=v_id))
        
        view = discord.ui.View()
        select = discord.ui.Select(placeholder="具体的な兵器を選択してください...", options=options)

        async def select_callback(it: discord.Interaction):
            await it.response.defer()
            res = data.get(select.values[0])
            if res:
                embed = discord.Embed(title=f"📊 {res.get('name', '??')}", color=0x2ecc71)
                embed.add_field(name="BR", value=res.get('br', '??'), inline=True)
                embed.add_field(name="Rank", value=res.get('rank', '??'), inline=True)
                if 'image_url' in res:
                    embed.set_image(url=res['image_url'])
                await it.followup.send(embed=embed)

        select.callback = select_callback
        view.add_item(select)
        
        await interaction.edit_original_response(content=f"✅ 取得完了。{COUNTRIES[country]} リスト:", view=view)

async def setup(bot):
    await bot.add_cog(WarThunder(bot))
