import datetime
import logging
import random
import string
import time

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from tgbot.models.database.cods import Cods


class ExceptionGenerateCode(ValueError):
    pass


async def generate_code(
        session: AsyncSession,
        phone_number: str
):
    end_time = time.time() + 30

    while time.time() < end_time:

        try:
            unique_code = "".join(random.choices(string.digits, k=6))
            code_model = Cods(
                code=unique_code,
                phone_number=phone_number,
                created_at=datetime.datetime.now()
            )
            session.add(code_model)
            await session.commit()
            return code_model
        except IntegrityError as e:
            logging.info(
                f"Не получилось создать: {e}"
            )

    raise ExceptionGenerateCode(
        "Не получилось сгенерировать промокод"
    )


