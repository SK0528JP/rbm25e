import discord
from discord import app_commands
from discord.ext import commands
import aiohttp

COUNTRIES = {
    "usa": "🇺🇸 USA", "germany": "🇩🇪 Germany", "ussr": "🇷🇺 USSR",
    "britain": "🇬🇧 Britain", "japan": "🇯🇵 Japan", "china": "🇨🇳 China",
    "italy": "🇮🇹 Italy", "france": "🇫🇷 France", "sweden": "🇸🇪 Sweden", "israel": "🇮🇱 Israel"
}
CATEGORIES = {
    "tanks": "🚜 陸上兵器", "planes": "✈️ 航空機", 
    "ships": "🚢 艦艇", "helicopters": "🚁 ヘリコプター"
}

class WTVehicleSelect(discord.ui.Select):
    def __init__(self, options):
        super().__init__(placeholder="調査する兵器を選択してください...", options=options)

    async def callback(self, interaction: discord.Interaction):
        # 1. まず即座に応答（defer）して3秒ルールを回避
        await interaction.response.defer()
        
        v_id = self.values[0]
        url = "https://www.wtvehiclesapi.repository.guru/api/vehicles/all"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        res = data.get(v_id)
                        if res:
                            embed = discord.Embed(
                                title=f"📊 兵器データ: {res.get('name', v_id)}",
                                color=discord.Color.gold()
                            )
                            embed.add_field(name="国家", value=res.get('country', '不明').upper(), inline=True)
                            embed.add_field(name="BR", value=res.get('br', '不明'), inline=True)
                            if 'image_url' in res:
                                embed.set_image(url=res['image_url'])
                            # 2. followup.send で後から結果を送信
                            return await interaction.followup.send(embed=embed)
            except Exception as e:
                return await interaction.followup.send(f"⚠️ 通信エラー: {e}")
        await interaction.followup.send("❌ データの取得に失敗しました。")

class WarThunder(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_base = "https://www.wtvehiclesapi.repository.guru/api/vehicles"

    @app_commands.command(name="wt", description="War Thunder兵器カタログを閲覧します")
    async def wt(self, interaction: discord.Interaction):
        # 最初のコマンド実行時に defer は不要（即座にViewを出すため）
        view = discord.ui.View(timeout=60)
        select = discord.ui.Select(placeholder="国家を選択してください...")
        for code, label in COUNTRIES.items():
            select.add_item(discord.SelectOption(label=label, value=code))

        async def country_callback(it: discord.Interaction):
            # 重要：ボタンを出す前に、この操作に対して「考え中」の状態を作る
            await it.response.defer(ephemeral=True)
            
            country_code = select.values[0]
            cat_view = discord.ui.View(timeout=60)
            
            for cat_id, cat_label in CATEGORIES.items():
                button = discord.ui.Button(label=cat_label, custom_id=f"{country_code}_{cat_id}")
                
                async def btn_callback(btn_it: discord.Interaction):
                    # 重要：ボタンクリックに対しても即座に defer
                    await btn_it.response.defer(ephemeral=True)
                    
                    c_code, c_id = btn_it.data['custom_id'].split('_')
                    async with aiohttp.ClientSession() as session:
                        async with session.get(f"{self.api_base}/{c_id}", timeout=10) as resp:
                            if resp.status == 200:
                                data = await resp.json()
                                filtered = {k: v for k, v in data.items() if v.get('country') == c_code}
                                if not filtered:
                                    return await btn_it.followup.send(f"❌ データなし")
                                
                                # 兵器リストを表示
                                options = []
                                for v_id, v_info in list(filtered.items())[:25]:
                                    name = v_info.get('name', v_id)[:50]
                                    options.append(discord.SelectOption(label=name, value=v_id))
                                
                                next_view = discord.ui.View()
                                next_view.add_item(WTVehicleSelect(options))
                                await btn_it.followup.send(f"📂 {COUNTRIES[c_code]} リスト:", view=next_view)
                
                button.callback = btn_callback
                cat_view.add_item(button)
            
            await it.followup.send(f"📍 カテゴリを選択してください。", view=cat_view)

        select.callback = country_callback
        view.add_item(select)
        await interaction.response.send_message("🛠️ **Rb m/25E 戦術データベース**", view=view)

async def setup(bot):
    await bot.add_cog(WarThunder(bot))
