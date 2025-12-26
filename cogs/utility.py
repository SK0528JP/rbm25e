import discord
from discord.ext import commands
from discord import app_commands
from strings import STRINGS

class Utility(commands.Cog):
    def __init__(self, bot, ledger):
        self.bot = bot
        self.ledger = ledger

    # スラッシュコマンドとして認識させるためのデコレータ
    @app_commands.command(name="lang", description="Set language / 言語設定")
    @app_commands.choices(language=[
        app_commands.Choice(name="日本語", value="ja"),
        app_commands.Choice(name="English", value="en"),
        app_commands.Choice(name="Svenska", value="sv"),
    ])
    async def set_lang(self, it: discord.Interaction, language: app_commands.Choice[str]):
        u = self.ledger.get_user(it.user.id)
        u["lang"] = language.value
        self.ledger.save()
        msg = STRINGS[language.value]["lang_updated"]
        await it.response.send_message(f"✅ {msg}", ephemeral=True)

    @app_commands.command(name="ping", description="Check latency")
    async def ping(self, it: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        await it.response.send_message(f"📡 Latency: {latency}ms")

async def setup(bot):
    from __main__ import ledger_instance
    # ここで add_cog する際、bot.tree に自動的に追加されます
    await bot.add_cog(Utility(bot, ledger_instance))
