# На модуль распространяется лицензия "GNU General Public License v3.0"
# https://github.com/all-licenses/GNU-General-Public-License-v3.0

# meta developer: @PyModule
# meta fhsdesc: tool, tools, lyrics, music
# requires: requests beautifulsoup4

import asyncio
import logging
import requests
from bs4 import BeautifulSoup, Tag, NavigableString
import re
from .. import loader, utils

logger = logging.getLogger(__name__)


@loader.tds
class LyricsMod(loader.Module):
    """Модуль для поиска текста песни через Genius API напрямую"""

    strings = {
        "name": "Lyrics",
        "no_token": "<emoji document_id=5774077015388852135>❌</emoji> <b>Токен Genius API не установлен. Используйте <code>.cfg Lyrics</code>.</b>",
        "usage": "<emoji document_id=5253959125838090076>👁</emoji> <b>Использование:</b> .lyrics [название песни]",
        "searching": "<emoji document_id=5253959125838090076>👁</emoji> <b>Ищу текст песни:</b> {query}...",
        "api_error": "<b>Ошибка API Genius:</b> {status}",
        "not_found": "<emoji document_id=5774077015388852135>❌</emoji> <b>Песня не найдена.</b>",
        "lyrics_not_found": "<b><emoji document_id=5774077015388852135>❌</emoji> Текст песни не найден.</b>",
        "truncated": "<b>Текст обрезан из-за ограничения Telegram.</b>",
        "error": "<b>Ошибка:</b> {error}",
        "_cfg_doc_token": "Токен для доступа к Genius API. Получите его на https://genius.com/api-clients",
    }

    strings_ru = {
        "_cls_doc": "Поиск текста песни через Genius API",
        "no_token": "<emoji document_id=5774077015388852135>❌</emoji> <b>Токен Genius API не установлен. Используйте <code>.cfg Lyrics</code>.</b>",
        "usage": "<emoji document_id=5253959125838090076>👁</emoji> <b>Использование:</b> .lyrics [название песни]",
        "searching": "<emoji document_id=5253959125838090076>👁</emoji> <b>Ищу текст песни:</b> {query}...",
        "api_error": "<b>Ошибка API Genius:</b> {status}",
        "not_found": "<emoji document_id=5774077015388852135>❌</emoji> <b>Песня не найдена.</b>",
        "lyrics_not_found": "<b><emoji document_id=5774077015388852135>❌</emoji> Текст песни не найден.</b>",
        "truncated": "<b>Текст обрезан из-за ограничения Telegram.</b>",
        "error": "<b>Ошибка:</b> {error}",
        "_cfg_doc_token": "Токен для доступа к Genius API. Получите его на https://genius.com/api-clients",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "GENIUS_TOKEN",
                None,
                doc=lambda: self.strings["_cfg_doc_token"],
                validator=loader.validators.Hidden(loader.validators.String()),
            )
        )

    def _lyrics(self, html: str) -> str | None:
        soup = BeautifulSoup(html, "html.parser")
        for remove in soup.find_all("div", class_=re.compile("LyricsHeader__Container")):
            remove.decompose()
        containers = soup.find_all("div", attrs={"data-lyrics-container": "true"})
        if not containers:
            return None
        lyrics = ""
        for container in containers:
            for elem in container.contents:
                if isinstance(elem, Tag):
                    if elem.name == "br":
                        lyrics += "\n"
                    else:
                        lyrics += elem.get_text(separator="\n")
                elif isinstance(elem, NavigableString):
                    lyrics += str(elem)
        lyrics = re.sub(r"\n{3,}", "\n\n", lyrics)
        return lyrics.strip()

    @loader.command()
    async def lyricscmd(self, message):
        """[запрос] - Найти текст песни по запросу"""
        token = self.config["GENIUS_TOKEN"]
        if not token:
            return await utils.answer(message, self.strings("no_token"))

        query = utils.get_args_raw(message)
        if not query:
            return await utils.answer(message, self.strings("usage"))

        await utils.answer(message, self.strings("searching").format(query=query))

        try:
            def _fetch():
                headers = {"Authorization": f"Bearer {token}"}
                response = requests.get(
                    f"https://api.genius.com/search?q={requests.utils.quote(query)}",
                    headers=headers,
                    timeout=10,
                )
                if response.status_code != 200:
                    return response.status_code, None, None, None, None
                data = response.json()
                hits = data.get("response", {}).get("hits", [])
                if not hits:
                    return None, None, None, None, None
                song_info = hits[0]["result"]
                song_url = song_info["url"]
                song_title = song_info["title"]
                artist_name = song_info["primary_artist"]["name"]
                html = requests.get(song_url, timeout=10).text
                return None, song_title, artist_name, html, song_url

            status, song_title, artist_name, html, _ = await asyncio.to_thread(_fetch)
            if status is not None:
                return await utils.answer(message, self.strings("api_error").format(status=status))
            if song_title is None:
                return await utils.answer(message, self.strings("not_found"))

            lyrics = await asyncio.to_thread(self._lyrics, html)

            if lyrics and len(lyrics) > 4096:
                lyrics = lyrics[:4000] + "\n\n" + self.strings("truncated")

            text = f"<b><emoji document_id=5938473438468378529>🎶</emoji> {utils.escape_html(song_title)} — {utils.escape_html(artist_name)}</b>\n\n"
            if lyrics:
                text += f"<blockquote expandable><b>{lyrics}</b></blockquote>"
            else:
                text += self.strings("lyrics_not_found")

            await utils.answer(message, text)

        except Exception as e:
            logger.exception("Error in lyrics command")
            await utils.answer(message, self.strings("error").format(error=utils.escape_html(str(e))))
