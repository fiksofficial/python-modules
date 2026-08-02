# На модуль распространяется лицензия "GNU General Public License v3.0"
# https://github.com/all-licenses/GNU-General-Public-License-v3.0

# meta developer: @PyModule
# meta fhsdesc: fun, rp, rpgame
# requires: toml
import os
from .. import loader, utils
from telethon.tl.types import Channel
import toml
import logging

logger = logging.getLogger(__name__)


# noinspection PyCallingNonCallable
@loader.tds
class IrisRP(loader.Module):
    """РП команды как в боте Ирис."""

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "action_decoration",
                'normal | без стилей',
                lambda: "Декорация для действия РП-команды",
                validator=loader.validators.Choice(
                    [
                        "normal | без стилей",
                        "bold | полужирный",
                        "italic | курсив",
                        "underlined | подчёркнутый",
                        "strikethrough | зачёркнутый",
                        "spoiler | скрытый",
                    ]
                ),
            ),

            loader.ConfigValue(
                "replica_decoration",
                'normal | без стилей',
                lambda: "Декорация для реплики РП-команды",
                validator=loader.validators.Choice(
                    [
                        "normal | без стилей",
                        "bold | полужирный",
                        "italic | курсив",
                        "underlined | подчёркнутый",
                        "strikethrough | зачёркнутый",
                        "spoiler | скрытый",
                    ]
                ),
            ),

            loader.ConfigValue(
                "speech_bubble",
                '💬',
                lambda: "Эмодзи речевого пузыря для «с репликой»",
                validator=loader.validators.String()
            )
        )

    strings = {
        'name': 'IrisRP',
        '_cls_doc': 'RP commands like in the Iris bot.',
        "no_data": "<emoji document_id=5774077015388852135>❌</emoji> <b>Вы не указали никаких данных.</b>",
        "invalid_format": "<emoji document_id=5774077015388852135>❌</emoji> <b>Неверный формат. Используйте: команда / действие / эмодзи</b>",
        "bad_words_count": "<emoji document_id=5774077015388852135>❌</emoji> <b>Команда должна содержать от 1 до 3 слов.</b>",
        "no_action": "<emoji document_id=5774077015388852135>❌</emoji> <b>Вы не указали действие команды.</b>",
        "reserved_all": '<emoji document_id=5774077015388852135>❌</emoji> <b>РП-команды не могут называться "all"</b>',
        "no_emoji": "<emoji document_id=5774077015388852135>❌</emoji> <b>Вы не указали эмодзи.</b>",
        "added": "<emoji document_id=5774022692642492953>✅</emoji> <b>Команда <code>{}</code> успешно добавлена",
        "added_emoji": " с эмодзи {}",
        "added_dot": ".</b>",
        "all_cleared": "<emoji document_id=5774022692642492953>✅</emoji> <b>Все РП команды успешно очищены.</b>",
        "no_command": "<emoji document_id=5774077015388852135>❌</emoji> <b>Вы не указали команду для удаления.</b>",
        "deleted": "<emoji document_id=5774022692642492953>✅</emoji> <b>Команда <code>{}</code> успешно удалена.</b>",
        "not_found": "<emoji document_id=5774077015388852135>❌</emoji> <b>Команда <code>{}</code> не найдена.</b>",
        "rp_disabled": "<emoji document_id=5253959125838090076>👁</emoji> <b>РП команды теперь выключены.</b>",
        "rp_enabled": "<emoji document_id=5253959125838090076>👁</emoji> <b>РП команды теперь включены.</b>",
        "count": "<emoji document_id=5253959125838090076>👁</emoji> <b>У вас {} команд.</b>",
        "count_zero": "<emoji document_id=5253959125838090076>👁</emoji> <b>У вас 0 команд.</b>",
        "backup_error": "<emoji document_id=5774077015388852135>❌</emoji> <b>Ошибка при создании бэкапа:</b>\n<code>{}</code>",
        "no_file": "<emoji document_id=5774077015388852135>❌</emoji> <b>В ответе нет файла.</b>",
        "corrupted_file": "<emoji document_id=5774077015388852135>❌</emoji> <b>Файл поврежден или не является бэкапом.</b>",
        "bad_backup": "<emoji document_id=5774077015388852135>❌</emoji> <b>Неверный формат бэкапа.</b>",
        "replaced": "<emoji document_id=5774022692642492953>✅</emoji> <b>РП команды успешно заменены из бэкапа.</b>",
        "added_backup": "<emoji document_id=5774022692642492953>✅</emoji> <b>РП команды успешно добавлены из бэкапа.</b>",
        "load_error": "<emoji document_id=5774077015388852135>❌</emoji> <b>Ошибка при загрузке бэкапа:</b>\n<code>{}</code>",
        "chat_on": "<emoji document_id=5774022692642492953>✅</emoji> <b>Доступ к РП-командам включен для чата {}</b>",
        "chat_off": "<emoji document_id=5774022692642492953>✅</emoji> <b>Доступ к РП-командам отключен для чата {}</b>",
        "list_header": "<b><emoji document_id=5253959125838090076>👁</emoji> Список доступов к РП командам:</b>",
        "no_accesses": "<emoji document_id=6028435952299413210>ℹ</emoji> <b>Нет ни пользователей, ни чатов с доступом к РП-командам</b>",
        "chats_header": "\n\n<emoji document_id=6037421444789440735>💬</emoji> <b>Чаты с доступом:</b>",
        "no_chats": "\n\n<emoji document_id=6028435952299413210>ℹ</emoji> <b>Нет чатов с доступом</b>",
        "users_header": "\n\n<emoji document_id=6035084557378654059>👤</emoji> <b>Пользователи с доступом:</b>",
        "no_users": "\n\n<emoji document_id=6028435952299413210>ℹ</emoji> <b>Нет пользователей с доступом</b>",
        "access_off_chat": "<emoji document_id=5774022692642492953>✅</emoji> <b>Доступ отключен для чата {}</b>",
        "access_on_chat": "<emoji document_id=5774022692642492953>✅</emoji> <b>Доступ включен для чата {}</b>",
        "access_off_user": "<emoji document_id=5774022692642492953>✅</emoji> <b>Доступ отключен для пользователя {}</b>",
        "access_on_user": "<emoji document_id=5774022692642492953>✅</emoji> <b>Доступ включен для пользователя {}</b>",
        "error": "<emoji document_id=5774077015388852135>❌</emoji> <b>Ошибка:</b> {}",
        "rpa_usage": (
            "<blockquote><emoji document_id=6028435952299413210>ℹ</emoji> <b>Используйте:</b></blockquote>\n"
            "<code>.rpa</code> <b>в чате - для управления доступом чата.</b>\n"
            "<code>.rpa [ID]</code> <b>- для управления по ID.</b>\n"
            "<code>.rpa</code> <b>в ответ на сообщение - для управления пользователем.</b>\n"
            "<code>.rpa -l</code> <b>- чтобы показать список доступов.</b>"
        ),
    }

    strings_ru = {
        '_cls_doc': 'РП команды как в боте Ирис.',
        "no_data": "<emoji document_id=5774077015388852135>❌</emoji> <b>Вы не указали никаких данных.</b>",
        "invalid_format": "<emoji document_id=5774077015388852135>❌</emoji> <b>Неверный формат. Используйте: команда / действие / эмодзи</b>",
        "bad_words_count": "<emoji document_id=5774077015388852135>❌</emoji> <b>Команда должна содержать от 1 до 3 слов.</b>",
        "no_action": "<emoji document_id=5774077015388852135>❌</emoji> <b>Вы не указали действие команды.</b>",
        "reserved_all": '<emoji document_id=5774077015388852135>❌</emoji> <b>РП-команды не могут называться "all"</b>',
        "no_emoji": "<emoji document_id=5774077015388852135>❌</emoji> <b>Вы не указали эмодзи.</b>",
        "added": "<emoji document_id=5774022692642492953>✅</emoji> <b>Команда <code>{}</code> успешно добавлена",
        "added_emoji": " с эмодзи {}",
        "added_dot": ".</b>",
        "all_cleared": "<emoji document_id=5774022692642492953>✅</emoji> <b>Все РП команды успешно очищены.</b>",
        "no_command": "<emoji document_id=5774077015388852135>❌</emoji> <b>Вы не указали команду для удаления.</b>",
        "deleted": "<emoji document_id=5774022692642492953>✅</emoji> <b>Команда <code>{}</code> успешно удалена.</b>",
        "not_found": "<emoji document_id=5774077015388852135>❌</emoji> <b>Команда <code>{}</code> не найдена.</b>",
        "rp_disabled": "<emoji document_id=5253959125838090076>👁</emoji> <b>РП команды теперь выключены.</b>",
        "rp_enabled": "<emoji document_id=5253959125838090076>👁</emoji> <b>РП команды теперь включены.</b>",
        "count": "<emoji document_id=5253959125838090076>👁</emoji> <b>У вас {} команд.</b>",
        "count_zero": "<emoji document_id=5253959125838090076>👁</emoji> <b>У вас 0 команд.</b>",
        "backup_error": "<emoji document_id=5774077015388852135>❌</emoji> <b>Ошибка при создании бэкапа:</b>\n<code>{}</code>",
        "no_file": "<emoji document_id=5774077015388852135>❌</emoji> <b>В ответе нет файла.</b>",
        "corrupted_file": "<emoji document_id=5774077015388852135>❌</emoji> <b>Файл поврежден или не является бэкапом.</b>",
        "bad_backup": "<emoji document_id=5774077015388852135>❌</emoji> <b>Неверный формат бэкапа.</b>",
        "replaced": "<emoji document_id=5774022692642492953>✅</emoji> <b>РП команды успешно заменены из бэкапа.</b>",
        "added_backup": "<emoji document_id=5774022692642492953>✅</emoji> <b>РП команды успешно добавлены из бэкапа.</b>",
        "load_error": "<emoji document_id=5774077015388852135>❌</emoji> <b>Ошибка при загрузке бэкапа:</b>\n<code>{}</code>",
        "chat_on": "<emoji document_id=5774022692642492953>✅</emoji> <b>Доступ к РП-командам включен для чата {}</b>",
        "chat_off": "<emoji document_id=5774022692642492953>✅</emoji> <b>Доступ к РП-командам отключен для чата {}</b>",
        "list_header": "<b><emoji document_id=5253959125838090076>👁</emoji> Список доступов к РП командам:</b>",
        "no_accesses": "<emoji document_id=6028435952299413210>ℹ</emoji> <b>Нет ни пользователей, ни чатов с доступом к РП-командам</b>",
        "chats_header": "\n\n<emoji document_id=6037421444789440735>💬</emoji> <b>Чаты с доступом:</b>",
        "no_chats": "\n\n<emoji document_id=6028435952299413210>ℹ</emoji> <b>Нет чатов с доступом</b>",
        "users_header": "\n\n<emoji document_id=6035084557378654059>👤</emoji> <b>Пользователи с доступом:</b>",
        "no_users": "\n\n<emoji document_id=6028435952299413210>ℹ</emoji> <b>Нет пользователей с доступом</b>",
        "access_off_chat": "<emoji document_id=5774022692642492953>✅</emoji> <b>Доступ отключен для чата {}</b>",
        "access_on_chat": "<emoji document_id=5774022692642492953>✅</emoji> <b>Доступ включен для чата {}</b>",
        "access_off_user": "<emoji document_id=5774022692642492953>✅</emoji> <b>Доступ отключен для пользователя {}</b>",
        "access_on_user": "<emoji document_id=5774022692642492953>✅</emoji> <b>Доступ включен для пользователя {}</b>",
        "error": "<emoji document_id=5774077015388852135>❌</emoji> <b>Ошибка:</b> {}",
        "rpa_usage": (
            "<blockquote><emoji document_id=6028435952299413210>ℹ</emoji> <b>Используйте:</b></blockquote>\n"
            "<code>.rpa</code> <b>в чате - для управления доступом чата.</b>\n"
            "<code>.rpa [ID]</code> <b>- для управления по ID.</b>\n"
            "<code>.rpa</code> <b>в ответ на сообщение - для управления пользователем.</b>\n"
            "<code>.rpa -l</code> <b>- чтобы показать список доступов.</b>"
        ),
    }

    async def client_ready(self, client, db):
        self.db = db
        self._me = await client.get_me()

        if not self.db.get("RPMod", "exlist", False):
            self.db.set("RPMod", "exlist", [])

        if not self.db.get("RPMod", "status", False):
            self.db.set("RPMod", "status", 1)

        if not self.db.get("RPMod", "rpcomands", False):
            self.db.set("RPMod", "rpcomands", {})

        if not self.db.get("RPMod", "rpemoji", False):
            self.db.set("RPMod", "rpemoji", {})

        if not self.db.get("RPMod", "nrpcommands", False):
            if self.db.get("RPMod", "rpcomands", False):
                commands_old = self.db.get("RPMod", "rpcomands")
                emoji_old = self.db.get("RPMod", "rpemoji")
                commands_new = {}
                for key in commands_old:
                    try:
                        commands_new[key] = [commands_old[key], emoji_old[key]]
                    except KeyError:
                        commands_new[key] = [commands_old[key], '']
                self.db.set("RPMod", "nrpcommands", commands_new)

            else:
                self.db.set("RPMod", "nrpcommands", {})

        useraccept = self.db.get("RPMod", "useraccept", False)
        if not useraccept:
            self.db.set("RPMod", "useraccept", {"chats": [], "users": []})

        elif isinstance(useraccept, list):
            self.db.set(
                "RPMod",
                "useraccept",
                {"chats": [], "users": useraccept},
            )

    async def addrpcmd(self, message):
        """[команда (1-3 слова)] / [действие] / (эмодзи) - Создать РП команду."""
        args = utils.get_args_raw(message)
        dict_rp = self.db.get("RPMod", "nrpcommands", {})

        if not args or not args.strip():
            await utils.answer(message, self.strings("no_data"))
            return

        try:
            if '/' not in args:
                await utils.answer(message, self.strings("invalid_format"))
                return

            parts = [part.strip() for part in args.split("/", maxsplit=2)]

            if len(parts) < 2:
                await utils.answer(message, self.strings("invalid_format"))
                return

            key_rp = parts[0].casefold()
            words_count = len(key_rp.split())

            if words_count < 1 or words_count > 3:
                await utils.answer(message, self.strings("bad_words_count"))
                return

            value_rp = parts[1]
            if not value_rp.strip():
                await utils.answer(message, self.strings("no_action"))
                return

            if key_rp == "all":
                await utils.answer(message, self.strings("reserved_all"))
                return

            emoji_rp = ""
            if len(args.split("/")) >= 3:
                emoji_rp = str(message.text.split("/", maxsplit=2)[2]).strip()

                if not emoji_rp or not emoji_rp.strip():
                    await utils.answer(message, self.strings("no_emoji"))
                    return

            dict_rp[key_rp] = [value_rp, emoji_rp.strip()]
            self.db.set("RPMod", "nrpcommands", dict_rp)

            response = self.strings("added").format(key_rp)
            if emoji_rp:
                response += self.strings("added_emoji").format(emoji_rp)
            response += self.strings("added_dot")

            await utils.answer(message, response)

        except Exception as e:
            logger.exception("Error in addrp: %s", e)
            await utils.answer(message, self.strings("invalid_format"))

    async def delrpcmd(self, message):
        """[команда / all] - Удалить РП команду."""
        dict_rp = self.db.get("RPMod", "nrpcommands")
        args = utils.get_args_raw(message)
        key_rp = str(args)

        if key_rp == "all":
            dict_rp.clear()
            self.db.set("RPMod", "nrpcommands", dict_rp)
            await utils.answer(message, self.strings("all_cleared"))
            return

        elif not key_rp or not key_rp.strip():
            await utils.answer(message, self.strings("no_command"))

        else:
            try:
                dict_rp.pop(key_rp)
                self.db.set("RPMod", "nrpcommands", dict_rp)
                await utils.answer(message, self.strings("deleted").format(key_rp))
            except KeyError:
                await utils.answer(message, self.strings("not_found").format(key_rp))

    async def rptogglecmd(self, message):
        """- Включить/Выключить РП команды."""
        status = self.db.get("RPMod", "status")
        if status == 1:
            self.db.set("RPMod", "status", 2)
            await utils.answer(message, self.strings("rp_disabled"))
        else:
            self.db.set("RPMod", "status", 1)
            await utils.answer(message, self.strings("rp_enabled"))

    async def rplistcmd(self, message):
        """- Список все ваших команд."""
        com = self.db.get("RPMod", "nrpcommands")

        coms_amount = len(com)

        if len(com) == 0:
            await utils.answer(message, self.strings("count_zero"))
            return

        com_list = self.strings("count").format(coms_amount)

        for i in com:
            if com[i][1] != '':
                com_list += f"\n•   <b><code>{i}</code> - {com[i][0]} |</b> {com[i][1]}"
            else:
                com_list += f"\n•   <b><code>{i}</code> - {com[i][0]}</b>"

        await utils.answer(message, com_list)

    async def rpbackcmd(self, message):
        """(all) - Сохранить или загрузить список РП команд. All используется для замены всех команд."""
        commands = self.db.get("RPMod", "nrpcommands")
        mes_id = message.to_id
        file_name = f"IrisRP_{self._me.id}.toml"

        reply = await message.get_reply_message()
        args = utils.get_args_raw(message)

        replace_commands = "all" in args

        if not reply:
            try:
                await message.delete()
                with open(file_name, "w") as f:
                    toml.dump(commands, f)
                await message.client.send_file(mes_id, file_name)
                os.remove(file_name)
            except Exception as e:
                logger.exception("Error creating backup: %s", e)
                await utils.answer(message, self.strings("backup_error").format(e))
        else:
            if not reply.document:
                await utils.answer(message, self.strings("no_file"))
                return

            try:
                await reply.download_media(file_name)

                with open(file_name, "r") as f:
                    try:
                        data = toml.load(f)
                    except toml.TomlDecodeError:
                        os.remove(file_name)
                        return await utils.answer(message, self.strings("corrupted_file"))

                for key in data.keys():
                    if not isinstance(data[key], list) or len(data[key]) != 2:
                        os.remove(file_name)
                        return await utils.answer(message, self.strings("bad_backup"))

                if replace_commands:
                    self.db.set("RPMod", "nrpcommands", data)
                    os.remove(file_name)
                    await utils.answer(message, self.strings("replaced"))
                else:
                    updated_commands = {**commands, **data}
                    self.db.set("RPMod", "nrpcommands", updated_commands)
                    os.remove(file_name)
                    await utils.answer(message, self.strings("added_backup"))

            except Exception as e:
                if os.path.exists(file_name):
                    os.remove(file_name)
                logger.exception("Error loading backup: %s", e)
                await utils.answer(message, self.strings("load_error").format(e))

    async def rpacmd(self, message):
        """(ID/Reply) - Разрешить или запретить доступ к РП командам. Для подробностей напишите .rpa"""

        reply = await message.get_reply_message()
        args = utils.get_args_raw(message)
        user_a = self.db.get("RPMod", "useraccept")

        if not reply and not args and message.is_group:
            chat = message.chat
            if chat.id not in user_a["chats"]:
                user_a["chats"].append(chat.id)
                return await utils.answer(message, self.strings("chat_on").format(chat.title))
            else:
                user_a["chats"].remove(chat.id)
                return await utils.answer(message, self.strings("chat_off").format(chat.title))

        elif args.lower() in ("-l", "л", "list", "список"):
            sms = self.strings("list_header")

            if not user_a["chats"] and not user_a["users"]:
                return await utils.answer(message, self.strings("no_accesses"))

            if user_a["chats"]:
                sms += self.strings("chats_header")
                for chat_id in user_a["chats"]:
                    try:
                        chat = await message.client.get_entity(int(chat_id))
                        sms += f"\n• <b>{chat.title}</b> (<code>{chat_id}</code>)"
                    except Exception as e:
                        logger.debug("Failed to resolve chat %s: %s", chat_id, e)
                        sms += f"\n• <code>{chat_id}</code>"
            else:
                sms += self.strings("no_chats")

            if user_a["users"]:
                sms += self.strings("users_header")
                for user_id in user_a["users"]:
                    try:
                        user = await message.client.get_entity(int(user_id))
                        sms += f"\n• <b>{user.first_name}</b> (<code>{user_id}</code>)"
                    except Exception as e:
                        logger.debug("Failed to resolve user %s: %s", user_id, e)
                        sms += f"\n• <code>{user_id}</code>"
            else:
                sms += self.strings("no_users")

            await utils.answer(message, sms)

        elif args or reply:
            try:
                target_id = int(args) if args and args.isdigit() else reply.sender_id
                entity = await message.client.get_entity(target_id)

                is_channel = isinstance(entity, Channel)
                target_name = entity.title if is_channel else entity.first_name

                if is_channel:
                    if target_id in user_a["chats"]:
                        user_a["chats"].remove(target_id)
                        msg = self.strings("access_off_chat").format(target_name)
                    else:
                        user_a["chats"].append(target_id)
                        msg = self.strings("access_on_chat").format(target_name)
                else:
                    if target_id in user_a["users"]:
                        user_a["users"].remove(target_id)
                        msg = self.strings("access_off_user").format(target_name)
                    else:
                        user_a["users"].append(target_id)
                        msg = self.strings("access_on_user").format(target_name)

                self.db.set("RPMod", "useraccept", user_a)
                await utils.answer(message, msg)

            except Exception as e:
                logger.exception("Error in rpa: %s", e)
                await utils.answer(
                    message,
                    self.strings("error").format(str(e))
                )

        else:
            await utils.answer(
                message,
                self.strings("rpa_usage")
            )

    async def watcher(self, message):
        try:
            status = self.db.get("RPMod", "status", 0)
            commands = self.db.get("RPMod", "nrpcommands", {})
            users_accept = self.db.get("RPMod", "useraccept", {"users": [], "chats": []})

            if status != 1:
                return

            me_id = self._me.id

            if (message.sender_id not in users_accept["users"] and
                message.sender_id != me_id and
                message.chat_id not in users_accept["chats"]):
                return

            me = message.sender or await message.client.get_entity(message.sender_id)

            text = message.text or ""
            lines = text.splitlines()
            if not lines:
                return

            words = lines[0].split()
            if not words:
                return

            found_command = None
            remaining_text = ""
            for i in range(min(3, len(words)), 0, -1):
                possible_command = " ".join(words[:i]).casefold()
                if possible_command in commands:
                    found_command = possible_command
                    remaining_text = " ".join(words[i:]) if i < len(words) else ""
                    break

            if not found_command:
                return

            if len(words) > 1 and words[-1].startswith("@"):
                target_mention = words[-1][1:]
                try:
                    if target_mention.isdigit():
                        user = await message.client.get_entity(int(target_mention))
                    else:
                        user = await message.client.get_entity(target_mention)
                    remaining_text = " ".join(words[len(found_command.split()):-1])
                except Exception as e:
                    logger.debug("Failed to resolve mention: %s", e)
                    reply = await message.get_reply_message()
                    if reply:
                        user = await message.client.get_entity(reply.sender_id)
                    else:
                        return
            else:
                reply = await message.get_reply_message()
                if reply:
                    user = await message.client.get_entity(reply.sender_id)
                else:
                    return

            command = commands[found_command]

            replica = ""
            if len(lines) > 1:
                replica = "\n".join(lines[1:])

            action_decoration = self.config.get('action_decoration', '')
            replica_decoration = self.config.get('replica_decoration', '')
            bubble = self.config.get('speech_bubble', '💬')

            s1 = {
                'bold': ("<b>", "</b>"),
                'italic': ("<i>", "</i>"),
                'underline': ("<u>", "</u>"),
                'strikethrough': ("<s>", "</s>"),
                'spoiler': ("<spoiler>", "</spoiler>")
            }.get(action_decoration, ("", ""))

            s2 = {
                'bold': ("<b>", "</b>"),
                'italic': ("<i>", "</i>"),
                'underline': ("<u>", "</u>"),
                'strikethrough': ("<s>", "</s>"),
                'spoiler': ("<spoiler>", "</spoiler>")
            }.get(replica_decoration, ("", ""))

            rp_message = []
            if command[1]:
                rp_message.append(f"{command[1]} | ")

            rp_message.append(
                f"<a href='tg://user?id={me.id}'>{me.first_name}</a> "
                f"{s1[0]}{command[0]}{s1[1]} "
                f"<a href='tg://user?id={user.id}'>{user.first_name}</a>"
            )

            if remaining_text:
                rp_message.append(remaining_text)

            if replica:
                rp_message.append(f"\n{bubble} <b>С репликой:</b> {s2[0]}{replica}{s2[1]}")

            await utils.answer(message, "".join(rp_message))

        except Exception as e:
            logger.exception("Error in IrisRP watcher: %s", e)

    @staticmethod
    def merge_dict(d1, d2):
        d_all = {**d1, **d2}
        for key in d_all:
            left = d1.get(key, {})
            right = d_all[key]
            d_all[key] = {**left, **right}
        return d_all
