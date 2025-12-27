import discord
from discord import app_commands
from discord.ext import commands
import google.generativeai as genai
import os
import aiohttp
import re
from io import BytesIO

class AIChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Gemini APIの設定
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None

    # --- スラッシュコマンド：/ai グループの定義 ---
    # ここで Group を作成し、コマンドを追加します
    ai_group = app_commands.Group(name="ai", description="Gemini知能中枢による支援機能")

    async def generate_content_async(self, contents):
        """Gemini APIを使用してコンテンツを生成する共通非同期関数"""
        if not self.model:
            return "❌ Gemini APIキーが設定されていないため、知能中枢が起動していません。"
        
        try:
            response = await self.model.generate_content_async(contents)
            if response.text:
                return response.text
            else:
                return "⚠️ 適切な回答を生成できませんでした。"
        except Exception as e:
            return f"⚠️ 思考回路でエラーが発生しました: {str(e)}"

    @ai_group.command(name="ask", description="Geminiに質問や相談をします（テキストのみ）")
    @app_commands.describe(prompt="質問したい内容")
    async def ask(self, interaction: discord.Interaction, prompt: str):
        """テキストベースの対話コマンド"""
        await interaction.response.defer()
        answer = await self.generate_content_async(prompt)
        
        if len(answer) > 2000:
            answer = answer[:1990] + "..."
        await interaction.followup.send(f"🤖 **AI回答:**\n{answer}")

    @ai_group.command(name="image", description="画像を解析し、その内容について回答します")
    @app_commands.describe(attachment="解析する画像ファイル", prompt="画像について聞きたいこと")
    async def image(self, interaction: discord.Interaction, attachment: discord.Attachment, prompt: str = "この画像について説明してください"):
        """画像+テキストの解析コマンド"""
        await interaction.response.defer()

        if not attachment.content_type or not attachment.content_type.startswith('image/'):
            return await interaction.followup.send("❌ 解析可能な画像ファイルを選択してください。", ephemeral=True)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(attachment.url) as resp:
                    if resp.status != 200:
                        return await interaction.followup.send("❌ 画像データの取得に失敗しました。")
                    image_data = await resp.read()

            image_part = {"mime_type": attachment.content_type, "data": image_data}
            answer = await self.generate_content_async([image_part, prompt])
            
            if len(answer) > 2000:
                answer = answer[:1990] + "..."
            await interaction.followup.send(f"🤖 **画像解析結果:**\n{answer}")
        except Exception as e:
            await interaction.followup.send(f"❌ 解析中にエラーが発生しました: {str(e)}")

    # --- メンション応答機能 ---
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        is_mentioned = self.bot.user in message.mentions
        is_reply_to_bot = (
            message.reference and 
            message.reference.resolved and 
            message.reference.resolved.author.id == self.bot.user.id
        )

        if is_mentioned or is_reply_to_bot:
            clean_content = re.sub(f'<@!?{self.bot.user.id}>', '', message.content).strip()
            
            if not clean_content and is_mentioned:
                await message.reply("📡 何かお手伝いできることはありますか？")
                return

            async with message.channel.typing():
                answer = await self.generate_content_async(clean_content)
                if len(answer) > 2000:
                    answer = answer[:1990] + "..."
                await message.reply(answer)

async def setup(bot):
    await bot.add_cog(AIChat(bot))
