# meta fhsdesc: tool, tools, server, admin
# requires: aiohttp

from .. import loader, utils
import aiohttp
import asyncio
import logging
from ..inline.types import InlineQuery

logger = logging.getLogger(__name__)

HEADERS = {"Accept": "application/json"}

MAX_POLL_ATTEMPTS = 15
POLL_DELAY = 2


@loader.tds
class CheckHostMod(loader.Module):
    """Check host via check-host.net"""

    strings = {
        "name": "CheckHost",
        "no_target": "❗ Please specify a host (IP or domain).",
        "checking": "🔍 Checking <code>{}</code> using <b>{}</b>...",
        "result": "📡 <b>{}</b> results for <code>{}</code>:\n\n{}",
        "error": "❌ Error: <code>{}</code>",
        "inline_select": "☑️ Choose check type for <b>{}</b>:",
        "btn_ping": "🏓 Ping",
        "btn_http": "🌐 HTTP",
        "btn_tcp": "🔌 TCP",
        "btn_dns": "🧬 DNS",
        "no_response": "❌ No response",
        "ok_response": "✅ {}",
        "unknown_format": "⚠ Unknown format",
    }

    strings_ru = {
        "name": "CheckHost",
        "_cls_doc": "Проверка хоста через check-host.net",
        "no_target": "❗ Укажи хост (IP или домен).",
        "checking": "🔍 Проверка <code>{}</code> через <b>{}</b>...",
        "result": "📡 <b>Результаты {}</b> для <code>{}</code>:\n\n{}",
        "error": "❌ Ошибка: <code>{}</code>",
        "inline_select": "☑️ Выбери тип проверки для <b>{}</b>:",
        "btn_ping": "🏓 Пинг",
        "btn_http": "🌐 HTTP",
        "btn_tcp": "🔌 TCP",
        "btn_dns": "🧬 DNS",
        "no_response": "❌ Нет ответа",
        "ok_response": "✅ {}",
        "unknown_format": "⚠ Неизвестный формат",
    }

    def __init__(self):
        self._session: aiohttp.ClientSession | None = None

    async def client_ready(self):
        self._session = aiohttp.ClientSession(headers=HEADERS)

    async def on_unload(self):
        if self._session and not self._session.closed:
            await self._session.close()

    @loader.command(doc="[host] — check host", ru_doc="[хост] — проверить хост")
    async def checkhostcmd(self, message):
        """[host] — check host / проверить хост"""
        args = utils.get_args_raw(message)
        if not args:
            return await utils.answer(message, self.strings("no_target"))

        host = args.strip()

        await self.inline.form(
            text=self.strings("inline_select").format(host),
            message=message,
            reply_markup=[
                [
                    {"text": self.strings("btn_ping"), "callback": self._callback("ping", host)},
                    {"text": self.strings("btn_http"), "callback": self._callback("http", host)}
                ],
                [
                    {"text": self.strings("btn_tcp"), "callback": self._callback("tcp", host)},
                    {"text": self.strings("btn_dns"), "callback": self._callback("dns", host)}
                ]
            ],
            force_me=True,
            silent=True
        )

    def _callback(self, check_type: str, host: str):
        async def wrapped(call):
            try:
                await call.edit(self.strings("checking").format(host, check_type.upper()))
                result = await self._run_check(check_type, host)
                await call.edit(self.strings("result").format(check_type.upper(), host, result))
            except Exception as e:
                logger.exception("Error in check-host callback")
                await call.edit(self.strings("error").format(utils.escape_html(str(e))))
        return wrapped

    async def _run_check(self, check_type, target):
        params = {"host": target, "max_nodes": 3}
        start_url = f"https://check-host.net/check-{check_type}"
        async with self._session.get(start_url, params=params) as resp:
            data = await resp.json()

        request_id = data.get("request_id")
        if not request_id:
            raise ValueError("API error: no request_id")

        # Поллинг результата вместо фиксированного sleep — ждём пока
        # все узлы ответят (или выйдем по лимиту попыток)
        result_url = f"https://check-host.net/check-result/{request_id}"
        data = None
        for _ in range(MAX_POLL_ATTEMPTS):
            await asyncio.sleep(POLL_DELAY)
            async with self._session.get(result_url) as resp:
                data = await resp.json()

            if data and all(value is not None for value in data.values()):
                break

        return self._parse_results(data)

    def _parse_results(self, data):
        if not isinstance(data, dict):
            return self.strings("error").format("Invalid API response")

        lines = []
        for node, result in data.items():
            location = node.split(".")[0]
            if result is None:
                lines.append(f"🌐 {location}: {self.strings('no_response')}")
                continue

            if isinstance(result, list) and result:
                first = result[0]
                if isinstance(first, list) and len(first) > 1:
                    lines.append(f"🌐 {location}: {self.strings('ok_response').format(first[1])}")
                else:
                    lines.append(f"🌐 {location}: {self.strings('ok_response').format(first)}")
            elif isinstance(result, str):
                lines.append(f"🌐 {location}: {self.strings('ok_response').format(result)}")
            else:
                lines.append(f"🌐 {location}: {self.strings('unknown_format')}")

        return "\n".join(lines)
