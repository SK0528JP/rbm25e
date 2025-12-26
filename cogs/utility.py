import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
from strings import STRINGS

class Utility(commands.Cog):
    def __init__(self, bot, ledger):
        self.bot = bot
        self.ledger = ledger

    @app_commands.command(name="lang", description="Set system language / 言語設定 / Ställ in språk")
    @app_commands.choices(language=[
        app_commands.Choice(name="日本語 (Japanese)", value="ja"),
        app_commands.Choice(name="English", value="en"),
        app_commands.Choice(name="Svenska (Swedish)", value="sv"),
    ])
    async def set_lang(self, it: discord.Interaction, language: app_commands.Choice[str]):
        """ユーザーの優先言語を更新します。"""
        u = self.ledger.get_user(it.user.id)
        u["lang"] = language.value
        self.ledger.save()
        
        lang = language.value
        msg = STRINGS[lang]["lang_updated"]
        
        embed = discord.Embed(description=f"✅ {msg}", color=0x88a096)
        embed.set_footer(text=STRINGS[lang]["footer_infra"])
        await it.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="status", description="Check your profile / プロフィール照会 / Visa profil")
    async def status(self, it: discord.Interaction):
        """ユーザー自身の資産と貢献度を表示します。"""
        u = self.ledger.get_user(it.user.id)
        lang = u.get("lang", "ja")
        s = STRINGS[lang]
        
        embed = discord.Embed(color=0xf8fafc)
        embed.set_author(name=f"{it.user.display_name} - {s['status_title']}", icon_url=it.user.display_avatar.url)
        
        # 統計情報を構造化して表示
        stats_val = f"💰 {s['status_credit']}: {u['money']:,}\n✨ {s['status_xp']}: {u['xp']:,}"
        embed.add_field(name="Statistics", value=f"```\n{stats_val}\n```", inline=False)
        
        # 最終アクティブ時間
        embed.set_footer(text=f"{s['footer_infra']} | Last Active: {u.get('last_active', 'N/A')}")
        await it.response.send_message(embed=embed)

    @app_commands.command(name="ping", description="Check system latency / 応答速度確認 / Kontrollera latens")
    async def ping(self, it: discord.Interaction):
        """システムの応答速度を表示します。"""
        u = self.ledger.get_user(it.user.id)
        lang = u.get("lang", "ja")
        s = STRINGS[lang]
        
        latency = round(self.bot.latency * 1000)
        embed = discord.Embed(title="System Status", color=0x88a096)
        
        # 言語に応じたメッセージ
        desc = {
            "ja": f"📡 接続状況は良好です。\n応答速度: `{latency}ms`",
            "en": f"📡 Connection is stable.\nLatency: `{latency}ms`",
            "sv": f"📡 Anslutningen är stabil.\nLatens: `{latency}ms`"
        }
        
        embed.description = desc.get(lang, desc["en"])
        embed.set_footer(text=s["footer_infra"])
        await it.response.send_message(embed=embed)

    @app_commands.command(name="help", description="System guide / ヘルプ / Hjälp")
    async def help_command(self, it: discord.Interaction):
        """利用可能なコマンドのリストを表示します。"""
        u = self.ledger.get_user(it.user.id)
        lang = u.get("lang", "ja")
        s = STRINGS[lang]
        
        embed = discord.Embed(title=f"{s['system_name']} Guide", color=0x475569)
        
        # カテゴリ表示（簡潔に維持）
        menu = {
            "ja": [("🔍 情報", "`/status` `/ping` `/lang`"), ("💳 経済", "`/pay` `/exchange` `/ranking`"), ("🎮 娯楽", "`/janken` `/omikuji`")],
            "en": [("🔍 Info", "`/status` `/ping` `/lang`"), ("💳 Finance", "`/pay` `/exchange` `/ranking`"), ("🎮 Fun", "`/janken` `/omikuji`")],
            "sv": [("🔍 Info", "`/status` `/ping` `/lang`"), ("💳 Ekonomi", "`/pay` `/utbyte` `/rankning`"), ("🎮 Nöje", "`/janken` `/omikuji`")]
        }
        
        for name, cmds in menu.get(lang, menu["en"]):
            embed.add_field(name=name, value=cmds, inline=True)
            
        embed.set_footer(text=s["footer_infra"])
        await it.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    # main.py の load_extension で呼び出されるための処理
    from main import ledger
    await bot.add_cog(Utility(bot, ledger))
