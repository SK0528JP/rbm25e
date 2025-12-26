import discord
from discord.ext import commands
from discord import app_commands
from strings import STRINGS

class Utility(commands.Cog):
    def __init__(self, bot, ledger):
        self.bot = bot
        self.ledger = ledger

    @app_commands.command(name="help", description="System Guide / ヘルプ / Hjälp")
    async def help_command(self, it: discord.Interaction):
        """システムの使用方法を各言語で表示します。"""
        u = self.ledger.get_user(it.user.id)
        lang = u.get("lang", "ja")
        s = STRINGS.get(lang, STRINGS["ja"])

        # 言語別の恒久的な説明文
        guides = {
            "ja": (
                "## 🌿 Rb m/25 インターフェースガイド\n"
                "当システムは北欧モダニズムに基づいた多機能・多言語Botです。\n\n"
                "### 🛠️ 初期設定\n"
                "- `/lang` : 表示言語を日本語、英語、スウェーデン語から選択します。\n"
                "- **貢献度(XP)** : チャットに参加することで3秒ごとに蓄積されます。\n\n"
                "### 📜 主要コマンド\n"
                "- `/status` : 現在の資産額と貢献度を表示します。\n"
                "- `/ranking` : コミュニティ内の上位層を確認します。\n"
                "- `/pay` : 指定したユーザーに資産を送金します。\n"
                "- `/janken` : 娯楽ユニット。勝利すると資産が増加します。\n\n"
                "*不明な点がある場合は管理者までお問い合わせください。*"
            ),
            "en": (
                "## 🌿 Rb m/25 Interface Guide\n"
                "A multi-functional system inspired by Swedish modernism.\n\n"
                "### 🛠️ Configuration\n"
                "- `/lang` : Select your preferred language (JP/EN/SV).\n"
                "- **Experience (XP)** : Earned every 3 seconds by chatting.\n\n"
                "### 📜 Key Commands\n"
                "- `/status` : View your current credits and XP.\n"
                "- `/ranking` : Check the community leaderboards.\n"
                "- `/pay` : Securely transfer credits to other users.\n"
                "- `/janken` : Entertainment unit. Win to increase credits.\n\n"
                "*For further assistance, please contact the administrator.*"
            ),
            "sv": (
                "## 🌿 Rb m/25 Gränssnittsguide\n"
                "Ett multifunktionellt system inspirerat av svensk modernism.\n\n"
                "### 🛠️ Konfiguration\n"
                "- `/lang` : Välj ditt föredragna språk (JP/EN/SV).\n"
                "- **Erfarenhet (XP)** : Tjänas var tredje sekund genom att chatta.\n\n"
                "### 📜 Huvudkommandon\n"
                "- `/status` : Visa dina nuvarande krediter och XP.\n"
                "- `/ranking` : Kontrollera gemenskapens topplistor.\n"
                "- `/pay` : Överför krediter säkert till andra användare.\n"
                "- `/janken` : Underhållningsenhet. Vinn för att öka krediter.\n\n"
                "*För ytterligare hjälp, kontakta administratören.*"
            )
        }

        embed = discord.Embed(
            description=guides.get(lang, guides["en"]),
            color=0x475569 # スレートグレー
        )
        embed.set_author(name=f"{s['system_name']} | Support", icon_url=self.bot.user.display_avatar.url)
        embed.set_footer(text=s["footer_infra"])

        # ephemeral=True で実行者本人にのみ表示
        await it.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="status", description="Check profile / プロフィール照会 / Visa profil")
    async def status(self, it: discord.Interaction):
        """ユーザーの資産と貢献度を表示します。"""
        u = self.ledger.get_user(it.user.id)
        lang = u.get("lang", "ja")
        s = STRINGS.get(lang, STRINGS["ja"])

        embed = discord.Embed(color=0xf8fafc)
        embed.set_author(name=f"{it.user.display_name}", icon_url=it.user.display_avatar.url)
        
        stats_val = f"💰 **{s['status_credit']}**: {u['money']:,} cr\n✨ **{s['status_xp']}**: {u['xp']:,} XP"
        embed.add_field(name=s["status_title"], value=stats_val, inline=False)
        
        embed.set_footer(text=f"{s['footer_infra']} | Active: {u.get('last_active', 'N/A')}")
        await it.response.send_message(embed=embed)

    @app_commands.command(name="lang", description="Set language / 言語設定 / Ställ in språk")
    @app_commands.choices(language=[
        app_commands.Choice(name="日本語 (Japanese)", value="ja"),
        app_commands.Choice(name="English", value="en"),
        app_commands.Choice(name="Svenska (Swedish)", value="sv"),
    ])
    async def set_lang(self, it: discord.Interaction, language: app_commands.Choice[str]):
        """ユーザーの言語設定を保存します。"""
        u = self.ledger.get_user(it.user.id)
        u["lang"] = language.value
        self.ledger.save()
        
        msg = STRINGS[language.value]["lang_updated"]
        embed = discord.Embed(description=f"✅ {msg}", color=0x88a096)
        await it.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="ping", description="Check latency / 応答速度 / Latens")
    async def ping(self, it: discord.Interaction):
        """システムの応答速度を表示します。"""
        latency = round(self.bot.latency * 1000)
        await it.response.send_message(f"📡 **Latency**: `{latency}ms`", ephemeral=True)

async def setup(bot):
    from __main__ import ledger_instance
    await bot.add_cog(Utility(bot, ledger_instance))
