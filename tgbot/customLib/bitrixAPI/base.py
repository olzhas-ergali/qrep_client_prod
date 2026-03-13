import json
import logging
import typing

import aiohttp
import requests

from tgbot import config


class MethodRequest:
    post = 'POST'
    put = 'PUT'
    get = 'GET'
    delete = 'DELETE'
    patch = 'PATCH'


def to_format(
        data
) -> str:
    if data is None:
        return ""
    return data


class BaseApi:

    def __init__(
            self,
            user_id: str,
            basic_token: str,
    ):
        self.production_url = f'https://bitrix.qazaqrepublic.com/rest/{user_id}/{basic_token}/' + '{method}'

    @property
    def url(self) -> str:
        return self.production_url

    @classmethod
    async def request_session(
            cls,
            method: MethodRequest.get,
            url: str,
            json_status: bool = True,
            answer_log: bool = False,
            **kwargs

    ):
        logging.info(
            f"METHOD {method}\nURL - {url}\n"
            f"dict - > {kwargs}"
        )

        async with aiohttp.ClientSession() as session:
            response = await session.request(
                method=method,
                url=url,
                **kwargs
            )

            if response.status == 400:
                logging.info("STATUS CODE -> 400")
                return

            try:
                if json_status:
                    data = await response.read()
                    data = json.loads(data)
                    return data
            except Exception as e:
                logging.exception(e)
            finally:
                if answer_log:
                    logging.info(
                        f'ANSWER: {await response.text()}'
                    )

            return response
