#         ______     ___  ___          _       _      
#    ____ | ___ \    |  \/  |         | |     | |     
#   / __ \| |_/ /   _| .  . | ___   __| |_   _| | ___ 
#  / / _` |  __/ | | | |\/| |/ _ \ / _` | | | | |/ _ \
# | | (_| |  | |_| | |  | | (_) | (_| | |_| | |  __/
#  \ \__,_\_|   \__, \_|  |_/\___/ \__,_|\__,_|_|\___|
#   \____/       __/ |                                
#               |___/                                  

# На модуль распространяется лицензия "GNU General Public License v3.0"
# https://github.com/all-licenses/GNU-General-Public-License-v3.0

# meta developer: @pymodule

import logging
import platform
import socket
import os
import time
import aiohttp
import psutil
from datetime import datetime, timezone, timedelta
from typing import Optional, Any
from collections import OrderedDict

from .. import loader, utils, validators
from herokutl.tl.functions.users import GetFullUserRequest
from herokutl.tl.functions.payments import GetStarsStatusRequest
from herokutl.tl.functions.help import GetNearestDcRequest

logger = logging.getLogger(__name__)

# Курс Telegram Stars к USD (фиксированный, источник: xvestor.ru/converter/tgstars/usd)
STAR_USD = 0.022


class LRUCache:
    """LRU-кэш с TTL"""
    def __init__(self, max_size: int = 100, ttl: int = 300):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.ttl = ttl
        self.timestamps = {}

    def get(self, key: str) -> Optional[Any]:
        if key not in self.cache:
            return None

        if time.time() - self.timestamps[key] > self.ttl:
            del self.cache[key]
            del self.timestamps[key]
            return None

        self.cache.move_to_end(key)
        return self.cache[key]

    def set(self, key: str, value: Any):
        if len(self.cache) >= self.max_size:
            oldest = next(iter(self.cache))
            del self.cache[oldest]
            del self.timestamps[oldest]

        self.cache[key] = value
        self.timestamps[key] = time.time()


