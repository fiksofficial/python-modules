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

from hikkatl.types import Message
from .. import loader, utils
import asyncio
import re


@loader.tds
class HistartMod(loader.Module):
    """
    Automatically restarts your userbot at set intervals.
    """

    strings = {
        "name": "Histart",
        "cfg_interval": "✅ Restart will occur every <b>{}</b>",
        "enabled_on": "✅ <b>Auto-restart enabled. Restarting UserBot...</b>",
        "enabled_off": "🛑 <b>Auto-restart disabled. Restarting UserBot...</b>",
        "invalid_format": "❌ <b>Invalid format.</b> Example: <code>1h30m</code>",
    }

    strings_ru = {
        "cfg_interval": "✅ <b>Рестарт будет каждые {}</b>",
        "enabled_on": "✅ <b>Авто-рестарт включён. Перезагрузка юзербота...</b>",
        "enabled_off": "🛑 <b>Авто-рестарт выключен. Перезагрузка юзербота...</b>",
        "invalid_format": "❌ <b>Неверный формат.</b> Пример: <code>1h30m</code>",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "enabled",
                False,
                lambda: "Enable auto-restart",
                validator=loader.validators.Boolean(),
            ),
            loader.ConfigValue(
                "interval",
                10800,
                lambda: "Interval between restarts in seconds (e.g. 3600 = 1h)",
                validator=loader.validators.Integer(minimum=1),
            ),
        )

    async def client_ready(self, client, db):
        self.client = client
        self.db = db

        if self.config["enabled"]:
            self._task = asyncio.create_task(self._auto_restart_loop())

    async def _auto_restart_loop(self):
        while True:
            await asyncio.sleep(self.config["interval"])
            await self.invoke("restart", "-f", peer="me")

    @loader.command(
        doc="⚙️ Set auto-restart interval. Supports formats like 1h30m, 2d3h.",
        ru_doc="⚙️ Установить интервал автоперезапуска. Поддерживает 1h30m, 2d3h и т.д.",
    )
    async def setrestart(self, message: Message):
        args = message.raw_text.split(maxsplit=1)
        if len(args) < 2:
            return await utils.answer(message, self.strings("invalid_format"))

        seconds = self._parse_interval(args[1].lower())
        if not seconds:
            return await utils.answer(message, self.strings("invalid_format"))

        self.config["interval"] = seconds
        short = self._short_format(seconds)
        await utils.answer(message, self.strings("cfg_interval").format(short))
        await self.invoke("restart", "-f", peer="me")

    @loader.command(
        doc="🔁 Toggle auto-restart on/off.",
        ru_doc="🔁 Включить или выключить авто-рестарт.",
    )
    async def histart(self, message: Message):
        self.config["enabled"] = not self.config["enabled"]
        await utils.answer(
            message,
            self.strings("enabled_on") if self.config["enabled"] else self.strings("enabled_off")
        )
        await self.invoke("restart", "-f", peer="me")

    def _parse_interval(self, text: str) -> int | None:
        multipliers = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800, "y": 31536000}
        matches = re.findall(r"(\d+)([smhdwy])", text)
        if not matches:
            return None
        return sum(int(n) * multipliers[u] for n, u in matches)

    def _short_format(self, seconds: int) -> str:
        units = [("y", 31536000), ("w", 604800), ("d", 86400), ("h", 3600), ("m", 60), ("s", 1)]
        result = []
        for key, val in units:
            count = seconds // val
            if count:
                result.append(f"{count}{key}")
                seconds %= val
        return "".join(result)

# Любопытной варваре на базаре нос оторвали! by @fiks_official