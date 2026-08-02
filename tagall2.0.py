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
# meta fhsdesc: tool, tools, admin, tag, alltag, tagall

from .. import loader, utils
from telethon.tl.types import ChannelParticipantsAdmins, UserStatusRecently, UserStatusOnline, Message
import typing
import asyncio
import logging

logger = logging.getLogger(__name__)

@loader.tds
class TagAllMod(loader.Module):
    """TagAll 2.0 — smart mention of chat participants: .tagall {all/admins/online/active} {text}"""

    strings = {
        "name": "TagAll 2.0",
        "done": "✅ <b>{}</b> users mentioned",
        "no_users": "⚠️ No users found matching this filter",
        "invalid_args": "❌ Invalid command format. Use: .tagall {all/admins/online/active} {text}",
        "confirm": "⚠️ This will send <b>{}</b> messages to <b>{}</b>. Continue? (yes/no)",
        "cancelled": "❌ Canceled.",
        "invalid_confirm": "❌ Please reply with <b>yes</b> or <b>no</b>.",
    }

    strings_ru = {
        "_cls_doc": "TagAll 2.0 — умное упоминание участников чата: .tagall {all/admins/online/active} {текст}",
        "done": "✅ Упомянуто <b>{}</b> пользователей",
        "no_users": "⚠️ Не найдено пользователей по данному фильтру",
        "invalid_args": "❌ Неверный формат команды. Используйте: .tagall {all/admins/online/active} {текст}",
        "confirm": "⚠️ Будет отправлено <b>{}</b> сообщений в <b>{}</b>. Продолжить? (да/нет)",
        "cancelled": "❌ Отменено.",
        "invalid_confirm": "❌ Ответьте <b>да</b> или <b>нет</b>.",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "batch_size",
                5,
                lambda: "How many users to mention per message",
                validator=loader.validators.Integer(minimum=1, maximum=20),
            ),
            loader.ConfigValue(
                "delay",
                2,
                lambda: "Delay between messages (seconds)",
                validator=loader.validators.Integer(minimum=0, maximum=30),
            ),
            loader.ConfigValue(
                "confirm_threshold",
                10,
                lambda: "Messages count at which to ask for confirmation",
                validator=loader.validators.Integer(minimum=1, maximum=100),
            ),
        )

    async def client_ready(self, client, db):
        self.client = client

    @loader.command(ru_doc="Упомянуть участников: .tagall {all/admins/online/active} {текст}")
    async def tagallcmd(self, message: Message):
        """Mention members: .tagall {all/admins/online/active} {text}"""
        args = utils.get_args_raw(message).split(maxsplit=1)
        mode = args[0].lower() if args else None
        text = args[1] if len(args) > 1 else "Срочное собрание!"

        valid_modes = {"all", "admins", "online", "active"}

        if mode not in valid_modes:
            await utils.answer(message, self.strings["invalid_args"])
            return

        chat = await self.client.get_entity(message.chat_id)
        users = await self._collect_users(chat, mode)
        if not users:
            await utils.answer(message, self.strings["no_users"])
            return

        batch_size = self.config["batch_size"]
        messages_count = -(-len(users) // batch_size)
        if messages_count > self.config["confirm_threshold"]:
            confirm = await self._ask_confirmation(message, messages_count, utils.escape_html(getattr(chat, "title", None) or chat.id))
            if confirm is None:
                return
            if not confirm:
                await utils.answer(message, self.strings["cancelled"])
                return

        tagged = await self._send_mentions(chat, text, users, batch_size)
        await utils.answer(message, self.strings["done"].format(tagged))

    async def _ask_confirmation(self, message, messages_count: int, chat_name) -> typing.Optional[bool]:
        status = await utils.answer(message, self.strings["confirm"].format(messages_count, chat_name))
        try:
            async with self.client.conversation(message.chat_id, timeout=30) as conv:
                response = await conv.get_response()
                answer = utils.get_args_raw(response).lower().strip()
                if answer in {"yes", "да", "y", "д"}:
                    return True
                if answer in {"no", "нет", "n", "н"}:
                    return False
                await conv.send_message(self.strings["invalid_confirm"])
                return None
        except Exception as e:
            logger.debug(f"Confirmation timeout or error: {e}")
            await utils.answer(message, self.strings["cancelled"])
            return None

    async def _collect_users(self, chat, filter_: str):
        users = []
        try:
            if filter_ == "all":
                async for user in self.client.iter_participants(chat):
                    if not user.bot:
                        users.append(user)

            elif filter_ == "admins":
                async for user in self.client.iter_participants(chat, filter=ChannelParticipantsAdmins):
                    if not user.bot:
                        users.append(user)

            elif filter_ == "online":
                async for user in self.client.iter_participants(chat):
                    if not user.bot and isinstance(user.status, (UserStatusRecently, UserStatusOnline)):
                        users.append(user)

            elif filter_ == "active":
                user_ids = set()
                async for msg in self.client.iter_messages(chat, limit=50):
                    if msg.sender_id and msg.sender_id not in user_ids:
                        try:
                            user = await self.client.get_entity(msg.sender_id)
                            if not user.bot:
                                users.append(user)
                                user_ids.add(msg.sender_id)
                        except Exception as e:
                            logger.debug(f"Failed to resolve user {msg.sender_id}: {e}")
                            continue
        except Exception as e:
            logger.error(f"Error collecting users in tagall: {e}")
            return []
        return users

    async def _send_mentions(self, chat, text: str, users, batch_size: int) -> int:
        tagged = 0
        delay = self.config["delay"]
        for i in range(0, len(users), batch_size):
            batch = users[i:i + batch_size]
            mentions = " ".join([f"<a href='tg://user?id={u.id}'>{utils.escape_html(u.first_name) or 'User'}</a>" for u in batch])
            msg_text = f"<b>{utils.escape_html(text)}</b>\n{mentions}" if text else mentions
            await self.client.send_message(chat, msg_text, link_preview=False, parse_mode="html")
            tagged += len(batch)
            if i + batch_size < len(users):
                await asyncio.sleep(delay)
        return tagged