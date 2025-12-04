from tgbot.customLib.bitrixAPI.base import BaseApi, MethodRequest


class Leads(BaseApi):

    def __init__(
            self,
            user_id: str,
            basic_token: str
    ):
        super().__init__(user_id=user_id, basic_token=basic_token)

    async def create(
            self,
            fields: dict,
            json: dict = None
    ):
        url = self.url.format(method='crm.lead.add')
        result = await self.request_session(
            method=MethodRequest.post,
            url=url,
            json_status=True,
            answer_log=False,
            params=fields,
            json=json
        )

        return result

    async def update(
            self,
            fields: dict
    ):
        url = self.url.format(method='crm.lead.update')
        result = await self.request_session(
            method=MethodRequest.post,
            url=url,
            json_status=True,
            answer_log=False,
            params=fields
        )

        return result