@loader.tds
class PlaceholdersMod(loader.Module):
    """Плейсхолдеры+: профиль, время, погода, курсы валют, крипта, система, музыка, факты и цитаты — для био, имени и статуса"""

    strings = {
        "name": "Placeholders+",
        "phtest_usage": "<b>Использование:</b> <code>.phtest Привет, {name}! Курс: {dollars_in_rub}</code>",
        "phtest_unknown": "🚫 Неизвестный плейсхолдер: <code>{}</code>",
        "phtest_error": "🚫 Ошибка в шаблоне: <code>{}</code>",
        "phlist_empty": "Плейсхолдеры не найдены",
    }

    strings_en = {
        "name": "Placeholders+",
        "phtest_usage": "<b>Usage:</b> <code>.phtest Hello, {name}! Rate: {dollars_in_rub}</code>",
        "phtest_unknown": "🚫 Unknown placeholder: <code>{}</code>",
        "phtest_error": "🚫 Template error: <code>{}</code>",
        "phlist_empty": "No placeholders found",
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "timezone",
                5,
                "Часовой пояс (offset от UTC)",
                validator=validators.Integer(),
            ),
            loader.ConfigValue(
                "weather_city",
                "Oral",
                "Город для погоды",
                validator=validators.String(),
            ),
            loader.ConfigValue(
                "lastfm_user",
                "",
                "Last.FM username",
                validator=validators.String(),
            ),
            loader.ConfigValue(
                "lastfm_api_key",
                "460cda35be2fbf4f28e8ea7a38580730",
                "Last.FM API key",
                validator=validators.String(),
            ),
            loader.ConfigValue(
                "crypto_address",
                "YOUR_WALLET_ADDRESS",
                "Крипто-кошелёк",
                validator=validators.String(),
            ),
            loader.ConfigValue(
                "card_number",
                "**** **** **** ****",
                "Номер карты",
                validator=validators.String(),
            ),
            loader.ConfigValue(
                "donate_site",
                "Boosty:https://boosty.to/yourname",
                "Донат: имя:ссылка",
                validator=validators.String(),
            ),
            loader.ConfigValue(
                "channel",
                "@yourchannel",
                "Канал",
                validator=validators.String(),
            ),
            loader.ConfigValue(
                "social_network",
                "https://vk.com/your",
                "Соцсеть",
                validator=validators.String(),
            ),
            loader.ConfigValue(
                "github_username",
                "",
                "GitHub username (для плейсхолдеров статистики)",
                validator=validators.String(),
            ),
            loader.ConfigValue(
                "time_format",
                "%H:%M:%S",
                "Формат времени (strftime)",
                validator=validators.String(),
            ),
            loader.ConfigValue(
                "date_format",
                "%d.%m.%Y",
                "Формат даты (strftime)",
                validator=validators.String(),
            ),
            loader.ConfigValue(
                "wind_unit",
                "км/ч",
                "Единица скорости ветра",
                validator=validators.Choice(["км/ч", "м/с"]),
            ),
            loader.ConfigValue(
                "pressure_unit",
                "мм рт. ст.",
                "Единица давления",
                validator=validators.Choice(["мм рт. ст.", "гПа"]),
            ),
        )
        self.cache = LRUCache(max_size=150, ttl=300)

    async def client_ready(self, client, db):
        self._client = client
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=15)
        )

        self.me = await client.get_me()
        self.full_me = await client(GetFullUserRequest(self.me))

        self._started_at = time.time()
        self.tz = timezone(timedelta(hours=self.config["timezone"]))
        self.weekdays_ru = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]

        try:
            psutil.cpu_percent(interval=None)
        except Exception:
            pass

        self._register_placeholders()

    def _register_placeholders(self):
        placeholders = [
            ("username", self.get_username, "Username"),
            ("name", self.get_name, "Имя"),
            ("surname", self.get_surname, "Фамилия"),
            ("bio_description", self.get_bio, "Описание"),
            ("user_id", self.get_user_id, "ID"),
            ("phone_number", self.get_phone, "Телефон"),
            ("dc_id", self.get_dc_id, "DC ID"),
            ("amount_stars", self.get_stars, "Баланс Stars"),
            ("premium_check", self.get_premium_check, "Дата окончания Premium"),

            ("dollars_in_rub", self.get_usd_to_rub, "USD → RUB"),
            ("rub_in_dollars", self.get_rub_to_usd, "RUB → USD"),
            ("euros_in_rub", self.get_eur_to_rub, "EUR → RUB"),
            ("rub_in_euros", self.get_rub_to_eur, "RUB → EUR"),
            ("yuan_in_rub", self.get_cny_to_rub, "CNY → RUB"),
            ("tenge_in_rub", self.get_kzt_to_rub, "KZT → RUB"),
            ("rub_in_tenge", self.get_rub_to_kzt, "RUB → KZT"),
            ("usdt_in_rub", self.get_usdt_to_rub, "USDT → RUB"),
            ("rub_in_usdt", self.get_rub_to_usdt, "RUB → USDT"),
            ("ton_in_rub", self.get_ton_to_rub, "TON → RUB"),
            ("rub_in_ton", self.get_rub_to_ton, "RUB → TON"),
            ("btc_in_rub", self.get_btc_to_rub, "BTC → RUB"),
            ("eth_in_rub", self.get_eth_to_rub, "ETH → RUB"),
            ("stars_in_rub", self.get_stars_to_rub, "Star → RUB"),
            ("stars_in_ton", self.get_stars_to_ton, "Star → TON"),
            ("stars_in_usdt", self.get_stars_to_usdt, "Star → USDT"),

            ("os_uptime", self.get_os_uptime, "Аптайм системы"),
            ("bot_uptime", self.get_bot_uptime, "Аптайм юзербота"),
            ("internet_usage", self.get_internet_usage, "Статистика трафика"),
            ("speedtest", self.get_speedtest, "Скорость интернета"),
            ("host", self.get_host, "Hostname ОС"),
            ("shell", self.get_shell, "Оболочка"),
            ("gpu", self.get_gpu, "GPU"),
            ("disk", self.get_disk, "Использование диска"),
            ("local_ip", self.get_local_ip, "Локальный IP"),
            ("public_ip", self.get_public_ip, "Внешний IP"),
            ("ip_info", self.get_ip_info, "Геолокация по IP"),
            ("user_and_hostname", self.get_user_hostname, "user@hostname"),
            ("battery", self.get_battery, "Заряд батареи"),
            ("cpu_usage", self.get_cpu_usage, "Загрузка CPU"),
            ("ram_usage", self.get_ram_usage, "Использование RAM"),
            ("ping", self.get_ping, "Пинг до Telegram"),

            ("time", self.get_time, "Время"),
            ("date", self.get_date, "Дата"),
            ("day_of_the_week", self.get_weekday, "День недели"),
            ("data_and_time", self.get_date_time, "Дата и время"),
            ("data_and_time_and_day_of_the_week", self.get_full_date_time_weekday, "Дата, время, день недели"),
            ("moon_phase", self.get_moon_phase, "Фаза Луны"),
            ("zodiac_sign", self.get_zodiac_sign, "Знак зодиака"),
            ("weather", self.get_weather_condition, "Погода"),
            ("outdoor_temperature", self.get_temperature, "Температура"),
            ("weather_and_temperature", self.get_weather_temp, "Погода и температура"),
            ("weather_emoji", self.get_weather_emoji, "Эмодзи погоды"),
            ("feels_like", self.get_feels_like, "Ощущается как"),
            ("humidity", self.get_humidity, "Влажность"),
            ("pressure", self.get_pressure, "Давление"),
            ("wind_speed", self.get_wind_speed, "Скорость ветра"),

            ("my_crypto_address", self.get_crypto_address, "Крипто-адрес"),
            ("my_card_number", self.get_card_number, "Номер карты"),
            ("my_donate_site", self.get_donate_site, "Донат"),
            ("my_channel", self.get_channel, "Канал"),
            ("my_social_network", self.get_social, "Соцсеть"),

            ("now_playing", self.get_now_playing, "Сейчас играет"),
            ("last_fm_user_and_now_playing", self.get_user_and_playing, "Last.FM + трек"),
            ("song_name", self.get_song_name, "Название трека"),
            ("song_artist", self.get_song_artist, "Артист"),
            ("last_fm_user", self.get_lastfm_user, "Last.FM username"),
            ("lastfm_stats", self.get_lastfm_stats, "Last.FM статистика"),

            ("github_repos", self.get_github_repos, "Публичные репозитории GitHub"),
            ("github_followers", self.get_github_followers, "Подписчики GitHub"),

            ("random_fact", self.get_random_fact, "Случайный факт"),
            ("quote", self.get_quote, "Случайная цитата"),
            ("joke", self.get_joke, "Случайная шутка"),
            ("advice", self.get_advice, "Случайный совет"),
            ("cat_fact", self.get_cat_fact, "Факт о котах"),
            ("kanye_quote", self.get_kanye_quote, "Цитата Канье Уэста"),
            ("affirmation", self.get_affirmation, "Аффирмация"),
        ]

        for name, func, desc in placeholders:
            utils.register_placeholder(name, func, desc)


    @loader.command()
    async def phtestcmd(self, message):
        """- Отрендерить текст с плейсхолдерами (.phtest Привет, {name}!)"""
        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, self.strings["phtest_usage"])
            return

        data = await utils.get_placeholders({}, args)
        try:
            out = args.format(**data)
        except KeyError as e:
            out = self.strings["phtest_unknown"].format(e)
        except Exception as e:
            out = self.strings["phtest_error"].format(e)

        await utils.answer(message, out)

    @loader.command()
    async def phlistcmd(self, message):
        """- Показать все доступные плейсхолдеры"""
        listing = utils.config_placeholders()
        await utils.answer(message, listing or self.strings["phlist_empty"])


    async def _fetch_json(self, url, params=None):
        """GET с JSON-ответом, возвращает None при любой ошибке"""
        try:
            async with self.session.get(url, params=params) as resp:
                if resp.status == 200:
                    return await resp.json(content_type=None)
        except Exception as e:
            logger.debug(f"Fetch error {url}: {e}")
        return None

    async def _get_rates(self):
        """Курсы ЦБ: {код: сколько валюты за 1 USD}. er-api → cbr-xml фолбэк"""
        cache_key = "fx_rates"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        data = await self._fetch_json("https://open.er-api.com/v6/latest/USD")
        if data and data.get("result") == "success" and "rates" in data:
            rates = data["rates"]
            self.cache.set(cache_key, rates)
            return rates

        data = await self._fetch_json("https://www.cbr-xml-daily.ru/daily_json.js")
        if data and "Valute" in data:
            rates = {
                code: v["Value"] / v["Nominal"]
                for code, v in data["Valute"].items()
            }
            rates["RUB"] = 1.0
            self.cache.set(cache_key, rates)
            return rates

        return None

    async def _fmt_rate(self, code_from: str, code_to: str, digits: int = 2) -> str:
        rates = await self._get_rates()
        if not rates or code_from not in rates or code_to not in rates:
            return f"Курс {code_from} недоступен"
        rate = rates[code_to] / rates[code_from]
        return f"1 {code_from} ≈ {rate:.{digits}f} {code_to}"

    async def _get_crypto(self):
        """Цены BTC/ETH/TON в RUB и USD одним запросом"""
        cache_key = "crypto_prices"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        data = await self._fetch_json(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": "bitcoin,ethereum,toncoin", "vs_currencies": "rub,usd"},
        )
        if not data:
            return None

        self.cache.set(cache_key, data)
        return data

    async def _get_github(self):
        """Статистика GitHub-профиля"""
        user = self.config["github_username"]
        if not user:
            return None

        cache_key = f"github_{user}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        data = await self._fetch_json(f"https://api.github.com/users/{user}")
        if not data or data.get("message"):
            return {}

        result = {
            "repos": data.get("public_repos", 0),
            "followers": data.get("followers", 0),
        }
        self.cache.set(cache_key, result)
        return result

    def _format_delta(self, delta: timedelta) -> str:
        days = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, _ = divmod(remainder, 60)

        if days > 0:
            return f"{days}д {hours}ч {minutes}м"
        if hours > 0:
            return f"{hours}ч {minutes}м"
        return f"{minutes}м"

    def _weather_emoji_for(self, condition: str) -> str:
        c = condition.lower()
        if any(k in c for k in ("гроза", "thunder")):
            return "⛈️"
        if any(k in c for k in ("дожд", "ливень", "морос", "rain", "drizzle", "shower")):
            return "🌧️"
        if any(k in c for k in ("снег", "snow", "sleet")):
            return "❄️"
        if any(k in c for k in ("туман", "дымк", "fog", "mist", "haze")):
            return "🌫️"
        if any(k in c for k in ("пасмурн", "overcast", "облачн", "cloud")):
            return "☁️"
        if any(k in c for k in ("ясно", "солнц", "clear", "sunny")):
            return "☀️"
        return "🌡️"

    def _moon_phase(self) -> str:
        ref = datetime(2000, 1, 6, 18, 14, tzinfo=timezone.utc)
        days = (datetime.now(timezone.utc) - ref).total_seconds() / 86400
        age = days % 29.53058867
        phases = [
            (1.85, "🌑 Новолуние"),
            (5.54, "🌒 Растущий серп"),
            (9.23, "🌓 Первая четверть"),
            (12.92, "🌔 Растущая Луна"),
            (16.61, "🌕 Полнолуние"),
            (20.30, "🌖 Убывающая Луна"),
            (24.00, "🌗 Последняя четверть"),
            (27.69, "🌘 Убывающий серп"),
        ]
        for limit, name in phases:
            if age <= limit:
                return name
        return "🌑 Новолуние"

    def _zodiac_sign(self) -> str:
        now = datetime.now(self.tz)
        md = now.month * 100 + now.day
        bounds = [
            (120, "♑ Козерог"), (219, "♒ Водолей"), (321, "♓ Рыбы"),
            (420, "♈ Овен"), (521, "♉ Телец"), (621, "♊ Близнецы"),
            (723, "♋ Рак"), (823, "♌ Лев"), (923, "♍ Дева"),
            (1023, "♎ Весы"), (1122, "♏ Скорпион"), (1222, "♐ Стрелец"),
            (1232, "♑ Козерог"),
        ]
        for bound, sign in bounds:
            if md <= bound:
                return sign
        return "♑ Козерог"


    async def get_premium_check(self):
        if not self.me.premium:
            return "Нет Premium"

        until = self.full_me.full_user.premium_until
        if not until or until < time.time():
            return "Премиум закончился"

        end_date = datetime.fromtimestamp(until, tz=self.tz)
        days_left = (end_date.date() - datetime.now(self.tz).date()).days

        formatted = end_date.strftime("%d.%m.%Y")
        return f"{formatted} (Осталось {days_left} дней)"

    async def get_username(self):
        return f"@{self.me.username}" if self.me.username else "Нет"

    async def get_name(self):
        return self.me.first_name or "Нет"

    async def get_surname(self):
        return self.me.last_name or "Нет"

    async def get_bio(self):
        return self.full_me.full_user.about or "Нет описания"

    async def get_user_id(self):
        return str(self.me.id)

    async def get_phone(self):
        return self.me.phone or "Скрыт"

    async def get_dc_id(self):
        return str(self.me.dc_id if hasattr(self.me, "dc_id") else "Неизвестно")

    async def get_stars(self):
        try:
            result = await self._client(GetStarsStatusRequest("me"))
            stars = result.balance.amount if result and result.balance else 0
            return f"{stars:,}".replace(",", " ") if stars else "0"
        except Exception:
            return "0"


    async def get_usd_to_rub(self):
        return await self._fmt_rate("USD", "RUB")

    async def get_rub_to_usd(self):
        return await self._fmt_rate("RUB", "USD", 4)

    async def get_eur_to_rub(self):
        return await self._fmt_rate("EUR", "RUB")

    async def get_rub_to_eur(self):
        return await self._fmt_rate("RUB", "EUR", 4)

    async def get_cny_to_rub(self):
        return await self._fmt_rate("CNY", "RUB")

    async def get_kzt_to_rub(self):
        return await self._fmt_rate("KZT", "RUB")

    async def get_rub_to_kzt(self):
        return await self._fmt_rate("RUB", "KZT", 2)

    async def get_usdt_to_rub(self):
        return await self.get_usd_to_rub()

    async def get_rub_to_usdt(self):
        return await self.get_rub_to_usd()

    async def get_ton_to_rub(self):
        data = await self._get_crypto()
        if data and "toncoin" in data and "rub" in data["toncoin"]:
            rate = data["toncoin"]["rub"]
            return f"1 TON ≈ {rate:.2f} RUB"
        return "Курс TON недоступен"

    async def get_rub_to_ton(self):
        data = await self._get_crypto()
        if data and "toncoin" in data and "rub" in data["toncoin"]:
            rate = data["toncoin"]["rub"]
            if rate > 0:
                return f"1 RUB ≈ {1 / rate:.6f} TON"
        return "Курс недоступен"

    async def get_btc_to_rub(self):
        data = await self._get_crypto()
        if data and "bitcoin" in data and "rub" in data["bitcoin"]:
            rate = data["bitcoin"]["rub"]
            return f"1 BTC ≈ {rate:,.0f}".replace(",", " ") + " RUB"
        return "Курс BTC недоступен"

    async def get_eth_to_rub(self):
        data = await self._get_crypto()
        if data and "ethereum" in data and "rub" in data["ethereum"]:
            rate = data["ethereum"]["rub"]
            return f"1 ETH ≈ {rate:,.0f}".replace(",", " ") + " RUB"
        return "Курс ETH недоступен"

    async def get_stars_to_rub(self):
        rates = await self._get_rates()
        if rates and "RUB" in rates:
            return f"1 Star ≈ {STAR_USD * rates['RUB']:.2f} RUB"
        return "1 Star ≈ 1.98 RUB"

    async def get_stars_to_ton(self):
        data = await self._get_crypto()
        if data and "toncoin" in data and "usd" in data["toncoin"]:
            ton_usd = data["toncoin"]["usd"]
            if ton_usd > 0:
                return f"1 Star ≈ {STAR_USD / ton_usd:.4f} TON"
        return "1 Star ≈ 0.006 TON"

    async def get_stars_to_usdt(self):
        return f"1 Star ≈ {STAR_USD:.3f} USDT"


    async def get_os_uptime(self):
        boot = datetime.fromtimestamp(psutil.boot_time())
        return self._format_delta(datetime.now() - boot)

    async def get_bot_uptime(self):
        return self._format_delta(timedelta(seconds=int(time.time() - self._started_at)))

    async def get_internet_usage(self):
        try:
            net = psutil.net_io_counters()
            sent_gb = net.bytes_sent // (1024**3)
            recv_gb = net.bytes_recv // (1024**3)
            return f"↑ {sent_gb} GB │ ↓ {recv_gb} GB"
        except Exception:
            return "↑ 0 GB │ ↓ 0 GB"

    async def get_speedtest(self):
        cache_key = "speedtest"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        test_urls = [
            "https://proof.ovh.net/files/10Mb.dat",
            "http://ipv4.download.thinkbroadband.com/10MB.zip",
            "https://speedtest.ftp.otenet.gr/files/test10Mb.db"
        ]

        for url in test_urls:
            try:
                start = time.time()
                async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=20)) as resp:
                    chunk_size = 1024 * 1024
                    total = 0
                    async for chunk in resp.content.iter_chunked(chunk_size):
                        total += len(chunk)
                        if total >= chunk_size:
                            break

                duration = time.time() - start
                if duration > 0:
                    speed_mbps = (total * 8) / (duration * 1024 * 1024)
                    result = f"≈ {speed_mbps:.1f} Mbps"
                    self.cache.set(cache_key, result)
                    return result
            except Exception:
                continue

        return "Тест скорости недоступен"

    async def get_host(self):
        return platform.node() or "Неизвестно"

    async def get_shell(self):
        return os.environ.get("SHELL", "Неизвестно").split("/")[-1]

    async def get_gpu(self):
        return "N/A (Cloud)"

    async def get_disk(self):
        try:
            usage = psutil.disk_usage("/")
            percent = (usage.used / usage.total) * 100
            used_gb = usage.used // (1024**3)
            total_gb = usage.total // (1024**3)
            return f"{used_gb} GB / {total_gb} GB ({percent:.1f}%)"
        except Exception:
            return "Диск недоступен"

    async def get_local_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "Неизвестно"

    async def get_public_ip(self):
        cache_key = "public_ip"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        data = await self._fetch_json("https://api.ipify.org?format=json")
        if data and "ip" in data:
            self.cache.set(cache_key, data["ip"])
            return data["ip"]
        return "Неизвестно"

    async def get_ip_info(self):
        cache_key = "ip_info"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        data = await self._fetch_json(
            "http://ip-api.com/json/",
            params={"lang": "ru", "fields": "status,country,city,isp"},
        )
        if data and data.get("status") == "success":
            city = data.get("city") or "—"
            country = data.get("country") or "—"
            isp = data.get("isp") or ""
            result = f"{city}, {country}" + (f" · {isp}" if isp else "")
            self.cache.set(cache_key, result)
            return result
        return await self.get_public_ip()

    async def get_user_hostname(self):
        try:
            user = os.environ.get("USER") or os.environ.get("USERNAME") or "user"
        except Exception:
            user = "user"
        host = await self.get_host()
        return f"{user}@{host}"

    async def get_battery(self):
        try:
            battery = psutil.sensors_battery()
        except Exception:
            battery = None

        if battery is None:
            return "Нет батареи"

        percent = round(battery.percent)
        plugged = getattr(battery, "power_plugged", False)
        emoji = "⚡" if plugged else ("🪫" if percent <= 20 else "🔋")
        return f"{emoji} {percent}%"

    async def get_cpu_usage(self):
        try:
            return f"{psutil.cpu_percent(interval=None):.0f}%"
        except Exception:
            return "N/A"

    async def get_ram_usage(self):
        try:
            vm = psutil.virtual_memory()
            used_mb = vm.used // (1024**2)
            total_mb = vm.total // (1024**2)
            return f"{used_mb} MB / {total_mb} MB ({vm.percent:.0f}%)"
        except Exception:
            return "N/A"

    async def get_ping(self):
        cache_key = "tg_ping"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        try:
            start = time.perf_counter()
            await self._client(GetNearestDcRequest())
            ms = (time.perf_counter() - start) * 1000
            result = f"{ms:.0f} ms"
            self.cache.set(cache_key, result)
            return result
        except Exception:
            return "N/A"


    async def get_time(self):
        return datetime.now(self.tz).strftime(self.config["time_format"])

    async def get_date(self):
        return datetime.now(self.tz).strftime(self.config["date_format"])

    async def get_weekday(self):
        return self.weekdays_ru[datetime.now(self.tz).weekday()]

    async def get_date_time(self):
        now = datetime.now(self.tz)
        return now.strftime(f"{self.config['date_format']} {self.config['time_format']}")

    async def get_full_date_time_weekday(self):
        now = datetime.now(self.tz)
        dt = now.strftime(f"{self.config['date_format']} {self.config['time_format']}")
        return f"{dt} ({self.weekdays_ru[now.weekday()]})"

    async def get_moon_phase(self):
        return self._moon_phase()

    async def get_zodiac_sign(self):
        return self._zodiac_sign()

    async def get_weather_condition(self):
        data = await self._get_weather_data()
        return data.get("condition", "Неизвестно")

    async def get_temperature(self):
        data = await self._get_weather_data()
        return data.get("temp", "??°C")

    async def get_weather_temp(self):
        data = await self._get_weather_data()
        return data.get("weather_temp", "??")

    async def get_weather_emoji(self):
        data = await self._get_weather_data()
        return self._weather_emoji_for(data.get("condition", ""))

    async def get_feels_like(self):
        data = await self._get_weather_data()
        return data.get("feels_like", "??°C")

    async def get_humidity(self):
        data = await self._get_weather_data()
        return data.get("humidity", "??%")

    async def get_pressure(self):
        data = await self._get_weather_data()
        return data.get("pressure", "?? мм рт. ст.")

    async def get_wind_speed(self):
        data = await self._get_weather_data()
        return data.get("wind", "?? км/ч")

    async def _get_weather_data(self):
        city = self.config["weather_city"]
        cache_key = f"weather_{city}"

        cached = self.cache.get(cache_key)
        if cached:
            return cached

        default = {
            "condition": "Неизвестно",
            "temp": "??°C",
            "weather_temp": "Погода недоступна",
            "humidity": "??%",
            "pressure": "?? мм рт. ст.",
            "wind": "?? км/ч",
            "feels_like": "??°C",
        }

        try:
            url = f"http://wttr.in/{city}?format=j1&lang=ru"
            async with self.session.get(url) as resp:
                if resp.status != 200:
                    raise RuntimeError(f"wttr.in status {resp.status}")

                data = await resp.json(content_type=None)
                c = data.get("current_condition", [{}])[0]

                lang_ru_list = c.get("lang_ru", [])
                condition = lang_ru_list[0].get("value") if lang_ru_list else None

                if not condition:
                    weather_desc = c.get("weatherDesc", [])
                    condition = (
                        weather_desc[0].get("value") if weather_desc else "Неизвестно"
                    )

                try:
                    hpa = float(c.get("pressure", 0))
                    if self.config["pressure_unit"] == "гПа":
                        pressure_str = f"{hpa:.0f} гПа"
                    else:
                        pressure_str = f"{round(hpa * 0.750062)} мм рт. ст."
                except (TypeError, ValueError):
                    pressure_str = "N/A"

                try:
                    kmph = float(c.get("windspeedKmph", 0))
                    if self.config["wind_unit"] == "м/с":
                        wind_str = f"{kmph * 0.277778:.1f} м/с"
                    else:
                        wind_str = f"{kmph:.0f} км/ч"
                except (TypeError, ValueError):
                    wind_str = "N/A"

                weather_data = {
                    "condition": condition,
                    "temp": f"{c.get('temp_C', 'N/A')}°C",
                    "weather_temp": f"{self._weather_emoji_for(condition)} {condition}, {c.get('temp_C', 'N/A')}°C",
                    "humidity": f"{c.get('humidity', 'N/A')}%",
                    "pressure": pressure_str,
                    "wind": wind_str,
                    "feels_like": f"{c.get('FeelsLikeC', 'N/A')}°C",
                }

                self.cache.set(cache_key, weather_data)
                return weather_data

        except Exception as e:
            logger.debug(f"Ошибка получения погоды для {city}: {e}")

        self.cache.set(cache_key, default)
        return default


    async def get_crypto_address(self):
        return self.config["crypto_address"]

    async def get_card_number(self):
        return self.config["card_number"]

    async def get_donate_site(self):
        val = self.config["donate_site"]
        if ":" in val:
            name, link = val.split(":", 1)
            return f'<a href="{link.strip()}">{name.strip()}</a>'
        return val

    async def get_channel(self):
        ch = self.config["channel"]
        if ch.startswith("@"):
            return f'<a href="https://t.me/{ch[1:]}">{ch}</a>'
        return ch

    async def get_social(self):
        return self.config["social_network"]


    async def get_lastfm_user(self):
        return self.config["lastfm_user"] or "Не указан"

    async def get_now_playing(self):
        track = await self._get_current_track()
        if not track:
            return "🎵 Ничего не играет"
        return f"🎵 <b>{track['name']}</b> — {track['artist']}"

    async def get_user_and_playing(self):
        user = await self.get_lastfm_user()
        track = await self._get_current_track()
        if not track:
            return f"{user}: ничего не играет"
        return f"{user}: {track['name']} — {track['artist']}"

    async def get_song_name(self):
        track = await self._get_current_track()
        return track["name"] if track else "—"

    async def get_song_artist(self):
        track = await self._get_current_track()
        return track["artist"] if track else "—"

    async def get_lastfm_stats(self):
        user = self.config["lastfm_user"]
        if not user:
            return "Укажите Last.FM username"

        cache_key = f"lastfm_stats_{user}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        api_key = self.config["lastfm_api_key"]

        data = await self._fetch_json(
            "https://ws.audioscrobbler.com/2.0/",
            params={
                "method": "user.getinfo",
                "user": user,
                "api_key": api_key,
                "format": "json",
            },
        )
        if data and "user" in data:
            stats = data["user"]
            result = f"🎵 {stats['playcount']} скробблов"
            self.cache.set(cache_key, result)
            return result

        return "Статистика недоступна"

    async def _get_current_track(self):
        user = self.config["lastfm_user"]
        if not user:
            return None

        cache_key = f"lastfm_track_{user}"
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        api_key = self.config["lastfm_api_key"]

        data = await self._fetch_json(
            "https://ws.audioscrobbler.com/2.0/",
            params={
                "method": "user.getrecenttracks",
                "user": user,
                "api_key": api_key,
                "format": "json",
                "limit": 1,
            },
        )
        tracks = (data or {}).get("recenttracks", {}).get("track", [])

        if tracks:
            track = tracks[0]
            now_playing = "@attr" in track and "nowplaying" in track["@attr"]

            result = {
                "name": track["name"],
                "artist": track["artist"]["#text"],
                "now_playing": now_playing,
            }
            self.cache.set(cache_key, result)
            return result

        return None


    async def get_github_repos(self):
        stats = await self._get_github()
        if stats is None:
            return "Укажите GitHub username"
        if not stats:
            return "Пользователь не найден"
        return f"📦 {stats['repos']} репозиториев"

    async def get_github_followers(self):
        stats = await self._get_github()
        if stats is None:
            return "Укажите GitHub username"
        if not stats:
            return "Пользователь не найден"
        return f"👥 {stats['followers']} подписчиков"


    async def get_random_fact(self):
        data = await self._fetch_json(
            "https://uselessfacts.jsph.pl/api/v2/facts/random",
            params={"language": "ru"},
        )
        if data and data.get("text"):
            return f"💡 {data['text']}"
        return "Факт недоступен"

    async def get_quote(self):
        data = await self._fetch_json("https://zenquotes.io/api/random")
        if data and isinstance(data, list) and data[0].get("q"):
            return f"«{data[0]['q']}» — {data[0].get('a', '?')}"
        return "Цитата недоступна"

    async def get_joke(self):
        data = await self._fetch_json(
            "https://v2.jokeapi.dev/joke/Any",
            params={"type": "single", "safe-mode": ""},
        )
        if data and not data.get("error") and data.get("joke"):
            return f"😄 {data['joke']}"
        return "Шутка недоступна"

    async def get_advice(self):
        data = await self._fetch_json("https://api.adviceslip.com/advice")
        slip = (data or {}).get("slip") or {}
        if slip.get("advice"):
            return f"🧠 {slip['advice']}"
        return "Совет недоступен"

    async def get_cat_fact(self):
        data = await self._fetch_json("https://catfact.ninja/fact")
        if data and data.get("fact"):
            return f"🐱 {data['fact']}"
        return "Факт о котах недоступен"

    async def get_kanye_quote(self):
        data = await self._fetch_json("https://api.kanye.rest")
        if data and data.get("quote"):
            return f"🎤 {data['quote']}"
        return "Цитата недоступна"

    async def get_affirmation(self):
        data = await self._fetch_json("https://www.affirmations.dev/")
        if data and data.get("affirmation"):
            return f"✨ {data['affirmation']}"
        return "Аффирмация недоступна"


    async def on_unload(self):
        utils.unregister_placeholders(type(self).__name__)
        await self.session.close()
