# На модуль распространяется лицензия "GNU General Public License v3.0"
# https://github.com/all-licenses/GNU-General-Public-License-v3.0

# meta developer: @PyModule
# meta fhsdesc: tool, tools, user, id

import logging
from .. import loader, utils

logger = logging.getLogger(__name__)

@loader.tds
class GetUserMod(loader.Module):
    """Получает username пользователя по его ID"""

    strings = {
        "name": "GetUser",
        "no_id": "❌ <b>Укажите ID пользователя!</b>",
        "user_not_exists": "<blockquote>👁 <b>Пользователь не существует.</b></blockquote>\n\n🔎 <b>ID: {user_id}</b>",
        "found_header": "<blockquote>👁 <b>Username найден.</b></blockquote>",
        "no_username_header": "<blockquote>👁 <b>Username не найден.</b></blockquote>",
        "error": "<blockquote>👁 <b>Ошибка при поиске пользователя.</b></blockquote>\n\n🔎 <b>ID: {user_id}</b>",
    }

    strings_ru = {
        "_cls_doc": "Получает username пользователя по его ID",
        "no_id": "❌ <b>Укажите ID пользователя!</b>",
        "user_not_exists": "<blockquote>👁 <b>Пользователь не существует.</b></blockquote>\n\n🔎 <b>ID: {user_id}</b>",
        "found_header": "<blockquote>👁 <b>Username найден.</b></blockquote>",
        "no_username_header": "<blockquote>👁 <b>Username не найден.</b></blockquote>",
        "error": "<blockquote>👁 <b>Ошибка при поиске пользователя.</b></blockquote>\n\n🔎 <b>ID: {user_id}</b>",
    }

    @loader.command()
    async def getusercmd(self, message):
        """[ID] - Найти username по ID."""
        args = utils.get_args_raw(message)
        if not args or not args.isdigit():
            return await utils.answer(message, self.strings("no_id"))

        user_id = int(args)

        try:
            user = await self.client.get_entity(user_id)
            if user.deleted or not user.first_name:
                return await utils.answer(
                    message,
                    self.strings("user_not_exists").format(user_id=user_id),
                )

            parts = [
                self.strings("found_header") if user.username else self.strings("no_username_header"),
                f"🔎 <b>ID: {user_id}</b>",
            ]
            if user.username:
                parts.append(f"👤 <b>Username: @{utils.escape_html(user.username)}</b>")
            parts.append(f"👤 <b>First name: {utils.escape_html(user.first_name)}</b>")
            if user.last_name:
                parts.append(f"👤 <b>Last name: {utils.escape_html(user.last_name)}</b>")

            await utils.answer(message, "\n\n".join(parts))
        except Exception:
            logger.exception("Error in getuser command")
            await utils.answer(message, self.strings("error").format(user_id=user_id))
