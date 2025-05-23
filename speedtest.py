# На модуль распространяется лицензия "GNU General Public License v3.0"
# https://github.com/all-licenses/GNU-General-Public-License-v3.0

# meta developer: @pymodule
# requires: pyspeedtest

import pyspeedtest
from .. import loader

class SpeedTestMod(loader.Module):
    """Модуль для проверки скорости интернета через pyspeedtest"""

    strings = {"name": "SpeedTest"}

    async def speedcmd(self, message):
        """Запускает тест скорости интернета"""
        msg = await message.edit("Запускаем Speedtest... 🏎️")

        try:
            st = pyspeedtest.SpeedTest()
            ping = st.ping()
            download_speed = st.download() / 1_000_000
            upload_speed = st.upload() / 1_000_000

        await msg.edit(
            f"<emoji document_id=5325547803936572038>✨</emoji> <b>Speedtest завершён!</b> <emoji document_id=5325547803936572038>✨</emoji>\n\n"
            f"<b>Ping:</b> <i>{ping:.2f} ms</i>\n"
            f"<emoji document_id=6041730074376410123>📥</emoji> <b>Загрузка:</b> <i>{download_speed:.2f} Mbps</i>\n"
            f"<emoji document_id=6041730074376410123>📤</emoji> <b>Отдача:</b> <i>{upload_speed:.2f} Mbps</i>",
            parse_mode="HTML"
        )
