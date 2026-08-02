# На модуль распространяется лицензия "GNU General Public License v3.0"
# https://github.com/all-licenses/GNU-General-Public-License-v3.0

# -*- coding: utf-8 -*-
# Name: UserParser
# Description: Данный модуль позволяет копировать ID, Username и Name участников чата при помощи команды .userpars
# meta developer: @PyModule
# meta fhsdesc: tool, tools, id, parser, userparser

from .. import loader, utils
import json
import os
import tempfile

@loader.tds
class UserIDParserMod(loader.Module):
    """Парсер ID, имени, фамилии и юзернейма пользователей с выбором формата файла"""
    strings = {
        "name": "UserParser",
        "format_set": "<emoji document_id=5206607081334906820>✔️</emoji> <b>Формат файла успешно установлен на: {}</b>",
        "invalid_format": "<emoji document_id=5274099962655816924>❗️</emoji> <b>Неверный формат! Используйте: json, txt или html.</b>",
        "not_chat": "<emoji document_id=5210952531676504517>❌</emoji> <b>Это не чат!</b>",
        "parsing": "<emoji document_id=5274099962655816924>⏳</emoji> <b>Собираю участников чата...</b>",
        "too_many": "<emoji document_id=5210952531676504517>⚠️</emoji> <b>В чате более {} участников. Парсинг может занять много времени.</b>",
        "success": "<emoji document_id=5206607081334906820>✔️</emoji> <b>Успешно! Файл отправлен в избранное.</b>",
        "error": "<emoji document_id=5210952531676504517>❌</emoji> <b>Ошибка: {}</b>",
        "invalid_format_stored": "<emoji document_id=5274099962655816924>❗️</emoji> <b>Неверный формат файла! Укажите 'json', 'txt' или 'html' с помощью команды .formatpars.</b>",
    }
    strings_ru = {
        "_cls_doc": "Парсер ID, имени, фамилии и юзернейма пользователей с выбором формата файла",
        "format_set": "<emoji document_id=5206607081334906820>✔️</emoji> <b>Формат файла успешно установлен на: {}</b>",
        "invalid_format": "<emoji document_id=5274099962655816924>❗️</emoji> <b>Неверный формат! Используйте: json, txt или html.</b>",
        "not_chat": "<emoji document_id=5210952531676504517>❌</emoji> <b>Это не чат!</b>",
        "parsing": "<emoji document_id=5274099962655816924>⏳</emoji> <b>Собираю участников чата...</b>",
        "too_many": "<emoji document_id=5210952531676504517>⚠️</emoji> <b>В чате более {} участников. Парсинг может занять много времени.</b>",
        "success": "<emoji document_id=5206607081334906820>✔️</emoji> <b>Успешно! Файл отправлен в избранное.</b>",
        "error": "<emoji document_id=5210952531676504517>❌</emoji> <b>Ошибка: {}</b>",
        "invalid_format_stored": "<emoji document_id=5274099962655816924>❗️</emoji> <b>Неверный формат файла! Укажите 'json', 'txt' или 'html' с помощью команды .formatpars.</b>",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "file_format",
                "json",
                lambda: "Формат файла по умолчанию: json, txt или html",
                validator=loader.validators.Choice(["json", "txt", "html"])
            ),
            loader.ConfigValue(
                "max_members",
                5000,
                lambda: "Максимальное количество участников для парсинга",
                validator=loader.validators.Integer(minimum=100, maximum=100000)
            )
        )

    async def client_ready(self, client, db):
        self.client = client
        self.db = db

    @loader.command(ru_doc="(.formatpars) <json|txt|html> - Устанавливает формат файла")
    async def formatparscmd(self, message):
        """Устанавливает формат файла: json, txt или html"""
        args = utils.get_args_raw(message)
        if args and args.lower() in ["json", "txt", "html"]:
            self.set("file_format", args.lower())
            await utils.answer(message, self.strings["format_set"].format(args.lower()))
        else:
            await utils.answer(message, self.strings["invalid_format"])

    @loader.command(ru_doc="(.userpars) - Собирает информацию о пользователях из чата и сохраняет в файл")
    async def userparscmd(self, message):
        """Собирает информацию о пользователях из чата и сохраняет в файл"""
        chat = message.chat
        if not chat:
            await utils.answer(message, self.strings["not_chat"])
            return

        total = await self.client.get_participants_count(chat.id)
        if total > self.config["max_members"]:
            await utils.answer(message, self.strings["too_many"].format(total))
            return

        status = await utils.answer(message, self.strings["parsing"])
        user_data = []
        async for user in self.client.iter_participants(chat.id, limit=self.config["max_members"]):
            user_info = {
                "id": user.id,
                "username": user.username or "None",
                "first_name": user.first_name or "None",
                "last_name": user.last_name or "None"
            }
            user_data.append(user_info)
            if len(user_data) % 500 == 0:
                await status.edit(
                    self.strings["parsing"].replace("...", f"... ({len(user_data)}/{total})")
                )

        chat_title = chat.title or "Без названия"
        chat_id = chat.id
        chat_info = f"Чат: {chat_title}\nID чата: {chat_id}"
        file_format = self.get("file_format")
        base_name = f"user_data_{chat_id}_{message.id}"
        if file_format == "json":
            file_path = os.path.join(tempfile.gettempdir(), f"{base_name}.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(user_data, f, indent=4, ensure_ascii=False)
            caption = f"Список пользователей из чата (JSON):\n{chat_info}"
        elif file_format == "txt":
            file_path = os.path.join(tempfile.gettempdir(), f"{base_name}.txt")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"{chat_info}\n\n")
                for user in user_data:
                    f.write(
                        f"ID: {user['id']}, "
                        f"Username: {user['username']}, "
                        f"Имя: {user['first_name']}, "
                        f"Фамилия: {user['last_name']}\n"
                    )
            caption = f"Список пользователей из чата (TXT):\n{chat_info}"
        elif file_format == "html":
            file_path = os.path.join(tempfile.gettempdir(), f"{base_name}.html")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Список пользователей</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f9f9f9;
        }}
        h1 {{
            text-align: center;
            color: #333;
        }}
        p {{
            font-size: 16px;
            color: #555;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            font-size: 16px;
            background-color: #fff;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: center;
        }}
        th {{
            background-color: #4CAF50;
            color: white;
            font-weight: bold;
        }}
        tr:nth-child(even) {{
            background-color: #f2f2f2;
        }}
        tr:hover {{
            background-color: #ddd;
        }}
        .bold {{
            font-weight: bold;
        }}
        .italic {{
            font-style: italic;
        }}
        .underline {{
            text-decoration: underline;
        }}
        .highlight {{
            background-color: yellow;
        }}
    </style>
</head>
<body>
    <h1 class="bold">Список пользователей из чата</h1>
    <p><strong>Чат:</strong> <span class="italic">{chat_title}</span></p>
    <p><strong>ID чата:</strong> <span class="underline">{chat_id}</span></p>
    <table>
        <tr>
            <th>ID</th>
            <th>Username</th>
            <th>Имя</th>
            <th>Фамилия</th>
        </tr>
""")
                for user in user_data:
                    f.write(f"""
        <tr>
            <td class="bold">{user['id']}</td>
            <td class="italic">{user['username']}</td>
            <td class="underline">{user['first_name']}</td>
            <td class="highlight">{user['last_name']}</td>
        </tr>
""")
                f.write("""
    </table>
</body>
</html>
""")
            caption = f"Список пользователей из чата (HTML):\n{chat_info}"
        else:
            await utils.answer(message, self.strings["invalid_format_stored"])
            return

        try:
            await self.client.send_file("me", file_path, caption=caption)
        finally:
            os.remove(file_path)
        await utils.answer(status, self.strings["success"])
