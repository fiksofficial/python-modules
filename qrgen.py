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
# meta fhsdesc: tool, tools, qr
# requires: requests

from .. import loader, utils
import requests
import uuid
import os
import asyncio
import tempfile

@loader.tds
class QRGenMod(loader.Module):
    """Generate QR codes from text or links"""

    strings = {
        "name": "QRGen",
        "generating": "📡 Generating QR for:\n<code>{text}</code>",
        "no_text": "❗ Please provide text or a link to encode",
        "api_error": "🚫 Error while contacting QR API",
        "not_image": "⚠️ API did not return an image",
        "ok": "✅ QR code successfully generated",
        "error_with_details": "🚫 Error:\n<code>{error}</code>",
        "_cfg_doc_timeout": "Request timeout in seconds",
        "_cfg_doc_size": "QR code size (e.g. 512x512)",
        "_cfg_doc_margin": "QR code margin in px",
    }

    strings_ru = {
        "name": "QRGen",
        "_cls_doc": "Генерация QR-кодов из текста или ссылок",
        "generating": "📡 Генерация QR для:\n<code>{text}</code>",
        "no_text": "❗ Укажи текст или ссылку для кодирования",
        "api_error": "🚫 Ошибка при запросе к QR API",
        "not_image": "⚠️ API не вернул изображение",
        "ok": "✅ QR-код успешно сгенерирован",
        "error_with_details": "🚫 Ошибка:\n<code>{error}</code>",
        "_cfg_doc_timeout": "Таймаут запроса в секундах",
        "_cfg_doc_size": "Размер QR-кода (например 512x512)",
        "_cfg_doc_margin": "Поля QR-кода в px",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "timeout",
                15,
                doc=lambda: self.strings["_cfg_doc_timeout"],
                validator=loader.validators.Integer(minimum=5, maximum=120),
            ),
            loader.ConfigValue(
                "size",
                "512x512",
                doc=lambda: self.strings["_cfg_doc_size"],
                validator=loader.validators.RegExp(r"^\d+x\d+$"),
            ),
            loader.ConfigValue(
                "margin",
                10,
                doc=lambda: self.strings["_cfg_doc_margin"],
                validator=loader.validators.Integer(minimum=0, maximum=50),
            ),
        )

    @loader.command(doc="Generate a QR code from text or link", ru_doc="Сгенерировать QR-код из текста или ссылки")
    async def qrcmd(self, message):
        """<text or URL> — generate QR code"""
        text = utils.get_args_raw(message)
        if not text:
            return await utils.answer(message, self.strings("no_text"))

        await utils.answer(message, self.strings("generating").format(text=text))

        temp_file = None
        try:
            params = {
                "data": text,
                "size": self.config["size"],
                "ecc": "M",
                "format": "png",
                "margin": self.config["margin"],
            }

            def _download() -> tuple[str | None, str | None]:
                # Скачиваем QR-код в tempfile; on error возвращаем (None, key)
                with requests.get(
                    "https://api.qrserver.com/v1/create-qr-code/",
                    params=params,
                    stream=True,
                    timeout=self.config["timeout"],
                ) as response:
                    if response.status_code != 200:
                        return None, "api_error"
                    if not response.headers.get("Content-Type", "").startswith("image/"):
                        return None, "not_image"

                    path = os.path.join(tempfile.gettempdir(), f"qr_{uuid.uuid4().hex}.png")
                    with open(path, "wb") as f:
                        for chunk in response.iter_content(8192):
                            f.write(chunk)
                    return path, None

            temp_file, error_key = await asyncio.to_thread(_download)
            if error_key:
                return await utils.answer(message, self.strings(error_key))

            await message.client.send_file(
                message.chat_id,
                temp_file,
                caption=self.strings("ok"),
                reply_to=message.id,
            )

            try:
                await message.delete()
            except Exception:
                pass

        except Exception as e:
            await utils.answer(
                message,
                self.strings("error_with_details").format(error=utils.escape_html(str(e))),
            )
        finally:
            # Гарантированно чистим temp-файл даже при ошибке send_file
            if temp_file and os.path.isfile(temp_file):
                try:
                    os.remove(temp_file)
                except OSError:
                    pass
