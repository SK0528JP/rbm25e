import discord
from discord.ext import commands
from discord import app_commands
from googletrans import Translator
import asyncio
import functools

class TranslatorCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Translatorのインスタンス初期化
        self.translator = Translator()
        
        # コンテキストメニュー（メッセージを右クリックして翻訳）の定義
        self.ctx_menu = app_commands.ContextMenu(
            name='Rb m/25E: 日本語翻訳',
            callback=self.translate_context_menu,
        )
        
        # アプリインストール設定 (サーバー設置型 & ユーザー設置型)
        # これにより、BotがいないサーバーやDMでも本機能が利用可能になる
        self.ctx_menu.installs(guild=True, user=True)
        self.ctx_menu.contexts(guild=True, dms=True, private_channels=True)

    async def cog_load(self):
        """コグ読み込み時にコマンドを同期ツリーに追加"""
        self.bot.tree.add_command(self.ctx_menu)

    async def cog_unload(self):
        """コグ解除時にコマンドをツリーから削除"""
        self.bot.tree.remove_command(self.ctx_menu.name, type=self.ctx_menu.type)

    async def _perform_translation(self, text: str, dest: str = 'ja'):
        """
        googletransの同期処理を非同期で安全に実行するための内部メソッド。
        GitHub等の共有ネットワーク環境での失敗を考慮し、最大3回のリトライを行う。
        """
        loop = asyncio.get_event_loop()
        last_error = None
        
        for attempt in range(3):
            try:
                # 実行をExecutorに投げてイベントループをブロックさせない
                result = await loop.run_in_executor(
                    None, 
                    functools.partial(self.translator.translate, text, dest=dest)
                )
                return result
            except Exception as e:
                last_error = e
                await asyncio.sleep(1) # 1秒待機してリトライ
        
        raise last_error

    async def translate_context_menu(self, it: discord.Interaction, message: discord.Message):
        """コンテキストメニュー経由の翻訳処理"""
        await it.response.defer(ephemeral=True)

        # 本文のバリデーション
        content = message.content
        if not content or not content.strip():
            return await it.followup.send("❌ 翻訳対象となるテキストが見つかりません。", ephemeral=True)

        try:
            result = await self._perform_translation(content)
            
            embed = discord.Embed(
                title="🌐 翻訳プロトコル解析結果",
                color=0x4C566A,
                description=f"**原文 ({result.src})**:\n```\n{content[:1000]}\n```\n**日本語訳**:\n{result.text}"
            )
            embed.set_footer(text="Rb m/25E Translation Subsystem")
            
            await it.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            await it.followup.send(
                "❌ 翻訳失敗: Google翻訳へのリクエストが拒否されました。\n"
                "短時間での多用を避けるか、しばらく待ってから再試行してください。", 
                ephemeral=True
            )

    @app_commands.command(name="tr", description="任意のテキストを日本語に翻訳します")
    @app_commands.describe(text="翻訳したい文章（他言語）")
    @app_commands.installs(guild=True, user=True)
    @app_commands.contexts(guild=True, dms=True, private_channels=True)
    async def translate_slash(self, it: discord.Interaction, text: str):
        """スラッシュコマンド経由の翻訳処理"""
        await it.response.defer(ephemeral=True)
        
        try:
            result = await self._perform_translation(text)
            await it.followup.send(
                f"**原文**: {text}\n**日本語訳 ({result.src} -> ja)**: {result.text}", 
                ephemeral=True
            )
        except Exception:
            await it.followup.send("❌ 翻訳エラーが発生しました。", ephemeral=True)

async def setup(bot):
    await bot.add_cog(TranslatorCog(bot))
