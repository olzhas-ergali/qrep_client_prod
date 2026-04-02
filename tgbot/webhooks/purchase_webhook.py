import asyncio
import logging
from typing import Optional

from aiohttp import web, hdrs
from aiohttp.web_request import Request
from aiohttp.web_response import Response

from tgbot.services.notification_service import NotificationService
from tgbot.config import Config

logger = logging.getLogger(__name__)


async def _purchase_review_bg(
    session_factory,
    notification_service: NotificationService,
    phone_number: str,
    telegram_id: int,
    purchase_id: Optional[str],
) -> None:
    try:
        async with session_factory() as session:
            ok = await notification_service.send_purchase_review_notification(
                session=session,
                phone_number=phone_number,
                telegram_id=telegram_id,
                purchase_id=purchase_id,
            )
            if ok:
                logger.info(
                    "Purchase notification sent successfully for phone: %s",
                    phone_number,
                )
            else:
                logger.error(
                    "Failed to send purchase notification for phone: %s",
                    phone_number,
                )
    except Exception:
        logger.exception("Background purchase notification failed for phone: %s", phone_number)


class PurchaseWebhookHandler:
    """Обработчик webhook'ов о покупках"""
    
    def __init__(self, config: Config, db_session_factory):
        self.config = config
        self.db_session_factory = db_session_factory
        self.notification_service = NotificationService(config)
    
    async def handle_purchase_notification(self, request: Request) -> Response:
        """
        Обрабатывает POST-запрос с данными о покупке
        
        Ожидаемый JSON:
        {
            "phone_number": "+7700123456",
            "telegram_id": 123456789,
            "purchase_id": "optional_purchase_id"
        }
        """
        try:
            # Проверяем Content-Type
            if request.content_type != 'application/json':
                return web.json_response(
                    {"error": "Invalid Content-Type. Expected application/json"},
                    status=400
                )
            
            # Получаем данные из запроса
            try:
                data = await request.json()
            except Exception as e:
                logger.error(f"Failed to parse JSON: {str(e)}")
                return web.json_response(
                    {"error": "Invalid JSON format"},
                    status=400
                )
            
            # Валидируем обязательные поля
            phone_number = data.get('phone_number')
            telegram_id = data.get('telegram_id')
            
            if not phone_number:
                return web.json_response(
                    {"error": "phone_number is required"},
                    status=400
                )
            
            if not telegram_id:
                return web.json_response(
                    {"error": "telegram_id is required"},
                    status=400
                )
            
            try:
                telegram_id = int(telegram_id)
            except (ValueError, TypeError):
                return web.json_response(
                    {"error": "telegram_id must be a valid integer"},
                    status=400
                )
            
            # Опциональные поля
            purchase_id = data.get('purchase_id')

            asyncio.create_task(
                _purchase_review_bg(
                    self.db_session_factory,
                    self.notification_service,
                    phone_number,
                    telegram_id,
                    purchase_id,
                )
            )
            return web.json_response(
                {
                    "status": "accepted",
                    "message": "Notification queued",
                },
                status=200,
            )
        
        except Exception as e:
            logger.error(f"Unexpected error in purchase webhook: {str(e)}")
            return web.json_response(
                {
                    "status": "error",
                    "message": "Internal server error"
                },
                status=500
            )
    
    async def handle_health_check(self, request: Request) -> Response:
        """Health check endpoint"""
        return web.json_response({"status": "healthy"}, status=200)


def setup_webhook_routes(app: web.Application, handler: PurchaseWebhookHandler):
    """Настройка маршрутов для webhook'ов"""
    
    # Основной endpoint для уведомлений о покупках
    app.router.add_post('/purchase-notification', handler.handle_purchase_notification)
    
    # Health check
    app.router.add_get('/health', handler.handle_health_check)
    
    # CORS для всех маршрутов (если нужно)
    app.router.add_route(hdrs.METH_OPTIONS, '/purchase-notification', handle_cors_preflight)


async def handle_cors_preflight(request: Request) -> Response:
    """Обработка CORS preflight запросов"""
    return web.Response(
        headers={
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, GET, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
        }
    )
