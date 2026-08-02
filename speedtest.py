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
# meta fhsdesc: tool, tools, test, speedtest
# requires: speedtest-cli

import asyncio
import speedtest
from .. import loader, utils

@loader.tds
class SpeedTestMod(loader.Module):
    """Checking your internet speed"""
    strings = {
        "name": "SpeedTest",
        "starting": "Running Speedtest…",
        "ping": "Ping: <i>{:.2f} ms</i>",
        "download": "Download: <i>{:.2f} Mbps</i>",
        "upload": "Upload: <i>{:.2f} Mbps</i>",
        "finished": "<b>Speedtest completed!</b>",
        "error": "Speedtest error: <code>{}</code>",
        "progress_ping": "Testing \"Ping\"...",
        "progress_download": "Testing \"Download\"...",
        "progress_upload": "Testing \"Upload\"...",
        "cfg_timeout": "Server request timeout (sec)",
        "cfg_retries": "Number of retry attempts",
        "quality_website": "Websites: {}",
        "quality_video": "Video: {}",
        "quality_gaming": "Gaming: {}",
        "quality_calls": "Video calls: {}",
    }

    strings_ru = {
        "_cls_doc": "Проверка скорости интернета",
        "starting": "Запускаем Speedtest…",
        "ping": "Ping: <i>{:.2f} мс</i>",
        "download": "Загрузка: <i>{:.2f} Мбит/с</i>",
        "upload": "Отдача: <i>{:.2f} Мбит/с</i>",
        "finished": "<b>Speedtest завершён!</b>",
        "error": "Ошибка при выполнении Speedtest: <code>{}</code>",
        "progress_ping": "Тестируем пинг...",
        "progress_download": "Тестируем скачивание...",
        "progress_upload": "Тестируем загрузку...",
        "cfg_timeout": "Таймаут запросов к серверу (сек)",
        "cfg_retries": "Кол‑во попыток при неудаче",
        "quality_website": "Сайты: {}",
        "quality_video": "Видео: {}",
        "quality_gaming": "Игры: {}",
        "quality_calls": "Видеосвязь: {}",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "timeout",
                30,
                lambda: self.strings("cfg_timeout"),
                validator=loader.validators.Integer(minimum=10, maximum=120),
            ),
            loader.ConfigValue(
                "retries",
                2,
                lambda: self.strings("cfg_retries"),
                validator=loader.validators.Integer(minimum=0, maximum=5),
            ),
        )

    def _get_quality_rating(self, category: str, ping: float, download: float, upload: float) -> str:
        if category == "website":
            if ping < 50 and download > 5:
                return "🟢🟢🟢🟢🟢"
            elif ping < 100 and download > 3:
                return "🟠🟠🟠🟠"
            elif ping < 200 and download > 1:
                return "🟡🟡🟡"
            elif ping < 300 and download > 0.5:
                return "🔴🔴"
            else:
                return "⚫"
        elif category == "video":
            if ping < 50 and download > 25:
                return "🟢🟢🟢🟢🟢"
            elif ping < 75 and download > 5:
                return "🟠🟠🟠🟠"
            elif ping < 100 and download > 3:
                return "🟡🟡🟡"
            elif ping < 150 and download > 1:
                return "🔴🔴"
            else:
                return "⚫"
        elif category == "gaming":
            if ping < 50 and download > 5 and upload > 3:
                return "🟢🟢🟢🟢🟢"
            elif ping < 100 and download > 3 and upload > 1:
                return "🟠🟠🟠🟠"
            elif ping < 150 and download > 1 and upload > 0.5:
                return "🟡🟡🟡"
            elif ping < 200 and download > 0.5:
                return "🔴🔴"
            else:
                return "⚫"
        elif category == "calls":
            if ping < 50 and download > 4 and upload > 4:
                return "🟢🟢🟢🟢🟢"
            elif ping < 100 and download > 1.5 and upload > 1.5:
                return "🟡🟡🟡🟡"
            elif ping < 150 and download > 1 and upload > 1:
                return "🟠🟠🟠"
            elif ping < 200 and download > 0.5:
                return "🔴🔴"
            else:
                return "⚫"
        return "⚫"

    @loader.command(
        ru_doc="(.st) - Запускает тест скорости интернета",
        en_doc="(.st) - Runs an internet speed test",
        alias="st",
    )
    async def speedcmd(self, message):
        msg = await utils.answer(message, self.strings("starting"))

        try:
            s = await asyncio.to_thread(speedtest.Speedtest)
            await asyncio.to_thread(s.get_best_server)
            await utils.answer(msg, self.strings("progress_ping"))

            ping = s.results.ping

            await utils.answer(msg, self.strings("progress_download"))
            download = (await asyncio.to_thread(s.download)) / 1_000_000

            await utils.answer(msg, self.strings("progress_upload"))
            upload = (await asyncio.to_thread(s.upload)) / 1_000_000

            text = (
                f"{self.strings('finished')}\n\n"
                f"{self.strings('ping').format(ping)}\n"
                f"{self.strings('download').format(download)}\n"
                f"{self.strings('upload').format(upload)}\n\n"
                f"{self.strings('quality_website').format(self._get_quality_rating('website', ping, download, upload))}\n"
                f"{self.strings('quality_video').format(self._get_quality_rating('video', ping, download, upload))}\n"
                f"{self.strings('quality_gaming').format(self._get_quality_rating('gaming', ping, download, upload))}\n"
                f"{self.strings('quality_calls').format(self._get_quality_rating('calls', ping, download, upload))}"
            )

            await utils.answer(msg, text)
        except Exception as exc:
            await utils.answer(
                msg,
                self.strings("error").format(utils.escape_html(str(exc))),
            )
