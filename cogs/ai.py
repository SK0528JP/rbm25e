import discord
from discord import app_commands
from discord.ext import commands
import os
import aiohttp
import re

class AIChat(commands.Cog):
    ai_group = app_commands.Group(name="ai", description="GitHub Native 知能中枢")

    def __init__(self, bot):
        self.bot = bot
        # GitHubのトークンを使用（GitHub Actionsなら自動で渡されるMY_GITHUB_TOKEN等）
        self.token = os.getenv("MY_GITHUB_TOKEN") or os.getenv("HUGGINGFACE_TOKEN")
        # GitHub Models の安定したエンドポイント
        self.endpoint = "https://models.inference.ai.azure.com/chat/completions"

    async def generate_response(self, prompt):
        if not self.token:
            return "❌ GitHubトークンが未設定です。"

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

        # Llama 3.1 70B (超高性能・無料) を指定
        payload = {
            "messages": [
                {"role": "system", "content": "あなたは支援AI『Rb m/25E』です。日本語で回答してください。"},
                {"role": "user", "content": prompt}
            ],
            "model": "meta-llama-3.1-70b-instruct",
            "max_tokens": 1000
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.endpoint, headers=headers, json=payload) as resp:
                    result = await resp.json()
                    
                    if resp.status == 200:
                        return result['choices'][0]['message']['content']
                    else:
                        error_details = result.get('error', {}).get('message', '不明なエラー')
                        return f"⚠️ GitHub AIエラー ({resp.status}): {error_details}"
        except Exception as e:
            return f"⚠️ 通信失敗: {str(e)}"

    @ai_group.command(name="ask", description="GitHub直結AIに質問します")
    async def ask(self, interaction: discord.Interaction, prompt: str):
        await interaction.response.defer()
        answer = await self.generate_response(prompt)
        await interaction.followup.send(f"🤖 **GitHub AI:**\n{answer[:1900]}")

async def setup(bot):
    await bot.add_cog(AIChat(bot))
