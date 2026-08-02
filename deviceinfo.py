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
# meta fhsdesc: tool, tools, phone, info
# requires: aiohttp cachetools

import asyncio
import logging
from typing import List, Dict, Any
import aiohttp
from cachetools import TTLCache

from .. import loader, utils
from ..inline.types import InlineMessage

logger = logging.getLogger(__name__)

@loader.tds
class DeviceInfo(loader.Module):
    """A module for obtaining information about smartphones"""

    strings = {
        "name": "DeviceInfo",
        "searching": "🔍 Searching devices for: <b>{}</b>...",
        "no_query": "❌ Specify a device name! Example: <code>.di iPhone 15</code>",
        "no_results": "📭 No devices found for query: <b>{}</b>",
        "device_list": "📱 Found {} devices for query <b>{}</b>:",
        "device_info": "📱 <b>{}</b>\n\n{}",
        "error": "❌ Error: {}. Try again later or check the API.",
        "network": "📡 <b>Network</b>: {}\n",
        "launched": "📅 <b>Launch</b>:\n  Announced: {}\n  Status: {}\n",
        "body": "📏 <b>Body</b>:\n  Dimensions: {}\n  Weight: {}\n  SIM: {}\n  Other: {}\n",
        "display": "🖥️ <b>Display</b>:\n  Type: {}\n  Size: {}\n  Resolution: {}\n  Protection: {}\n",
        "platform": "⚙️ <b>Platform</b>:\n  OS: {}\n  Chipset: {}\n  CPU: {}\n  GPU: {}\n",
        "memory": "💾 <b>Memory</b>:\n  Card slot: {}\n  Internal: {}\n  Other: {}\n",
        "main_camera": "📷 <b>Main Camera</b>:\n  Modules: {}\n  Features: {}\n  Video: {}\n",
        "selfie_camera": "🤳 <b>Selfie Camera</b>:\n  Modules: {}\n  Features: {}\n  Video: {}\n",
        "sound": "🔊 <b>Sound</b>:\n  Loudspeaker: {}\n  Audio Jack: {}\n  Other: {}\n",
        "comms": "🌐 <b>Comms</b>:\n  Wi-Fi: {}\n  Bluetooth: {}\n  GPS: {}\n  NFC: {}\n  Infrared: {}\n  Radio: {}\n  USB: {}\n",
        "sensors": "🛠️ <b>Sensors</b>: {}\n",
        "battery": "🔋 <b>Battery</b>:\n  Type: {}\n  Charging: {}\n",
        "misc": "🎨 <b>Misc</b>:\n  Colors: {}\n  Models: {}\n",
        "show_body": "📏 Body",
        "show_memory": "💾 Memory",
        "show_cameras": "📷 Cameras",
        "show_sound": "🔊 Sound",
        "show_comms": "🌐 Comms",
        "show_sensors": "🛠️ Sensors",
        "show_misc": "🎨 Misc",
        "next_photo": "▶️ Next Photo",
        "prev_photo": "◀️ Prev Photo",
        "back": "🔙 Back",
        "back_to_device": "🔙 To Device",
        "config_saved": "✅ Configuration saved!",
        "retrying": "🔄 Retrying request... (attempt {}/{})"
    }

    strings_ru = {
        "name": "DeviceInfo",
        "_cls_doc": "Модуль для получения информации о смартфонах",
        "searching": "🔍 Ищу устройства по запросу: <b>{}</b>...",
        "no_query": "❌ Укажи название устройства! Пример: <code>.di iPhone 15</code>",
        "no_results": "📭 Устройства не найдены для запросу: <b>{}</b>",
        "device_list": "📱 Найдено {} устройств по запросу <b>{}</b>:",
        "device_info": "📱 <b>{}</b>\n\n{}",
        "error": "❌ Ошибка: {}. Попробуй позже или проверь API.",
        "network": "📡 <b>Сеть</b>: {}\n",
        "launched": "📅 <b>Дата выпуска</b>:\n  Анонс: {}\n  Статус: {}\n",
        "body": "📏 <b>Корпус</b>:\n  Размеры: {}\n  Вес: {}\n  SIM: {}\n  Прочее: {}\n",
        "display": "🖥️ <b>Дисплей</b>:\n  Тип: {}\n  Размер: {}\n  Разрешение: {}\n  Защита: {}\n",
        "platform": "⚙️ <b>Платформа</b>:\n  ОС: {}\n  Чипсет: {}\n  CPU: {}\n  GPU: {}\n",
        "memory": "💾 <b>Память</b>:\n  Карта памяти: {}\n  Внутренняя: {}\n  Прочее: {}\n",
        "main_camera": "📷 <b>Основная камера</b>:\n  Модули: {}\n  Функции: {}\n  Видео: {}\n",
        "selfie_camera": "🤳 <b>Фронтальная камера</b>:\n  Модули: {}\n  Функции: {}\n  Видео: {}\n",
        "sound": "🔊 <b>Звук</b>:\n  Динамик: {}\n  Аудиоразъём: {}\n  Прочее: {}\n",
        "comms": "🌐 <b>Связь</b>:\n  Wi-Fi: {}\n  Bluetooth: {}\n  GPS: {}\n  NFC: {}\n  Инфракрасный порт: {}\n  Радио: {}\n  USB: {}\n",
        "sensors": "🛠️ <b>Датчики</b>: {}\n",
        "battery": "🔋 <b>Батарея</b>:\n  Тип: {}\n  Зарядка: {}\n",
        "misc": "🎨 <b>Разное</b>:\n  Цвета: {}\n  Модели: {}\n",
        "show_body": "📏 Корпус",
        "show_memory": "💾 Память",
        "show_cameras": "📷 Камеры",
        "show_sound": "🔊 Звук",
        "show_comms": "🌐 Связь",
        "show_sensors": "🛠️ Датчики",
        "show_misc": "🎨 Разное",
        "next_photo": "▶️ След. фото",
        "prev_photo": "◀️ Пред. фото",
        "back": "🔙 Назад",
        "back_to_device": "🔙 К устройству",
        "config_saved": "✅ Конфигурация сохранена!",
        "retrying": "🔄 Повторяю запрос... (попытка {}/{} )"
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "api_base_url",
                "https://gmsarena.vercel.app/",
                lambda: "API Url",
                validator=loader.validators.String()
            ),
            loader.ConfigValue(
                "max_results",
                20,
                lambda: "Maximum search results to display",
                validator=loader.validators.Integer(minimum=1, maximum=50)
            ),
            loader.ConfigValue(
                "timeout",
                10,
                lambda: "Timeout for API requests (seconds)",
                validator=loader.validators.Integer(minimum=5, maximum=30)
            ),
            loader.ConfigValue(
                "retry_attempts",
                3,
                lambda: "Number of retry attempts for API requests",
                validator=loader.validators.Integer(minimum=1, maximum=5)
            )
        )
        self.cache = TTLCache(maxsize=100, ttl=300)
        self.session: aiohttp.ClientSession = None

    async def client_ready(self, client, db):
        """Initialize aiohttp session on client ready"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config["timeout"])
        )
        logger.info("DeviceInfo: aiohttp session initialized")
        self.client = client  

    async def on_unload(self):
        """Close aiohttp session on module unload"""
        if self.session:
            await self.session.close()
            logger.info("DeviceInfo: aiohttp session closed")

    @staticmethod
    def _safe_get(device: Dict[str, Any], key: str, default: str = "N/A") -> str:
        """Safely get a value from a nested dict or return a default"""
        if not isinstance(device, dict):
            return default
        value = device.get(key)
        return value if value is not None and value != "" else default

    async def _resolve_entity(self, call: InlineMessage, message_id: int, chat_id: int = None):
        """Resolve Telegram entity to Message or int"""
        if call and getattr(call, "message", None):
            return call.message
        return chat_id or message_id

    async def _fetch_json(self, endpoint: str, params: Dict[str, Any] = None) -> Any:
        """Fetch JSON from API with retry and caching"""
        cache_key = f"{endpoint}_{params}" if params else endpoint
        if cache_key in self.cache:
            logger.debug(f"Cache hit for {cache_key}")
            return self.cache[cache_key]

        url = f"{self.config['api_base_url']}/gsm/{endpoint}"
        params_clean = {k: v for k, v in (params or {}).items() if k != "message"}  
        for attempt in range(1, self.config["retry_attempts"] + 1):
            try:
                async with self.session.get(url, params=params_clean or None) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        logger.error(f"DeviceInfo: HTTP {resp.status} for {url}: {error_text}")
                        raise aiohttp.ClientError(f"HTTP {resp.status}: {error_text}")
                    content_type = resp.headers.get("Content-Type", "")
                    if "application/json" not in content_type:
                        error_text = await resp.text()
                        logger.error(f"DeviceInfo: Invalid content-type {content_type} for {url}: {error_text}")
                        raise ValueError(f"Invalid content-type: {content_type}")
                    data = await resp.json()
                    if data is None:
                        error_text = await resp.text()
                        logger.error(f"DeviceInfo: API returned None for {url}: {error_text}")
                        if endpoint.startswith("search"):
                            data = []  
                        else:
                            data = {}  
                    if not isinstance(data, (list, dict)):
                        logger.error(f"DeviceInfo: Unexpected API response type for {url}: {type(data)}")
                        raise ValueError(f"Unexpected API response type: {type(data)}")
                    self.cache[cache_key] = data
                    logger.debug(f"Cache set for {cache_key}")
                    return data
            except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as e:
                logger.warning(f"DeviceInfo: Request failed for {endpoint} (attempt {attempt}): {e}")
                if attempt < self.config["retry_attempts"]:
                    if params and "message" in params:
                        await utils.answer(params["message"], self.strings["retrying"].format(attempt, self.config["retry_attempts"]))
                    await asyncio.sleep(2 * attempt)
                else:
                    logger.error(f"DeviceInfo: API failed after {self.config['retry_attempts']} attempts: {e}")
                    if endpoint.startswith("search"):
                        return []  
                    return {}  

    def _format_essential_info(self, device: Dict[str, Any]) -> str:
        """Format essential device info (name, network, launch, display, platform, battery)"""
        info_text = ""
        if "network" in device:
            info_text += self.strings["network"].format(self._safe_get(device, "network"))
        launched = device.get("launched", device.get("launced"))
        if launched:  
            info_text += self.strings["launched"].format(
                self._safe_get(launched, "announced"),
                self._safe_get(launched, "status")
            )
        if "display" in device:
            display = device.get("display", {})
            info_text += self.strings["display"].format(
                self._safe_get(display, "type"),
                self._safe_get(display, "size"),
                self._safe_get(display, "resolution"),
                self._safe_get(display, "protection")
            )
        if "platform" in device:
            platform = device.get("platform", {})
            info_text += self.strings["platform"].format(
                self._safe_get(platform, "os"),
                self._safe_get(platform, "chipset"),
                self._safe_get(platform, "cpu"),
                self._safe_get(platform, "gpu")
            )
        if "battery" in device:
            battery = device.get("battery", {})
            info_text += self.strings["battery"].format(
                self._safe_get(battery, "battType"),
                self._safe_get(battery, "charging")
            )
        return info_text

    def _format_section(self, section: str, device: Dict[str, Any]) -> str:
        """Format a specific section of device info"""
        if section == "body" and "body" in device:
            body = device.get("body", {})
            return self.strings["body"].format(
                self._safe_get(body, "dimension"),
                self._safe_get(body, "weight"),
                self._safe_get(body, "sim"),
                self._safe_get(body, "other")
            )
        if section == "memory" and "memory" in device:
            memory = {item.get("label", ""): item.get("value", "N/A") for item in device.get("memory", [])}
            return self.strings["memory"].format(
                self._safe_get(memory, "card"),
                self._safe_get(memory, "internal"),
                self._safe_get(memory, "otherMemory")
            )
        if section == "cameras":
            cam_text = ""
            if "mainCamera" in device:
                main = device.get("mainCamera", {})
                cam_text += self.strings["main_camera"].format(
                    self._safe_get(main, "mainModules"),
                    self._safe_get(main, "mainFeatures"),
                    self._safe_get(main, "mainVideo")
                )
            if "selfieCamera" in device:
                selfie = device.get("selfieCamera", {})
                cam_text += self.strings["selfie_camera"].format(
                    self._safe_get(selfie, "selfieModules"),
                    self._safe_get(selfie, "selfieFeatures"),
                    self._safe_get(selfie, "selfieVideo")
                )
            return cam_text
        if section == "sound" and "sound" in device:
            sound = device.get("sound", {})
            return self.strings["sound"].format(
                self._safe_get(sound, "loudSpeaker"),
                self._safe_get(sound, "audioJack"),
                self._safe_get(sound, "otherSound")
            )
        if section == "comms" and "comms" in device:
            comms = device.get("comms", {})
            return self.strings["comms"].format(
                self._safe_get(comms, "wlan"),
                self._safe_get(comms, "bluetooth"),
                self._safe_get(comms, "gps"),
                self._safe_get(comms, "nfc"),
                self._safe_get(comms, "infrared"),
                self._safe_get(comms, "radio"),
                self._safe_get(comms, "usb")
            )
        if section == "sensors" and "sensors" in device:
            return self.strings["sensors"].format(self._safe_get(device, "sensors"))
        if section == "misc" and "misc" in device:
            misc = device.get("misc", {})
            return self.strings["misc"].format(
                self._safe_get(misc, "colors"),
                self._safe_get(misc, "models")
            )
        return "N/A"

    @loader.command(ru_doc="(.di) <название устройства> - Получить информацию о смартфоне", alias="di")
    async def deviceinfo(self, message):
        """(.di) <device name> - Get smartphone info by name"""
        query = utils.get_args_raw(message).strip()
        if not query:
            await utils.answer(message, self.strings["no_query"])
            return

        await utils.answer(message, self.strings["searching"].format(query))
        try:
            devices = await self._fetch_json("search", {"q": query, "message": message})
            if not devices:  
                await utils.answer(message, self.strings["no_results"].format(query))
                return

            devices = devices[:self.config["max_results"]]
            button_rows = [[{"text": device["name"], "callback": self.show_device_info, "args": [device["id"], query, message.id, message.chat_id, 0, None]}] for device in devices]
            await self.inline.list(
                message=message,
                strings=[self.strings["device_list"].format(len(devices), query)],
                custom_buttons=button_rows,
                ttl=60,
                force_me=True,  
                manual_security=True,
                silent=True
            )
        except Exception as e:
            logger.error(f"DeviceInfo: Failed to fetch search results: {e}")
            await utils.answer(message, self.strings["error"].format(str(e)))

    async def show_device_info(self, call: InlineMessage, device_id: str, query: str, message_id: int, chat_id: int, photo_idx: int, prev_call_id: str = None):
        """Handle device selection and show essential info with buttons for details"""
        message = await self._resolve_entity(call, message_id, chat_id)
        
        try:
            device = await self._fetch_json(f"info/{device_id}", {"message": message})
            if not device:  
                raise ValueError("No device info returned")
            images_data = await self._fetch_json(f"images/{device_id}", {"message": message})
            images = images_data.get("images", []) if isinstance(images_data, dict) else []

            info_text = self._format_essential_info(device)
            full_text = self.strings["device_info"].format(device.get("name", "N/A"), info_text)

            # Truncate for media caption (Telegram limit: 1024 chars)
            caption = full_text[:1024] + ("..." if len(full_text) > 1024 else "") if images else full_text
            logger.debug(f"DeviceInfo: Caption length: {len(caption)} characters, photo_idx: {photo_idx}")

            # Buttons for additional sections and photo navigation
            buttons = [
                [
                    {"text": self.strings["show_body"], "callback": self.show_section, "args": ["body", device_id, query, message_id, chat_id, photo_idx]},
                    {"text": self.strings["show_memory"], "callback": self.show_section, "args": ["memory", device_id, query, message_id, chat_id, photo_idx]},
                ],
                [
                    {"text": self.strings["show_cameras"], "callback": self.show_section, "args": ["cameras", device_id, query, message_id, chat_id, photo_idx]},
                    {"text": self.strings["show_sound"], "callback": self.show_section, "args": ["sound", device_id, query, message_id, chat_id, photo_idx]},
                ],
                [
                    {"text": self.strings["show_comms"], "callback": self.show_section, "args": ["comms", device_id, query, message_id, chat_id, photo_idx]},
                    {"text": self.strings["show_sensors"], "callback": self.show_section, "args": ["sensors", device_id, query, message_id, chat_id, photo_idx]},
                ],
                [
                    {"text": self.strings["show_misc"], "callback": self.show_section, "args": ["misc", device_id, query, message_id, chat_id, photo_idx]},
                ],
                [
                    {"text": self.strings["prev_photo"], "callback": self.show_device_info, "args": [device_id, query, message_id, chat_id, max(0, photo_idx - 1), call.id]} if photo_idx > 0 else None,
                    {"text": self.strings["next_photo"], "callback": self.show_device_info, "args": [device_id, query, message_id, chat_id, min(len(images) - 1, photo_idx + 1), call.id]} if images and photo_idx < len(images) - 1 else None,
                    {"text": self.strings["back"], "callback": self.back_to_search, "args": [query, message_id, chat_id]},
                ]
            ]
            # Filter out None buttons
            buttons = [[btn for btn in row if btn] for row in buttons if any(row)]

            # Always edit the message (for device selection or photo navigation)
            logger.debug(f"DeviceInfo: Editing message for device_id: {device_id}, photo_idx: {photo_idx}, call_id: {call.id}")
            await call.edit(
                text=caption,
                reply_markup=buttons,
                photo=images[photo_idx] if images else None,
                disable_web_page_preview=True
            )
        except Exception as e:
            logger.error(f"DeviceInfo: Failed to show device info: {e}")
            await call.edit(
                text=self.strings["error"].format(str(e)),
                reply_markup=[],
                disable_web_page_preview=True
            )

    async def show_section(self, call: InlineMessage, section: str, device_id: str, query: str, message_id: int, chat_id: int, photo_idx: int):
        """Show a specific section of device info"""
        message = await self._resolve_entity(call, message_id, chat_id)
        
        try:
            device = await self._fetch_json(f"info/{device_id}", {"message": message})
            if not device:
                raise ValueError("No device info returned")
            
            section_text = self._format_section(section, device)
            full_text = self.strings["device_info"].format(device.get("name", "N/A"), section_text)

            # Truncate for Telegram message limit (4000 chars)
            full_text = full_text[:4000] + ("..." if len(full_text) > 4000 else "")

            # Buttons for returning to device info
            buttons = [
                [{"text": self.strings["back_to_device"], "callback": self.show_device_info, "args": [device_id, query, message_id, chat_id, photo_idx, call.id]}]
            ]

            # Try to edit the message
            try:
                logger.debug(f"DeviceInfo: Editing message for section: {section}, call_id: {call.id}")
                await call.edit(
                    text=full_text,
                    reply_markup=buttons,
                    photo=None,  # Sections don't include photos to avoid media/text mismatch
                    disable_web_page_preview=True
                )
            except Exception as edit_error:
                logger.warning(f"DeviceInfo: Failed to edit message for section {section}: {edit_error}")
                # Fallback to new inline form if edit fails
                await self.inline.form(
                    text=full_text,
                    message=message,
                    reply_markup=buttons,
                    ttl=300,
                    force_me=True,
                    silent=True
                )
        except Exception as e:
            logger.error(f"DeviceInfo: Failed to show section {section}: {e}")
            try:
                await call.edit(
                    text=self.strings["error"].format(str(e)),
                    reply_markup=[],
                    disable_web_page_preview=True
                )
            except Exception as edit_error:
                logger.warning(f"DeviceInfo: Failed to edit error message: {edit_error}")
                await self.inline.form(
                    text=self.strings["error"].format(str(e)),
                    message=message,
                    silent=True
                )

    async def back_to_search(self, call: InlineMessage, query: str, message_id: int, chat_id: int):
        """Handle 'Back' button to return to search results"""
        message = await self._resolve_entity(call, message_id, chat_id)
        
        try:
            devices = await self._fetch_json("search", {"q": query, "message": message})
            logger.debug(f"DeviceInfo: Fetched {len(devices)} devices for query: {query}")
            if not devices:  
                logger.warning(f"DeviceInfo: No devices found for query: {query}")
                try:
                    await call.edit(
                        text=self.strings["no_results"].format(query),
                        reply_markup=[],
                        photo=None,
                        disable_web_page_preview=True
                    )
                except Exception as edit_error:
                    logger.warning(f"DeviceInfo: Failed to edit no_results message: {edit_error}")
                    await self.inline.form(
                        text=self.strings["no_results"].format(query),
                        message=message,
                        silent=True
                    )
                return

            devices = devices[:self.config["max_results"]]
            button_rows = [[{"text": device["name"], "callback": self.show_device_info, "args": [device["id"], query, message_id, chat_id, 0, None]}] for device in devices]
            list_text = self.strings["device_list"].format(len(devices), query)

            # Try to edit the message
            try:
                logger.debug(f"DeviceInfo: Editing message for back_to_search, query: {query}, call_id: {call.id}")
                await call.edit(
                    text=list_text,
                    reply_markup=button_rows,
                    photo=None,
                    disable_web_page_preview=True
                )
            except Exception as edit_error:
                logger.warning(f"DeviceInfo: Failed to edit back_to_search message: {edit_error}")
                await self.inline.list(
                    message=message_id,
                    strings=[list_text],
                    custom_buttons=button_rows,
                    ttl=60,
                    force_me=True,
                    manual_security=True,
                    silent=True
                )
        except Exception as e:
            logger.error(f"DeviceInfo: Failed to return to search: {e}")
            try:
                await call.edit(
                    text=self.strings["error"].format(str(e)),
                    reply_markup=[],
                    photo=None,
                   disable_web_page_preview=True
                )
            except Exception as edit_error:
                logger.warning(f"DeviceInfo: Failed to edit error message: {edit_error}")
                await self.inline.form(
                    text=self.strings["error"].format(str(e)),
                    message=message,
                    silent=True
                )