import discord
from discord import app_commands
from discord.ext import commands
import google.generativeai as genai
import os
import re
import aiohttp # 画像ダウンロード用
from io import BytesIO # 画像データ処理用

class AIChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.model_text = genai.GenerativeModel('gemini-1.5-flash') # テキスト専用モデル
            self.model_vision = genai.GenerativeModel('gemini-1.5-flash-001') # Vision対応モデル (画像認識に特化)
            
            self.system_instruction = (
                "あなたは『Rb m/25E』という名称の、多機能支援型Discord Botです。"
                "冷静かつ誠実で、少し軍事的な支援AIのような口調で話してください。"
                "ユーザーのことを『司令官』または『ユーザー』と呼び、簡潔に回答してください。"
                "回答の最後に『承知しました、司令官。』や『了解です。』などを添えてください。"
            )
        else:
            self.model_text = None
            self.model_vision = None

    async def generate_text_response(self, prompt: str):
        """テキストプロンプトから回答を生成する共通関数"""
        if not self.model_text:
            return "❌ Gemini APIキーが設定されていないため、知能中枢が起動していません。"
        
        try:
            full_prompt = f"{self.system_instruction}\n\n質問: {prompt}"
            response = await self.model_text.generate_content_async(full_prompt) # 非同期で実行
            
            content = response.text
            if len(content) > 1900:
                content = content[:1900] + "\n...(長文のため以下省略)"
            return content
        except Exception as e:
            return f"⚠️ 思考回路でエラーが発生しました: {str(e)}"

    async def generate_vision_response(self, image_data: BytesIO, prompt: str):
        """画像とテキストプロンプトから回答を生成する関数"""
        if not self.model_vision:
            return "❌ Gemini Vision APIキーが設定されていないか、モデルが起動していません。"
        
        try:
            image_part = {
                'mime_type': 'image/jpeg', # Discordの画像はほぼJPEGかPNG
                'data': image_data.getvalue()
            }
            
            # システム命令と画像、プロンプトを渡す
            response = await self.model_vision.generate_content_async(
                [self.system_instruction, image_part, prompt]
            )
            
            content = response.text
            if len(content) > 1900:
                content = content[:1900] + "\n...(長文のため以下省略)"
            return content
        except Exception as e:
            return f"⚠️ 画像解析中にエラーが発生しました: {str(e)}"

    # /ai (テキストチャット)
    @app_commands.command(name="ai", description="Gemini知能中枢に質問します。")
    @app_commands.describe(prompt="質問や話したい内容")
    async def ai_chat(self, interaction: discord.Interaction, prompt: str):
        await interaction.response.defer() # 思考時間を確保
        answer = await self.generate_text_response(prompt)
        await interaction.followup.send(f"🤖 **Rb m/25E 知能中枢:**\n{answer}")

    # /ai_image (画像解析)
    @app_commands.command(name="ai_image", description="画像を解析し、質問に答えます。")
    @app_commands.describe(image="解析する画像", prompt="画像についての質問")
    async def ai_image(self, interaction: discord.Interaction, image: discord.Attachment, prompt: str):
        await interaction.response.defer() # 思考時間を確保

        if not image.content_type.startswith(('image/jpeg', 'image/png', 'image/webp')):
            return await interaction.followup.send("❌ 画像ファイル（JPG, PNG, WebP）のみ対応しています、司令官。", ephemeral=True)

        try:
            # 画像をダウンロード
            async with aiohttp.ClientSession() as session:
                async with session.get(image.url) as resp:
                    if resp.status != 200:
                        return await interaction.followup.send("❌ 画像のダウンロードに失敗しました、司令官。", ephemeral=True)
                    image_data = BytesIO(await resp.read())
            
            answer = await self.generate_vision_response(image_data, prompt)
            await interaction.followup.send(f"🤖 **Rb m/25E 知能中枢 (画像解析):**\n{answer}")

        except Exception as e:
            await interaction.followup.send(f"❌ 画像解析中に予期せぬエラーが発生しました: {str(e)}", ephemeral=True)


    @commands.Cog.listener()
    async def on_message(self, message):
        """メンションされた際に応答するロジック (テキスト専用)"""
        if message.author.bot:
            return

        # Botへのメンションが含まれているかチェック
        if self.bot.user in message.mentions:
            # メンション部分を削除してプロンプトを抽出
            content = re.sub(f'<@!?{self.bot.user.id}>', '', message.content).strip()
            
            if not content:
                await message.reply("📡 司令官、何か御用でしょうか？（メンションの後にメッセージを入力してください）")
                return

            async with message.channel.typing():
                answer = await self.generate_text_response(content)
                await message.reply(answer)

async def setup(bot):
    await bot.add_cog(AIChat(bot))

