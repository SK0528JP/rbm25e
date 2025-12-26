import discord
from discord import app_commands
from discord.ext import commands
import random
import asyncio
from datetime import datetime

class Fishing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # 獲物リスト（名前, 基本価格, サイズ範囲, レア度, 出現の重み）
        # 全体的に価格を抑え、レアリティの重みを厳しく調整
        self.FISH_POOL = [
            # ゴミ (Weights: 25) - ほぼ換金価値なし
            {"name": "長靴", "base_price": 2, "size_range": (20, 30), "rarity": "ゴミ", "weight": 10},
            {"name": "空き缶", "base_price": 1, "size_range": (5, 10), "rarity": "ゴミ", "weight": 10},
            {"name": "ビニール袋", "base_price": 1, "size_range": (30, 50), "rarity": "ゴミ", "weight": 5},

            # 一般 (Weights: 60) - メインの収入源
            {"name": "アジ", "base_price": 15, "size_range": (15, 30), "rarity": "N", "weight": 15},
            {"name": "イワシ", "base_price": 10, "size_range": (10, 25), "rarity": "N", "weight": 15},
            {"name": "サバ", "base_price": 25, "size_range": (25, 45), "rarity": "N", "weight": 10},
            {"name": "キス", "base_price": 12, "size_range": (10, 25), "rarity": "N", "weight": 10},
            {"name": "メバル", "base_price": 20, "size_range": (15, 35), "rarity": "N", "weight": 10},

            # レア (Weights: 12) - ちょっと嬉しい
            {"name": "マダイ", "base_price": 80, "size_range": (30, 90), "rarity": "R", "weight": 4},
            {"name": "クロダイ", "base_price": 70, "size_range": (30, 60), "rarity": "R", "weight": 4},
            {"name": "スズキ", "base_price": 100, "size_range": (50, 100), "rarity": "R", "weight": 3},
            {"name": "アオリイカ", "base_price": 90, "size_range": (20, 50), "rarity": "R", "weight": 1},

            # スーパーレア (Weights: 2.5) - 誇れる釣果
            {"name": "ブリ", "base_price": 350, "size_range": (80, 120), "rarity": "SR", "weight": 1.0},
            {"name": "ホンマグロ", "base_price": 600, "size_range": (150, 300), "rarity": "SR", "weight": 1.0},
            {"name": "クエ", "base_price": 800, "size_range": (60, 130), "rarity": "SR", "weight": 0.5},

            # ウルトラレア・伝説 (Weights: 0.5) - サーバーの英雄レベル
            {"name": "リュウグウノツカイ", "base_price": 2500, "size_range": (300, 700), "rarity": "SSR", "weight": 0.2},
            {"name": "黄金のシャチ", "base_price": 5000, "size_range": (500, 800), "rarity": "SSR", "weight": 0.2},
            {"name": "ポセイドンの三叉槍", "base_price": 12000, "size_range": (200, 210), "rarity": "LEGEND", "weight": 0.05},
            {"name": "古びた宝箱", "base_price": 8000, "size_range": (50, 60), "rarity": "TREASURE", "weight": 0.05},
        ]

    @app_commands.command(name="fishing", description="釣りをします。")
    async def fishing(self, interaction: discord.Interaction):
        await interaction.response.send_message("🎣 釣り糸を垂らしました。アタリを待っています...")
        await asyncio.sleep(random.randint(3, 6))

        weights = [f["weight"] for f in self.FISH_POOL]
        fish_base = random.choices(self.FISH_POOL, weights=weights, k=1)[0]

        size = round(random.uniform(fish_base["size_range"][0], fish_base["size_range"][1]), 1)
        size_multiplier = size / fish_base["size_range"][0]
        price = int(fish_base["base_price"] * size_multiplier)

        user_data = self.bot.ledger.get_user(interaction.user.id)
        if "fishing_inventory" not in user_data:
            user_data["fishing_inventory"] = []
        
        new_item = {
            "name": fish_base["name"],
            "size": size,
            "price": price,
            "rarity": fish_base["rarity"],
            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        user_data["fishing_inventory"].append(new_item)
        self.bot.ledger.save()

        color_map = {
            "ゴミ": discord.Color.dark_gray(),
            "N": discord.Color.blue(),
            "R": discord.Color.green(),
            "SR": discord.Color.purple(),
            "SSR": discord.Color.gold(),
            "LEGEND": discord.Color.from_rgb(255, 0, 0),
            "TREASURE": discord.Color.from_rgb(0, 255, 255)
        }
        color = color_map.get(fish_base["rarity"], discord.Color.default())

        embed = discord.Embed(title="🐟 釣果報告！", color=color)
        embed.add_field(name="獲物", value=f"**{fish_base['name']}**", inline=True)
        embed.add_field(name="サイズ", value=f"**{size} cm**", inline=True)
        embed.add_field(name="推定価値", value=f"**{price} cr**", inline=True)
        embed.add_field(name="レア度", value=fish_base["rarity"], inline=True)
        
        if fish_base["rarity"] in ["SSR", "LEGEND", "TREASURE"]:
            await interaction.edit_original_response(content="🎊 **大物だぁぁぁ！！** 🎊", embed=embed)
        else:
            await interaction.edit_original_response(content=None, embed=embed)

    @app_commands.command(name="fishing_inventory", description="所持している獲物一覧を表示します。")
    async def fishing_inventory(self, interaction: discord.Interaction):
        user_data = self.bot.ledger.get_user(interaction.user.id)
        inventory = user_data.get("fishing_inventory", [])

        if not inventory:
            await interaction.response.send_message("🪣 生け簀は空っぽだ。", ephemeral=True)
            return

        embed = discord.Embed(title=f"🪣 {interaction.user.display_name} の生け簀", color=discord.Color.blue())
        desc = ""
        display_items = inventory[-20:]
        offset = len(inventory) - len(display_items)
        
        for i, item in enumerate(display_items):
            desc += f"`{offset + i}`: **{item['name']}** ({item['size']}cm) / {item['price']} cr\n"
        
        embed.description = desc
        embed.set_footer(text=f"合計所持数: {len(inventory)} 匹")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="fishing_sale", description="獲物を売却してcrを獲得します。")
    @app_commands.describe(target="番号、または 'all' で全売却")
    async def fishing_sale(self, interaction: discord.Interaction, target: str):
        user_data = self.bot.ledger.get_user(interaction.user.id)
        inventory = user_data.get("fishing_inventory", [])

        if not inventory:
            await interaction.response.send_message("❌ 売却するものが何もないぞ。", ephemeral=True)
            return

        if target.lower() == "all":
            total_price = sum(item["price"] for item in inventory)
            count = len(inventory)
            user_data["money"] = user_data.get("money", 0) + total_price
            user_data["fishing_inventory"] = []
            self.bot.ledger.save()
            await interaction.response.send_message(f"💰 **{count}匹** をすべて売却し、**{total_price} cr** を獲得した！")
        else:
            try:
                idx = int(target)
                if 0 <= idx < len(inventory):
                    item = inventory.pop(idx)
                    price = item["price"]
                    user_data["money"] = user_data.get("money", 0) + price
                    self.bot.ledger.save()
                    await interaction.response.send_message(f"💰 **{item['name']}** ({item['size']}cm) を売却し、**{price} cr** を獲得した！")
                else:
                    await interaction.response.send_message("❌ その番号の獲物はいないようだ。", ephemeral=True)
            except ValueError:
                await interaction.response.send_message("❌ 番号を入力するか、'all' と入力してくれ。", ephemeral=True)

    @app_commands.command(name="fishing_ranking", description="大物ランキングを表示します。")
    async def fishing_ranking(self, interaction: discord.Interaction):
        await interaction.response.defer()
        
        all_fish = []
        ledger_data = self.bot.ledger.data
        
        for user_id_str, data in ledger_data.items():
            inventory = data.get("fishing_inventory", [])
            if not inventory:
                continue
            
            try:
                user_id = int(user_id_str)
            except ValueError:
                continue

            for item in inventory:
                all_fish.append({
                    "name": item.get("name", "不明"),
                    "size": item.get("size", 0),
                    "owner_id": user_id
                })

        if not all_fish:
            await interaction.followup.send("🌊 まだこの海に記録はない...")
            return

        all_fish.sort(key=lambda x: x["size"], reverse=True)

        embed = discord.Embed(title="🏆 歴代大物ランキング TOP10", color=discord.Color.gold())
        lines = []
        
        for i, fish in enumerate(all_fish[:10], 1):
            owner_id = fish["owner_id"]
            member = interaction.guild.get_member(owner_id)
            if member:
                display_name = member.display_name
            else:
                user = self.bot.get_user(owner_id)
                display_name = user.display_name if user else f"ユーザー({owner_id})"
            
            medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"`{i}.`"
            lines.append(f"{medal} **{display_name}** - {fish['name']} ({fish['size']} cm)")

        embed.description = "\n".join(lines)
        await interaction.followup.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Fishing(bot))
