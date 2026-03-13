import typing

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton


class GenerateMarkupButtons:
    def __init__(self,
                 laylout: typing.List or int,
                 markup: typing.Union[InlineKeyboardMarkup, ReplyKeyboardMarkup],
                 keyboards: typing.List[typing.Union[InlineKeyboardButton, KeyboardButton]]):
        self.laylout: typing.Union[typing.List, int] = laylout
        self.keyboards: typing.List[typing.Union[InlineKeyboardButton, KeyboardButton]] = keyboards
        self.markup: typing.Union[InlineKeyboardMarkup, ReplyKeyboardMarkup] = markup

    def insert(self, keyboards) -> list:
        for _keyboard in self.keyboards:
            if len(keyboards[-1]) < self.laylout:
                keyboards[-1].append(_keyboard)
            else:
                keyboards.append([_keyboard])
        return keyboards

    def _generate(self):
        c = 0
        res = []
        if type(self.laylout) is int:
            keyboards = [[]]
            res = self.insert(keyboards)
        else:
            for row in self.laylout:
                res.append([])
                for _i in range(row):
                    res[len(res) - 1].append(self.keyboards[c])
                    c += 1
        return res

    def get(self):
        keyboards = self._generate()
        for row_keyboards in keyboards:
            self.markup.row(*row_keyboards)
        return self.markup
