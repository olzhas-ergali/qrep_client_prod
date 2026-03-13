import json
import logging
import asyncio

from service.tgbot.lib.SendPlusAPI.base import BaseApi, MethodRequest


class SendPlus(BaseApi):

    def __init__(
            self,
            client_id: str,
            client_secret: str,
            waba_bot_id: str
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.waba_bot_id = waba_bot_id
        super().__init__()

    async def send_template_by_phone(
            self,
            phone: str,
            bot_id: str,
            template: dict | str = None
    ):
        url = self.url.format(method='contacts/sendTemplateByPhone')
        # local = await self.get_local_by_phone(
        #     phone=phone
        # )
        #logging.info(json.loads(template))
        result = await self.request_session(
            method=MethodRequest.post,
            url=url,
            client_id=self.client_id,
            client_secret=self.client_secret,
            json_status=True,
            answer_log=False,
            params={'phone': phone},
            json={
                "bot_id": bot_id,
                "phone": phone,
                "template": json.loads(template) if isinstance(template, str) else template
            }
        )
        await asyncio.sleep(0.3)
        return result

    async def send_by_phone(
            self,
            phone: str,
            bot_id: str,
            text: str = None,
            texts: dict = None
    ):
        url = self.url.format(method='contacts/sendByPhone')
        local = await self.get_local_by_phone(
            phone=phone
        )
        logging.info(local)
        result = await self.request_session(
            method=MethodRequest.post,
            url=url,
            client_id=self.client_id,
            client_secret=self.client_secret,
            json_status=True,
            answer_log=False,
            #params={'phone': phone},
            json={
                "bot_id": bot_id,
                "phone": phone,
                "message": {
                    "type": "text",
                    "text": {
                        "body": texts.get(local) if texts else text
                    }
                }
            }
        )
        #"body": texts.get(local) if texts else text

        return result

    async def get_local_by_phone(
            self,
            phone: str,
            json: dict = None
    ):
        url = self.url.format(method='contacts/getByPhone')
        result = await self.request_session(
            method=MethodRequest.get,
            url=url,
            client_id=self.client_id,
            client_secret=self.client_secret,
            json_status=True,
            answer_log=False,
            params={'phone': phone, 'bot_id': self.waba_bot_id}
        )

        if result.get('data'):
            return result.get('data').get('variables').get('local')
        return 'rus'

