# На модуль распространяется лицензия "GNU General Public License v3.0"
# https://github.com/all-licenses/GNU-General-Public-License-v3.0

# meta developer: @pymodule
# meta fhsdesc: tool, tools, random

from .. import loader, utils
from ..inline.types import InlineQuery
import random
from herokutl.tl.types import Message

@loader.tds
class RandomizerMod(loader.Module):
    """Randomly selects one of the comma-separated values."""

    strings = {
        "name": "Randomizer",
        "too_few_values": "Please provide at least two values separated by commas.",
        "result": "Random choice: {result}",
        "inline_title": "🎲 Random choice",
        "inline_description": "{result}",
    }

    strings_ru = {
        "name": "Рандомайзер",
        "_cls_doc": "Случайно выбирает одно из значений, перечисленных через запятую",
        "too_few_values": "Укажи хотя бы два значения через запятую.",
        "result": "Случайный выбор: {result}",
        "inline_title": "🎲 Случайный выбор",
        "inline_description": "{result}",
    }

    @loader.command(
        doc="Picks a random value from those listed (comma-separated)",
        ru_doc="Выбирает случайное значение из перечисленных через запятую"
    )
    async def randomizecmd(self, message: Message):
        items = self._parse(utils.get_args_raw(message))
        if not items:
            await utils.answer(message, self.strings("too_few_values"))
            return

        await utils.answer(message, self.strings("result").format(result=random.choice(items)))

    @loader.inline_everyone
    @loader.inline_handler()
    async def randomizer_inline_handler(self, query: InlineQuery):
        """Random - Pick a random value from the comma-separated list"""
        items = self._parse(query.args)
        if not items:
            return None

        result = random.choice(items)
        return [{
            "title": self.strings("inline_title"),
            "description": self.strings("inline_description").format(result=result),
            "message": self.strings("result").format(result=result),
        }]

    @staticmethod
    def _parse(args: str) -> list[str]:
        if not args:
            return []
        items = [item.strip() for item in args.split(",") if item.strip()]
        return items if len(items) >= 2 else []
