import discord
from discord import app_commands
from discord.ext import commands
import os
import aiohttp
import re
import json

class AIChat(commands.Cog):
    ai_group = app_commands.Group(name="ai", description="Rb m/25E 安定知能中枢")

    def __init__(self, bot):
        self.bot = bot
        self.api_token = os.getenv("HUGGINGFACE_TOKEN")
        
        # 安定性を重視し、多くのユーザーが現在も成功しているエンドポイントを使用
        self.api_url = "https://api-inference.huggingface.co/models"
        
        # モデル選定：申請不要・日本語対応・高稼働率のモデルを厳選
        # 対話用: Microsoft Phi-3 (非常に軽量でエラーが出にくい)
        self.chat_model = "microsoft/Phi-3-mini-4k-instruct"
        # 視覚用: Salesforce BLIP (画像解析のデファクトスタンダード)
        self.vision_model = "Salesforce/blip-image-captioning-base"

    async def query_api(self, model_id, payload, is_binary=False):
        if not self.api_token:
            return "❌ HUGGINGFACE_TOKEN が未設定です。"

        url = f"{self.api_url}/{model_id}"
        headers = {"Authorization": f"Bearer {self.api_token}"}
        
        try:
            async with aiohttp.ClientSession() as session:
                if is_binary:
                    # 画像データ送信時
                    async with session.post(url, headers=headers, data=payload) as resp:
                        if resp.status == 200:
                            return await resp.json()
                        return await self.handle_error(resp)
                else:
                    # テキストデータ送信時
                    async with session.post(url, headers=headers, json=payload) as resp:
                        if resp.status == 200:
                            return await resp.json()
                        return await self.handle_error(resp)
        except Exception as e:
            return f"⚠️ 通信失敗: {str(e)}"

    async def handle_error(self, resp):
        if resp.status == 503:
            return "💤 AIユニット起動中... (20秒ほど待って再試行してください)"
        try:
            err_data = await resp.json()
            return f"⚠️ APIエラー ({resp.status}): {err_data.get('error', '不明')}"
        except:
            return f"⚠️ 致命的エラー ({resp.status}): モデルのパスが変更された可能性があります。"

    @ai_group.command(name="ask", description="AIと対話します")
    async def ask(self, interaction: discord.Interaction, prompt: str):
        await interaction.response.defer()
        
        # Phi-3 向けのシンプルなプロンプト形式
        payload = {
            "inputs": f"<|user|>\n{prompt}<|end|>\n<|assistant|>",
            "parameters": {"max_new_tokens": 500, "return_full_text": False}
        }
        
        result = await self.query_api(self.chat_model, payload)
        
        if isinstance(result, str):
            answer = result
        else:
            # 応答リストからテキストを抽出
            answer = result[0].get('generated_text', '応答が空でした。')

        await interaction.followup.send(f"🤖 **AI回答:**\n{answer[:1900]}")

    @ai_group.command(name="image", description="画像を解析します")
    async def image(self, interaction: discord.Interaction, attachment: discord.Attachment):
        await interaction.response.defer()
        
        if not attachment.content_type or not attachment.content_type.startswith('image/'):
            return await interaction.followup.send("❌ 画像ファイルを指定してください。")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(attachment.url) as resp:
                    image_data = await resp.read()

            result = await self.query_api(self.vision_model, image_data, is_binary=True)
            
            if isinstance(result, str):
                await interaction.followup.send(result)
            else:
                desc = result[0].get('generated_text', '解析不能')
                await interaction.followup.send(f"🤖 **視覚解析:** {desc}")
        except Exception as e:
            await interaction.followup.send(f"❌ 解析失敗: {str(e)}")

async def setup(bot):
    await bot.add_cog(AIChat(bot))
