# meta developer: @pymodule

import subprocess
import re
from .. import loader, utils

class SpeedTestMod(loader.Module):
    """Модуль для проверки скорости интернета через Speedtest"""
    
    strings = {"name": "SpeedTest"}

    async def speedcmd(self, message):
        """Запускает тест скорости интернета"""
        
        msg = await message.edit("Запускаем Speedtest... 🏎️")
        
        try:
            result = subprocess.run(["speedtest"], capture_output=True, text=True)
            output = result.stdout
        except Exception as e:
            return await msg.edit(f"<emoji document_id=5420323339723881652>⚠️</emoji> <b>Ошибка:</b> `{e}`", parse_mode="HTML")
        
        download_match = re.search(r"Download:\s+([\d.]+)\s+Mbps", output)
        upload_match = re.search(r"Upload:\s+([\d.]+)\s+Mbps", output)
        
        if not download_match or not upload_match:
            return await msg.edit("<emoji document_id=5210952531676504517>❌</emoji> <b>Не удалось извлечь данные о скорости. Проверьте, установлен ли пакет speedtest(Подробнее: https://www.speedtest.net/ru/apps/cli)</b>", parse_mode="HTML")
        
        download_speed = download_match.group(1)
        upload_speed = upload_match.group(1)
        
        await msg.edit(f"<emoji document_id=5325547803936572038>✨</emoji> <b>Speedtest завершён!</b> <emoji document_id=5325547803936572038>✨</emoji>\n\n"
                       f"<emoji document_id=6041730074376410123>📥</emoji> <b>Загрузка:</b> <i>{download_speed} Mbps</i>\n"
                       f"<emoji document_id=6041730074376410123>📤</emoji> <b>Отдача:</b> <i>{upload_speed} Mbps</i>", parse_mode="HTML")
