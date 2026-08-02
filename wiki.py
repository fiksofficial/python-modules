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
# requires: aiohttp
# meta fhsdesc: tool, tools, wiki, wikipedia, info, wikiinfo

import logging
from .. import loader, utils
from ..inline.types import InlineQuery
import aiohttp

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Android 10; Mobile; rv:145.0) Gecko/145.0 Firefox/145.0"
}


@loader.tds
class WikiSearchMod(loader.Module):
    """Search Wikipedia articles"""

    strings = {
        "name": "WikiSearch",
        "no_query": "❗ Please provide a search term.",
        "searching": "🔎 Searching Wikipedia for: <b>{query}</b>",
        "not_found": "🚫 No results found for: <code>{query}</code>",
        "error": "🚫 Error: <code>{error}</code>",
        "article": "<b>{title}</b>\n\n{summary}\n\n🌐 <a href='{url}'>Read more…</a>",
        "inline_title": "📚 {title}",
        "inline_description": "🔍 {summary}",
    }

    strings_ru = {
        "name": "WikiSearch",
        "_cls_doc": "Поиск статей в Википедии",
        "no_query": "❗ Укажи термин для поиска.",
        "searching": "🔎 Поиск в Википедии по запросу: <b>{query}</b>",
        "not_found": "🚫 Ничего не найдено по запросу: <code>{query}</code>",
        "error": "🚫 Ошибка: <code>{error}</code>",
        "article": "<b>{title}</b>\n\n{summary}\n\n🌐 <a href='{url}'>Читать далее…</a>",
        "inline_title": "📚 {title}",
        "inline_description": "🔍 {summary}",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "lang",
                "en",
                lambda: "Language for Wikipedia search (e.g. en, ru, fr)",
                validator=loader.validators.RegExp(r"^[a-z]{2}$"),
            )
        )
        self._session: aiohttp.ClientSession | None = None

    async def client_ready(self):
        self._session = aiohttp.ClientSession(headers=HEADERS)

    async def on_unload(self):
        if self._session and not self._session.closed:
            await self._session.close()

    @loader.command(doc="[term] - Search Wikipedia for a term", ru_doc="[термин] - Поиск статьи в Википедии по запросу")
    async def wikicmd(self, message):
        """[term] - Search Wikipedia for a term"""
        query = utils.get_args_raw(message)
        if not query:
            return await utils.answer(message, self.strings("no_query"))

        await utils.answer(message, self.strings("searching").format(query=query))

        article = await self._get_article_async(query)
        if article is None:
            return await utils.answer(message, self.strings("not_found").format(query=query))

        await utils.answer(
            message,
            self.strings("article").format(
                title=article["title"],
                summary=article["summary"],
                url=article["url"]
            )
        )

    async def _get_article_async(self, query):
        """Возвращает dict со статьёй или None при ошибке/отсутствии результата"""
        try:
            lang = self.config["lang"]
            search_url = f"https://{lang}.wikipedia.org/w/api.php"
            params = {
                "action": "query",
                "format": "json",
                "list": "search",
                "srsearch": query,
                "srlimit": 1
            }
            async with self._session.get(search_url, params=params) as res:
                data = await res.json()
                results = data.get("query", {}).get("search", [])
                if not results:
                    return None

            title = results[0]["title"]
            summary_url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{title.replace(' ', '_')}"
            async with self._session.get(summary_url) as res:
                data = await res.json()

            return {
                "title": data.get("title", title),
                "summary": data.get("extract", "No summary available"),
                "url": data.get("content_urls", {}).get("desktop", {}).get("page", f"https://{lang}.wikipedia.org/wiki/{title.replace(' ', '_')}")
            }

        except Exception:
            logger.exception("Error in Wikipedia request")
            return None

    @loader.inline_everyone
    @loader.inline_handler()
    async def wiki_inline_handler(self, query: InlineQuery):
        """[term] - Inline Wikipedia search"""
        if not query.args:
            return [{"title": "🚫 No query", "message": self.strings("no_query")}]

        article = await self._get_article_async(query.args)
        if article is None:
            return [{
                "title": "🚫 No results",
                "message": self.strings("not_found").format(query=query.args),
            }]

        return [{
            "title": self.strings("inline_title").format(title=article["title"]),
            "description": article["summary"][:100],
            "message": self.strings("article").format(
                title=article["title"],
                summary=article["summary"],
                url=article["url"]
            )
        }]
