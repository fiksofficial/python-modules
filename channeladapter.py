# На модуль распространяется лицензия "GNU General Public License v3.0
# https://github.com/all-licenses/GNU-General-Public-License-v3.0

# meta developer: @PyModule
# meta fhsdesc: tool, tools, channel, admintools, admin, admintool
from telethon.tl.types import Message
from .. import loader, utils
import logging

logger = logging.getLogger(__name__)

@loader.tds
class ChannelAdapterMod(loader.Module):
    """Модуль для добавления переходника в сообщения каналов"""
    strings = {
        "name": "ChannelAdapter",
        "_cls_doc": "Модуль для добавления переходника в сообщения каналов",
        "no_channel_id": "<emoji document_id=6030563507299160824>❗️</emoji> <b>Укажите ID канала.</b>",
        "no_text": "<emoji document_id=6030563507299160824>❗️</emoji> <b>Укажите текст переходника.</b>",
        "added": "<emoji document_id=5774022692642492953>✅</emoji> <b>Переходник добавлен для канала:</b> <code>{}</code> - {}",
        "not_found": "<emoji document_id=5774077015388852135>❌</emoji> <b>Этот канал не найден в списке.</b>",
        "deleted": "<emoji document_id=5774022692642492953>✅</emoji> <b>Переходник для канала <code>{}</code> удалён.</b>",
        "empty": "<emoji document_id=5774077015388852135>❌</emoji> <b>Нет сохранённых переходников.</b>",
        "list_header": "<blockquote><emoji document_id=5253959125838090076>👁</emoji> <b>Список сохранённых переходников</b></blockquote>\n\n\n",
        "list_item": "<emoji document_id=6032924188828767321>➕</emoji> <b><code>{}</code>:</b> {}\n\n",
        "nothing_to_clear": "<emoji document_id=5774077015388852135>❌</emoji> <b>Нет переходников для удаления.</b>",
        "cleared": "<emoji document_id=5774022692642492953>✅</emoji> <b>Все адаптеры были удалены.</b>",
        "watcher_error": "<emoji document_id=6030563507299160824>❗️</emoji> <b>Ошибка в ChannelAdapter:</b>\n`{}`",
    }

    strings_ru = {
        "_cls_doc": "Модуль для добавления переходника в сообщения каналов",
        "no_channel_id": "<emoji document_id=6030563507299160824>❗️</emoji> <b>Укажите ID канала.</b>",
        "no_text": "<emoji document_id=6030563507299160824>❗️</emoji> <b>Укажите текст переходника.</b>",
        "added": "<emoji document_id=5774022692642492953>✅</emoji> <b>Переходник добавлен для канала:</b> <code>{}</code> - {}",
        "not_found": "<emoji document_id=5774077015388852135>❌</emoji> <b>Этот канал не найден в списке.</b>",
        "deleted": "<emoji document_id=5774022692642492953>✅</emoji> <b>Переходник для канала <code>{}</code> удалён.</b>",
        "empty": "<emoji document_id=5774077015388852135>❌</emoji> <b>Нет сохранённых переходников.</b>",
        "list_header": "<blockquote><emoji document_id=5253959125838090076>👁</emoji> <b>Список сохранённых переходников</b></blockquote>\n\n\n",
        "list_item": "<emoji document_id=6032924188828767321>➕</emoji> <b><code>{}</code>:</b> {}\n\n",
        "nothing_to_clear": "<emoji document_id=5774077015388852135>❌</emoji> <b>Нет переходников для удаления.</b>",
        "cleared": "<emoji document_id=5774022692642492953>✅</emoji> <b>Все адаптеры были удалены.</b>",
        "watcher_error": "<emoji document_id=6030563507299160824>❗️</emoji> <b>Ошибка в ChannelAdapter:</b>\n`{}`",
    }

    async def client_ready(self, client, db):
        self.client = client
        self.db = db
        if not self.db.get(__name__, "adapters"):
            self.db.set(__name__, "adapters", {})

    def get_adapters(self):
        """Получает адаптеры из базы данных"""
        return self.db.get(__name__, "adapters", {})

    def save_adapters(self, adapters):
        """Сохраняет адаптеры в базу данных"""
        self.db.set(__name__, "adapters", adapters)

    @loader.command(ru_doc="[ID канала] [Текст] - Добавить канал и переходник")
    async def addadaptercmd(self, message: Message):
        """[CHANNEL ID] [Текст] - Добавить канал и переходник."""
        args = utils.get_args_raw(message).split()
        if len(args) < 2:
            await utils.answer(message, self.strings("no_channel_id"))
            return

        chat_id = args[0]
        adapter_text = " ".join(args[1:])

        if not adapter_text:
            await utils.answer(message, self.strings("no_text"))
            return

        adapters = self.get_adapters()
        adapters[chat_id] = adapter_text
        self.save_adapters(adapters)

        await utils.answer(message, self.strings("added").format(chat_id, adapter_text))

    @loader.command(ru_doc="[ID канала] - Удалить переходник для канала")
    async def deladaptercmd(self, message: Message):
        """[CHANNEL ID] - Удалить переходник для канала."""
        args = utils.get_args_raw(message).split()
        if len(args) < 1:
            await utils.answer(message, self.strings("no_channel_id"))
            return

        chat_id = args[0]
        adapters = self.get_adapters()

        if chat_id not in adapters:
            await utils.answer(message, self.strings("not_found"))
            return

        del adapters[chat_id]
        self.save_adapters(adapters)

        await utils.answer(message, self.strings("deleted").format(chat_id))

    @loader.command(ru_doc="- Показать список всех переходников")
    async def listadapterscmd(self, message: Message):
        """- Показать список всех переходников."""
        adapters = self.get_adapters()
        if not adapters:
            await utils.answer(message, self.strings("empty"))
            return

        text = self.strings("list_header")
        for chat_id, adapter_text in adapters.items():
            text += self.strings("list_item").format(chat_id, adapter_text)

        await utils.answer(message, text)

    @loader.command(ru_doc="- Удалить все переходники")
    async def clearadapterscmd(self, message: Message):
        """- Удалить все переходники."""
        adapters = self.get_adapters()
        if not adapters:
            await utils.answer(message, self.strings("nothing_to_clear"))
            return

        self.db.set(__name__, "adapters", {})
        await utils.answer(message, self.strings("cleared"))

    async def watcher(self, message: Message):
        """Автоматически добавляет переходник в сообщения каналов"""
        if not message or not message.out:
            return

        adapters = self.get_adapters()
        adapter_text = adapters.get(str(message.chat_id), None)

        if not adapter_text:
            return

        try:
            if message.text:
                modified_text = f"{message.text}\n\n{adapter_text}"
                await message.edit(modified_text, parse_mode='html')
            elif message.media:
                modified_caption = f"{message.text}\n\n{adapter_text}" if message.text else adapter_text
                await message.edit(text=modified_caption, parse_mode='html')
        except Exception as e:
            logger.exception("Error in ChannelAdapter watcher: %s", e)
            me = await self.client.get_me()
            await self.client.send_message(me.id, self.strings("watcher_error").format(str(e)))
