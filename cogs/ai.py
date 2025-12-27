import discord
from discord import app_commands
from discord.ext import commands
import google.generativeai as genai
import os
import aiohttp
import re

class AIChat(commands.Cog):
    # --- 重要：コマンドグループの定義 ---
    # クラスの直下で定義することで、自動的に /ai がツリーに登録されます
    ai_group = app_commands.Group(name="ai", description="Gemini知能中枢による支援機能")

    def __init__(self, bot):
        self.bot = bot
        self.api_key = os.getenv("GEMINI_API_KEY")
        
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None

    async def generate_response(self, contents):
        if not self.model:
            return "❌ APIキーが未設定です。"
        try:
            response = await self.model.generate_content_async(contents)
            if response and response.text:
                return response.text
            return "⚠️ 回答を生成できませんでした。"
        except Exception as e:
            return f"⚠️ 接続エラー: {str(e)}"

    # --- グループ内コマンド ---
    @ai_group.command(name="ask", description="テキストで質問します")
    @app_commands.describe(prompt="質問内容")
    async def ask(self, interaction: discord.Interaction, prompt: str):
        await interaction.response.defer()
        answer = await self.generate_response(prompt)
        await interaction.followup.send(f"🤖 **AI回答:**\n{answer[:1900]}")

    @ai_group.command(name="image", description="画像を解析します")
    @app_commands.describe(attachment="画像ファイル", prompt="質問（任意）")
    async def image(self, interaction: discord.Interaction, attachment: discord.Attachment, prompt: str = "この画像について説明してください"):
        await interaction.response.defer()
        if not attachment.content_type.startswith('image/'):
            return await interaction.followup.send("❌ 画像ファイルを添付してください。")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(attachment.url) as resp:
                    image_data = await resp.read()

            contents = [{"mime_type": attachment.content_type, "data": image_data}, prompt]
            answer = await self.generate_response(contents)
            await interaction.followup.send(f"🤖 **解析結果:**\n{answer[:1900]}")
        except Exception as e:
            await interaction.followup.send(f"⚠️ 解析エラー: {str(e)}")

    # --- メンション応答 ---
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot: return
        if self.bot.user in message.mentions or (message.reference and message.reference.resolved and message.reference.resolved.author.id == self.bot.user.id):
            clean_content = re.sub(f'<@!?{self.bot.user.id}>', '', message.content).strip()
            if not clean_content: return
            async with message.channel.typing():
                answer = await self.generate_response(clean_content)
                await message.reply(answer[:2000])

async def setup(bot):
    await bot.add_cog(AIChat(bot))
