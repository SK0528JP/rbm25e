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
            # 最新のFlashモデルを使用（高速かつマルチモーダル対応）
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            
            # システム命令：Botのキャラクター設定
            self.system_instruction = (
                "あなたは『Rb m/25E』という名称の、多機能支援型Discord Botです。"
                "冷静かつ誠実で、少し軍事的な支援AIのような口調で話してください。"
                "ユーザーのことを『司令官』または『ユーザー』と呼び、簡潔に回答してください。"
                "回答の最後は『承知しました。』や『了解です、司令官。』などで締めてください。"
            )
        else:
            self.model = None

    # --- 共通生成ロジック ---
    async def generate_content_async(self, contents):
        if not self.model:
            return "❌ Gemini APIキーが設定されていないため、知能中枢が起動していません。"
        try:
            # システム命令を先頭に付与
            prompt_parts = [self.system_instruction]
            if isinstance(contents, list):
                prompt_parts.extend(contents)
            else:
                prompt_parts.append(contents)

            response = await self.model.generate_content_async(prompt_parts)
            return response.text if response.text else "⚠️ 適切な回答を生成できませんでした。"
        except Exception as e:
            return f"⚠️ 思考回路でエラーが発生しました: {str(e)}"

    # --- スラッシュコマンド：/ai グループ ---
    ai_group = app_commands.Group(name="ai", description="Gemini知能中枢による支援機能")

    @ai_group.command(name="ask", description="テキストでGeminiに質問・相談をします")
    @app_commands.describe(prompt="質問したい内容")
    async def ask(self, interaction: discord.Interaction, prompt: str):
        await interaction.response.defer()
        answer = await self.generate_content_async(prompt)
        await interaction.followup.send(f"🤖 **Rb m/25E 知能中枢:**\n{answer}")

    @ai_group.command(name="image", description="画像の内容を解析し、質問に答えます")
    @app_commands.describe(attachment="解析する画像", prompt="画像について聞きたいこと（空欄でも可）")
    async def image(self, interaction: discord.Interaction, attachment: discord.Attachment, prompt: str = "この画像について詳しく説明してください"):
        await interaction.response.defer()

        # 画像形式チェック
        if not attachment.content_type or not attachment.content_type.startswith('image/'):
            return await interaction.followup.send("❌ 解析可能な画像ファイルを選択してください。", ephemeral=True)

        try:
            # aiohttpで画像をバイナリとして取得
            async with aiohttp.ClientSession() as session:
                async with session.get(attachment.url) as resp:
                    if resp.status != 200:
                        return await interaction.followup.send("❌ 画像データの受信に失敗しました。")
                    image_data = await resp.read()

            image_part = {
                "mime_type": attachment.content_type,
                "data": image_data
            }

            answer = await self.generate_content_async([image_part, prompt])
            await interaction.followup.send(f"🤖 **Rb m/25E 画像解析:**\n{answer}")
        except Exception as e:
            await interaction.followup.send(f"❌ 解析失敗: {str(e)}")

    # --- メンション応答機能 ---
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        # Botへのメンション、または返信先がBotの場合
        is_mentioned = self.bot.user in message.mentions
        is_reply_to_bot = message.reference and message.reference.resolved and message.reference.resolved.author.id == self.bot.user.id

        if is_mentioned or is_reply_to_bot:
            # メンション部分を削除して中身を抽出
            clean_content = re.sub(f'<@!?{self.bot.user.id}>', '', message.content).strip()
            
            if not clean_content and is_mentioned:
                await message.reply("📡 司令官、何か御用でしょうか？")
                return

            async with message.channel.typing():
                answer = await self.generate_content_async(clean_content)
                # 2000文字制限対策
                if len(answer) > 2000:
                    answer = answer[:1990] + "..."
                await message.reply(answer)

async def setup(bot):
    await bot.add_cog(AIChat(bot))
