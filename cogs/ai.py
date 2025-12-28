import discord
from discord import app_commands
from discord.ext import commands
import os
import aiohttp
import re
import json

class AIChat(commands.Cog):
    ai_group = app_commands.Group(name="ai", description="Gemini知能中枢 (Direct Access)")

    def __init__(self, bot):
        self.bot = bot
        self.api_key = os.getenv("GEMINI_API_KEY")
        # 直接叩くためのURL (v1 安定版)
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.api_key}"

    async def generate_response(self, prompt):
        if not self.api_key:
            return "❌ APIキーが未設定です。"

        # リクエストデータ（Google APIの生仕様）
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }]
        }
        headers = {'Content-Type': 'application/json'}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.url, headers=headers, data=json.dumps(payload)) as resp:
                    result = await resp.json()
                    
                    if resp.status == 200:
                        # 成功時のデータ抽出
                        return result['candidates'][0]['content']['parts'][0]['text']
                    else:
                        # エラー時の生メッセージを解析
                        error_msg = result.get('error', {}).get('message', '不明なエラー')
                        return f"⚠️ APIエラー ({resp.status}): {error_msg}"
        except Exception as e:
            return f"⚠️ 通信失敗: {str(e)}"

    @ai_group.command(name="ask", description="Geminiに質問します")
    async def ask(self, interaction: discord.Interaction, prompt: str):
        await interaction.response.defer()
        answer = await self.generate_response(prompt)
        await interaction.followup.send(f"🤖 **AI回答:**\n{answer[:1900]}")

async def setup(bot):
    await bot.add_cog(AIChat(bot))
