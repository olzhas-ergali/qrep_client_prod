import re
import typing


def parse_phone(value: str):
    return value.strip().replace("+", '').replace(' ', '')


def is_mail_valid(email) -> typing.Optional[bool]:
    regex = re.compile(r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+')
    if re.fullmatch(regex, email):
        return True
    return False
