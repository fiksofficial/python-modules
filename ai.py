#         ______     ___  ___          _       _      
#    ____ | ___ \    |  \/  |         | |     | |     
#   / __ \| |_/ /   _| .  . | ___   __| |_   _| | ___ 
#  / / _` |  __/ | | | |\/| |/ _ \ / _` | | | | |/ _ \
# | | (_| | |  | |_| | |  | | (_) | (_| | |_| | |  __/
#  \ \__,_\_|   \__, \_|  |_/\___/ \__,_|\__,_|_|\___|
#   \____/       __/ |                                
#               |___/                                 

# На модуль распространяется лицензия "GNU General Public License v3.0"
# https://github.com/all-licenses/GNU-General-Public-License-v3.0

# meta developer: @pymodule
# meta fhsdesc: tool, tools, ai, assistant

from .. import loader, utils
import aiohttp
import json
import asyncio
import logging
import re
from telethon.tl.types import Message
from ..inline.types import BotMessage
from typing import Union, List, Optional

API_URL = "https://api.intelligence.io.solutions/api/v1/chat/completions"
TG_MSG_LIMIT = 4096
MAX_INPUT_LENGTH = 8000

@loader.tds
class AIModule(loader.Module):
    """Module for interacting with AI"""
    strings = {
        "name": "AI",
        "no_question": "❌ <b>Error:</b> Please provide a question.",
        "no_api_key": "❌ <b>Error:</b> API key is not set. Configure it using <code>{prefix}config AI</code>.",
        "empty_file": "❌ <b>Error:</b> The file is empty.",
        "empty_response": "❌ <b>Error:</b> Empty response from API.",
        "request_error": "❌ <b>Request error:</b> <code>{error}</code>",
        "no_txt_file": "❌ <b>Error:</b> Reply to a <code>.txt</code>, <code>.md</code>, or <code>.json</code> file.",
        "reading_file": "🔄 <b>Reading file...</b>",
        "request_sent": "🔍 <b>Sending request...</b>",
        "history_cleared": "✔️ <b>Query history cleared.</b>",
        "input_too_long": "⚠️ <b>Error:</b> Input is too long ({length} characters). Maximum: {max_length}.",
        "config_view": "<b>🔧 Current settings:</b>\n\n- <b>API_KEY:</b> {api_key}\n- <b>Model:</b> {model}\n- <b>Save history:</b> {save_history}\n- <b>History limit:</b> {history_limit}\n- <b>System prompt:</b> {system_prompt}",
        "cfg_api_key": "IO Intelligence API key (https://ai.io.net/ai/api-keys).",
        "cfg_model": "Model (e.g., deepseek-ai/DeepSeek-R1).",
        "cfg_save_history": "Save query history to the database.",
        "cfg_history_limit": "Maximum number of messages in history (0 = no limit).",
        "cfg_system_prompt": "System prompt to set the model's context.",
        "invalid_api_key": "❌ <b>Error:</b> Invalid or expired API key.",
        "rate_limit_exceeded": "❌ <b>Error:</b> Rate limit exceeded. Check limits: https://docs.io.net/reference/get-started-with-io-intelligence-api.",
        "test_success": "✅ <b>Success:</b> API key is valid.",
        "test_failed": "❌ <b>Error:</b> Failed to validate API key: <code>{error}</code>",
        "think_header": "<b>📝 AI Thoughts:</b>",
        "response_header": "<b>💬 Response:</b>",
        "clear_history": "🧹 Clear History",
        "close": "❌ Close",
    }

    strings_ru = {
        "name": "AI",
        "no_question": "❌ Ошибка: Укажите вопрос.",
        "no_api_key": "❌ Ошибка: API-ключ не установлен. Настройте через <code>{prefix}config AI</code>.",
        "empty_file": "❌ Ошибка: Файл пустой.",
        "empty_response": "❌ Ошибка: Пустой ответ от API.",
        "request_error": "❌ Ошибка запроса: <code>{error}</code>",
        "no_txt_file": "❌ Ошибка: Ответьте на файл <code>.txt</code>, <code>.md</code> или <code>.json</code>.",
        "reading_file": "🔄 Чтение файла...",
        "request_sent": "🔍 Отправка запроса...",
        "history_cleared": "✔️ История запросов очищена.",
        "input_too_long": "⚠️ Ошибка: Текст слишком длинный ({length} символов). Максимум: {max_length}.",
        "config_view": "🔧 Текущие настройки:\n\n- API_KEY: {api_key}\n- Модель: {model}\n- Сохранять историю: {save_history}\n- Лимит истории: {history_limit}\n- Системный промпт: {system_prompt}",
        "cfg_api_key": "API-ключ IO Intelligence (https://ai.io.net/ai/api-keys).",
        "cfg_model": "Модель (например, deepseek-ai/DeepSeek-R1).",
        "cfg_save_history": "Сохранять историю запросов в базе данных.",
        "cfg_history_limit": "Максимальное количество сообщений в истории (0 = без лимита).",
        "cfg_system_prompt": "Системный промпт для настройки контекста модели.",
        "invalid_api_key": "❌ Ошибка: Неверный или истёкший API-ключ.",
        "rate_limit_exceeded": "❌ Ошибка: Превышен лимит запросов. Проверьте лимиты: https://docs.io.net/reference/get-started-with-io-intelligence-api.",
        "test_success": "✅ Успех: API-ключ валиден.",
        "test_failed": "❌ Ошибка: Не удалось проверить API-ключ: <code>{error}</code>",
        "think_header": "<b>📝 Размышления ИИ:</b>",
        "response_header": "<b>💬 Ответ:</b>",
        "clear_history": "🧹 Очистить историю",
        "close": "❌ Закрыть",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "API_KEY",
                "",
                lambda: self.strings["cfg_api_key"],
                validator=loader.validators.Hidden()
            ),
            loader.ConfigValue(
                "MODEL",
                "deepseek-ai/DeepSeek-R1",
                lambda: self.strings["cfg_model"],
                validator=loader.validators.Choice([
                    "meta-llama/Llama-4-Maverick-17B-128E-Instruct-FP8",
                    "deepseek-ai/DeepSeek-R1-0528",
                    "Qwen/Qwen3-235B-A22B-FP8",
                    "meta-llama/Llama-3.3-70B-Instruct",
                    "google/gemma-3-27b-it",
                    "mistralai/Magistral-Small-2506",
                    "mistralai/Devstral-Small-2505",
                    "deepseek-ai/DeepSeek-R1-Distill-Llama-70B",
                    "deepseek-ai/DeepSeek-R1",
                    "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
                    "mistralai/Mistral-Large-Instruct-2411",
                    "mistralai/Ministral-8B-Instruct-2410"
                ])
            ),
            loader.ConfigValue(
                "SAVE_HISTORY",
                True,
                lambda: self.strings["cfg_save_history"],
                validator=loader.validators.Boolean()
            ),
            loader.ConfigValue(
                "HISTORY_LIMIT",
                10,
                lambda: self.strings["cfg_history_limit"],
                validator=loader.validators.Integer(minimum=0)
            ),
            loader.ConfigValue(
                "SYSTEM_PROMPT",
                "You are a helpful assistant.",
                lambda: self.strings["cfg_system_prompt"],
                validator=loader.validators.String()
            )
        )
        self.history = []

    async def client_ready(self, client, db):
        self._client = client
        self._db = db
        self._session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30)
        )
        self.history = self._db.get(self.strings["name"], "history", [])

    async def on_unload(self):
        if self._session:
            await self._session.close()

    def _truncate_history(self):
        if not self.config["SAVE_HISTORY"]:
            self.history = []
        else:
            limit = self.config["HISTORY_LIMIT"]
            if limit > 0 and len(self.history) > limit * 2:
                self.history = self.history[-limit * 2:]
        self._db.set(self.strings["name"], "history", self.history)

    async def _send_request(self, payload, api_key):
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        try:
            async with self._session.post(API_URL, headers=headers, json=payload) as response:
                if response.status == 401:
                    raise aiohttp.ClientResponseError(
                        response.request_info,
                        response.history,
                        status=401,
                        message="Invalid or expired API key"
                    )
                if response.status == 429:
                    raise aiohttp.ClientResponseError(
                        response.request_info,
                        response.history,
                        status=429,
                        message="Rate limit exceeded"
                    )
                if response.status == 400:
                    raise aiohttp.ClientResponseError(
                        response.request_info,
                        response.history,
                        status=400,
                        message="Invalid request parameters"
                    )
                response.raise_for_status()
                data = await response.json()
                if "choices" in data and len(data["choices"]) > 0:
                    content = data["choices"][0]["message"]["content"]
                    logging.debug(f"API response content: {content}")
                    return content
                return None
        except aiohttp.ClientResponseError as e:
            logging.error(f"API request failed: {str(e)}")
            if e.status == 401:
                raise ValueError(self.strings["invalid_api_key"])
            if e.status == 429:
                raise ValueError(self.strings["rate_limit_exceeded"])
            if e.status == 400:
                raise ValueError("Invalid request parameters")
            raise ValueError(f"HTTP Error: {e.message}")
        except aiohttp.ClientTimeout:
            logging.error("API request timed out")
            raise ValueError("Request timed out after 30 seconds")
        except aiohttp.ClientError as e:
            logging.error(f"API client error: {str(e)}")
            raise ValueError(f"API request failed: {str(e)}")

    async def _send_long_message(self, message: Message, text: str, reply_markup=None):
        think_pattern = r"<think>(.*?)</think>"
        think_matches = re.findall(think_pattern, text, re.DOTALL)

        think_text = ""
        if think_matches:
            think_text = "\n\n".join([f"<i>{match.strip()}</i>" for match in think_matches])

        text = re.sub(think_pattern, "", text, flags=re.DOTALL).strip()
        text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)

        if think_text:
            full_text = f"{self.strings['think_header']}\n{think_text}\n\n{self.strings['response_header']}\n{text}"
        else:
            full_text = f"{self.strings['response_header']}\n{text}"

        chunks = [full_text[i:i + TG_MSG_LIMIT] for i in range(0, len(full_text), TG_MSG_LIMIT)]
        for i, chunk in enumerate(chunks):
            await utils.answer(message, chunk, reply_markup=reply_markup if i == len(chunks) - 1 else None)

    async def clear_history_callback(self, call: BotMessage):
        self.history = []
        self._db.set(self.strings["name"], "history", [])
        await call.edit(self.strings["history_cleared"])

    async def close_message_callback(self, call: BotMessage):
        await call.delete()

    @loader.command(
        doc="Send a question to AI. Usage: .ai [--no-history] <question>",
        ru_doc="Отправить вопрос к AI. Использование: .ai [--no-history] <вопрос>"
    )
    async def ai(self, message: Message):
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, self.strings["no_question"])
            return
        api_key = self.config["API_KEY"].strip()
        if not api_key:
            await utils.answer(message, self.strings["no_api_key"].format(prefix=self.get_prefix()))
            return
        if len(args) > MAX_INPUT_LENGTH:
            await utils.answer(message, self.strings["input_too_long"].format(length=len(args), max_length=MAX_INPUT_LENGTH))
            return
        save_to_history = not args.startswith("--no-history") and self.config["SAVE_HISTORY"]
        if not save_to_history:
            args = args.replace("--no-history", "").strip()
        if not args:
            await utils.answer(message, self.strings["no_question"])
            return
        await utils.answer(message, self.strings["request_sent"])
        logging.debug(f"Sending request with model: {self.config['MODEL']}")
        messages = [{"role": "system", "content": self.config["SYSTEM_PROMPT"]}] if self.config["SYSTEM_PROMPT"] else []
        if save_to_history:
            self.history.append({"role": "user", "content": args})
            self._truncate_history()
            messages.extend(self.history)
        else:
            messages.append({"role": "user", "content": args})
        payload = {
            "model": self.config["MODEL"],
            "messages": messages,
            "temperature": 0.7,
            "max_completion_tokens": 1000
        }
        try:
            reply = await self._send_request(payload, api_key)
            if reply:
                if save_to_history:
                    self.history.append({"role": "assistant", "content": reply})
                    self._truncate_history()
                reply_markup = [
                    [
                        {"text": self.strings["clear_history"], "callback": self.clear_history_callback},
                        {"text": self.strings["close"], "callback": self.close_message_callback}
                    ]
                ]
                await self._send_long_message(message, reply, reply_markup)
            else:
                await utils.answer(message, self.strings["empty_response"])
        except ValueError as e:
            await utils.answer(message, self.strings["request_error"].format(error=str(e)))

    @loader.command(
        doc="Send file contents to AI. Usage: .txtai [--no-history] (file reply)",
        ru_doc="Отправить содержимое файла к AI. Использование: .txtai [--no-history] (ответ на файл)"
    )
    async def txtai(self, message: Message):
        reply = await message.get_reply_message()
        if not reply or not reply.file or not reply.file.name.lower().endswith((".txt", ".md", ".json")):
            await utils.answer(message, self.strings["no_txt_file"])
            return
        api_key = self.config["API_KEY"].strip()
        if not api_key:
            await utils.answer(message, self.strings["no_api_key"].format(prefix=self.get_prefix()))
            return
        await utils.answer(message, self.strings["reading_file"])
        file_bytes = await reply.download_media(bytes)
        try:
            file_text = file_bytes.decode("utf-8").strip()
        except UnicodeDecodeError:
            await utils.answer(message, "❌ <b>Error:</b> Unable to decode file as UTF-8.")
            return
        if not file_text:
            await utils.answer(message, self.strings["empty_file"])
            return
        if len(file_text) > MAX_INPUT_LENGTH:
            await utils.answer(message, self.strings["input_too_long"].format(length=len(file_text), max_length=MAX_INPUT_LENGTH))
            return
        args = utils.get_args_raw(message)
        save_to_history = not args.startswith("--no-history") and self.config["SAVE_HISTORY"]
        if not args.startswith("--no-history"):
            args = args.replace("--no-history", "").strip()
        await utils.answer(message, self.strings["request_sent"])
        messages = [{"role": "system", "content": self.config["SYSTEM_PROMPT"]}] if self.config["SYSTEM_PROMPT"] else []
        if save_to_history:
            self.history.append({"role": "user", "content": file_text})
            self._truncate_history()
            messages.extend(self.history)
        else:
            messages.append({"role": "user", "content": file_text})
        payload = {
            "model": self.config["MODEL"],
            "messages": messages,
            "temperature": 0.7,
            "max_completion_tokens": 1000
        }
        try:
            reply = await self._send_request(payload, api_key)
            if reply:
                if save_to_history:
                    self.history.append({"role": "assistant", "content": reply})
                    self._truncate_history()
                reply_markup = [
                    [
                        {"text": self.strings["clear_history"], "callback": self.clear_history_callback},
                        {"text": self.strings["close"], "callback": self.close_message_callback}
                    ]
                ]
                await self._send_long_message(message, reply, reply_markup)
            else:
                await utils.answer(message, self.strings["empty_response"])
        except ValueError as e:
            await utils.answer(message, self.strings["request_error"].format(error=str(e)))

    @loader.command(
        doc="Clear query history. Usage: .clearai",
        ru_doc="Очистить историю запросов. Использование: .clearai"
    )
    async def clearai(self, message: Message):
        self.history = []
        self._db.set(self.strings["name"], "history", [])
        await utils.answer(message, self.strings["history_cleared"])

    @loader.command(
        doc="View or change settings. Usage: .aiconfig [--edit]",
        ru_doc="Просмотреть или изменить настройки. Использование: .aiconfig [--edit]"
    )
    async def aiconfig(self, message: Message):
        args = utils.get_args_raw(message)
        if args == "--edit":
            await self.allmodules.commands["config"]("AI", peer=message.peer_id)
            return
        api_key = self.config["API_KEY"].strip()
        masked_key = "********" if api_key else "<not set>"
        save_history = "Enabled" if self.config["SAVE_HISTORY"] else "Disabled"
        system_prompt = self.config["SYSTEM_PROMPT"][:50] + "..." if len(self.config["SYSTEM_PROMPT"]) > 50 else self.config["SYSTEM_PROMPT"]
        await utils.answer(
            message,
            self.strings["config_view"].format(
                api_key=masked_key,
                model=self.config["MODEL"],
                save_history=save_history,
                history_limit=self.config["HISTORY_LIMIT"],
                system_prompt=system_prompt or "<not set>"
            )
        )

    @loader.command(
        doc="Check the validity of the API key. Usage: .aitest",
        ru_doc="Проверить валидность API-ключа. Использование: .aitest"
    )
    async def aitest(self, message: Message):
        api_key = self.config["API_KEY"].strip()
        if not api_key:
            await utils.answer(message, self.strings["no_api_key"].format(prefix=self.get_prefix()))
            return
        await utils.answer(message, self.strings["request_sent"])
        payload = {
            "model": self.config["MODEL"],
            "messages": [{"role": "user", "content": "Test"}],
            "temperature": 0.7,
            "max_completion_tokens": 10
        }
        try:
            await self._send_request(payload, api_key)
            await utils.answer(message, self.strings["test_success"])
        except ValueError as e:
            await utils.answer(message, self.strings["test_failed"].format(error=str(e)))
