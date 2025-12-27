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

    # --- 重要：コマンドグループの定義と登録 ---
    # app_commands.Group を直接定義
    ai_group = app_commands.Group(name="ai", description="Gemini知能中枢による支援機能")

    async def generate_content_async(self, contents):
        if not self.model:
            return "❌ Gemini APIキーが未設定です。"
        try:
            response = await self.model.generate_content_async(contents)
            return response.text if response.text else "⚠️ 回答を生成できませんでした。"
        except Exception as e:
            return f"⚠️ エラー発生: {str(e)}"

    # グループ内にコマンドを配置
    @ai_group.command(name="ask", description="Geminiに質問します（テキスト）")
    @app_commands.describe(prompt="質問内容")
    async def ask(self, interaction: discord.Interaction, prompt: str):
        await interaction.response.defer()
        answer = await self.generate_content_async(prompt)
        if len(answer) > 2000: answer = answer[:1990] + "..."
        await interaction.followup.send(f"🤖 **AI回答:**\n{answer}")

    @ai_group.command(name="image", description="画像を解析します")
    @app_commands.describe(attachment="画像ファイル", prompt="質問（任意）")
    async def image(self, interaction: discord.Interaction, attachment: discord.Attachment, prompt: str = "この画像について説明してください"):
        await interaction.response.defer()
        if not attachment.content_type or not attachment.content_type.startswith('image/'):
            return await interaction.followup.send("❌ 画像を選択してください。", ephemeral=True)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(attachment.url) as resp:
                    if resp.status != 200: return await interaction.followup.send("❌ 取得失敗")
                    image_data = await resp.read()

            image_part = {"mime_type": attachment.content_type, "data": image_data}
            answer = await self.generate_content_async([image_part, prompt])
            if len(answer) > 2000: answer = answer[:1990] + "..."
            await interaction.followup.send(f"🤖 **画像解析結果:**\n{answer}")
        except Exception as e:
            await interaction.followup.send(f"❌ エラー: {str(e)}")

    # メンション応答はそのまま維持
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot: return
        is_mentioned = self.bot.user in message.mentions
        is_reply = message.reference and message.reference.resolved and message.reference.resolved.author.id == self.bot.user.id
        if is_mentioned or is_reply:
            clean_content = re.sub(f'<@!?{self.bot.user.id}>', '', message.content).strip()
            if not clean_content: return await message.reply("📡 何かお手伝いしましょうか？")
            async with message.channel.typing():
                answer = await self.generate_content_async(clean_content)
                await message.reply(answer[:2000])

async def setup(bot):
    await bot.add_cog(AIChat(bot))
