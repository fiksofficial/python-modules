from .. import loader, utils
import requests
import json
import asyncio

API_URL = "https://openrouter.ai/api/v1/chat/completions"

@loader.tds
class DeepSeekModule(loader.Module):
    "Модуль для отправки вопросов к DeepSeek с использованием OpenRouter API."

    strings = {"name": "DeepSeek"}

    def __init__(self):
        self.config = loader.ModuleConfig(
            "ANIMATION", True, "Включить анимацию печати",
            "API_KEY", "", "API ключ OpenRouter"
        )
        self.history = []

    async def dsccmd(self, message):
        "Отправить вопрос к DeepSeek. Использование: .dsc <вопрос>"
        args = utils.get_args_raw(message)
        if not args:
            await message.edit("**❌ Ошибка:** Укажите вопрос.", parse_mode="Markdown")
            return
        
        api_key = self.config["API_KEY"].strip()
        if not api_key:
            await message.edit("**❌ Ошибка:** API ключ не установлен.", parse_mode="Markdown")
            return
        
        await message.edit("**🔄 Отправка запроса...**", parse_mode="Markdown")
        
        self.history.append({"role": "user", "content": args})
        
        payload = {
            "model": "deepseek/deepseek-r1:free",
            "messages": self.history
        }
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(API_URL, headers=headers, data=json.dumps(payload))
            response.raise_for_status()
            data = response.json()
            
            if "choices" in data and len(data["choices"]) > 0:
                reply = data["choices"][0]["message"]["content"]
                self.history.append({"role": "assistant", "content": reply})
                
                if self.config["ANIMATION"]:
                    words = reply.split()
                    displayed_text = "**💬 Ответ:**\n\n"
                    
                    for word in words:
                        displayed_text += word + " "
                        await message.edit(displayed_text, parse_mode="Markdown")
                        await asyncio.sleep(0.2)  # Задержка между словами
                else:
                    await message.edit(f"**💬 Ответ:**\n\n{reply}", parse_mode="Markdown")
            else:
                await message.edit("**❌ Ошибка:** Пустой ответ от API.", parse_mode="Markdown")
        except requests.exceptions.RequestException as e:
            await message.edit(f"**❌ Ошибка запроса:** `{str(e)}`", parse_mode="Markdown")

    async def cleardsccmd(self, message):
        "Очистить историю диалога с DeepSeek."
        self.history = []
        await message.edit("**✅ История диалога очищена.**", parse_mode="Markdown")

