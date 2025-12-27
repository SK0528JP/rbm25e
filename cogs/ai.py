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
        self.api_key = os.getenv("GEMINI_API_KEY")
        
        # 使用候補となるモデルリスト（優先度順）
        # Flash系で失敗したら、安定版のPro系へ自動的に切り替えます
        self.text_models = [
            'gemini-1.5-flash',
            'gemini-1.5-flash-latest',
            'gemini-1.5-pro',
            'gemini-pro'
        ]
        
        # 画像対応モデルのリスト（Pro(旧)は画像非対応のため除外）
        self.vision_models = [
            'gemini-1.5-flash',
            'gemini-1.5-flash-latest',
            'gemini-1.5-pro'
        ]

        if self.api_key:
            genai.configure(api_key=self.api_key)
        
        # 現在アクティブなモデル名を保持する変数
        self.active_model_name = "未接続"

    async def _try_generate(self, models_list, contents):
        """
        リスト内のモデルを順番に試し、最初に成功した結果を返す
        """
        if not self.api_key:
            return "❌ Gemini APIキーが設定されていません。"

        last_error = None
        
        for model_name in models_list:
            try:
                # モデルのインスタンス化
                model = genai.GenerativeModel(model_name)
                
                # 生成実行
                response = await model.generate_content_async(contents)
                
                if response and response.text:
                    # 成功したら、そのモデル名を記録して結果を返す
                    self.active_model_name = model_name
                    return response.text
            except Exception as e:
                # エラー（404など）が出たら次のモデルへ
                last_error = e
                print(f"[AI Log] Model '{model_name}' failed: {e}")
                continue
        
        # 全滅した場合
        return f"⚠️ 全てのモデルで通信に失敗しました。\n最終エラー: {str(last_error)}\n(APIキーの権限や有効性を確認してください)"

    # --- コマンドグループ ---
    ai_group = app_commands.Group(name="ai", description="Gemini知能中枢")

    @ai_group.command(name="ask", description="Geminiと会話します")
    async def ask(self, interaction: discord.Interaction, prompt: str):
        await interaction.response.defer()
        
        # システムプロンプトを付与
        system_prompt = "あなたは支援AI『Rb m/25E』です。司令官に対し、冷静かつ的確に回答してください。"
        full_content = [system_prompt, f"質問: {prompt}"]
        
        # テキスト用モデルリストで試行
        answer = await self._try_generate(self.text_models, full_content)
        
        msg = f"🤖 **AI回答 ({self.active_model_name}):**\n{answer}"
        if len(msg) > 2000: msg = msg[:1990] + "..."
        await interaction.followup.send(msg)

    @ai_group.command(name="image", description="画像を解析します")
    async def image(self, interaction: discord.Interaction, attachment: discord.Attachment, prompt: str = "この画像について説明してください"):
        await interaction.response.defer()
        
        if not attachment.content_type or not attachment.content_type.startswith('image/'):
            return await interaction.followup.send("❌ 画像を選択してください。", ephemeral=True)

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(attachment.url) as resp:
                    if resp.status != 200:
                        return await interaction.followup.send("❌ 画像取得失敗")
                    image_data = await resp.read()

            image_part = {"mime_type": attachment.content_type, "data": image_data}
            
            # システムプロンプト + 画像 + 質問
            contents = ["あなたは画像認識機能を持つ支援AIです。", image_part, prompt]
            
            # 画像用モデルリストで試行
            answer = await self._try_generate(self.vision_models, contents)
            
            msg = f"🤖 **画像解析 ({self.active_model_name}):**\n{answer}"
            if len(msg) > 2000: msg = msg[:1990] + "..."
            await interaction.followup.send(msg)

        except Exception as e:
            await interaction.followup.send(f"❌ 処理エラー: {str(e)}")

    @ai_group.command(name="status", description="現在のAI接続状況を確認します")
    async def status(self, interaction: discord.Interaction):
        """現在の接続モデルとAPIキー状態を表示"""
        status_msg = "🟢 APIキー設定済み" if self.api_key else "🔴 APIキー未設定"
        await interaction.response.send_message(
            f"📡 **知能中枢ステータス**\n"
            f"API状態: {status_msg}\n"
            f"最終接続モデル: `{self.active_model_name}`\n"
            f"候補モデル数: {len(self.text_models)} 機"
        )

    # --- メンション応答 ---
    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot: return
        
        is_mentioned = self.bot.user in message.mentions
        is_reply = (message.reference and message.reference.resolved and 
                    message.reference.resolved.author.id == self.bot.user.id)

        if is_mentioned or is_reply:
            clean_content = re.sub(f'<@!?{self.bot.user.id}>', '', message.content).strip()
            if not clean_content: return await message.reply("📡 待機中。指示をどうぞ。")

            async with message.channel.typing():
                # メンション時はテキストモデルを使用
                answer = await self._try_generate(self.text_models, clean_content)
                if len(answer) > 2000: answer = answer[:1990] + "..."
                await message.reply(answer)

async def setup(bot):
    await bot.add_cog(AIChat(bot))
