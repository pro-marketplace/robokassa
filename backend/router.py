"""
Robokassa Payment Integration Router
"""
import hashlib
import os
import random
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Импорты из основного проекта (нужно адаптировать пути)
# from app.db.sessionmaker import get_db_session
# from app.db.models import Order, OrderItem


router = APIRouter(prefix="/robokassa", tags=["robokassa"])


# ============================================================================
# КОНФИГУРАЦИЯ
# ============================================================================

ROBOKASSA_MERCHANT_LOGIN = os.getenv("ROBOKASSA_MERCHANT_LOGIN")
ROBOKASSA_PASSWORD_1 = os.getenv("ROBOKASSA_PASSWORD_1")
ROBOKASSA_PASSWORD_2 = os.getenv("ROBOKASSA_PASSWORD_2")
ROBOKASSA_TEST_MODE = os.getenv("ROBOKASSA_TEST_MODE", "0") == "1"


# ============================================================================
# СХЕМЫ
# ============================================================================

class CartItem(BaseModel):
    id: int
    name: str
    price: float
    quantity: int


class CreatePaymentRequest(BaseModel):
    amount: float
    user_name: str
    user_email: EmailStr
    user_phone: str
    user_address: Optional[str] = None
    order_comment: Optional[str] = None
    cart_items: list[CartItem]
    is_test: bool = False


@dataclass
class CreatePaymentResponse:
    payment_url: str
    order_id: int
    order_number: str
    robokassa_inv_id: int
    amount: str


@dataclass
class WebhookResponse:
    success: bool
    message: str


# ============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================================

def generate_signature(*args: str, password: str) -> str:
    """Генерирует MD5 сигнатуру для Robokassa"""
    signature_string = ":".join(str(arg) for arg in args) + f":{password}"
    return hashlib.md5(signature_string.encode()).hexdigest()


def generate_invoice_id() -> int:
    """Генерирует уникальный InvoiceID"""
    return random.randint(100000, 2147483647)


def generate_order_number(invoice_id: int) -> str:
    """Генерирует номер заказа"""
    date_str = datetime.now().strftime("%Y%m%d")
    return f"ORD-{date_str}-{invoice_id}"


def build_payment_url(
    merchant_login: str,
    amount: float,
    invoice_id: int,
    signature: str,
    email: str,
    description: str,
    is_test: bool = False,
) -> str:
    """Формирует URL для перенаправления на Robokassa"""
    params = {
        "MerchantLogin": merchant_login,
        "OutSum": f"{amount:.2f}",
        "InvoiceID": invoice_id,
        "SignatureValue": signature,
        "Email": email,
        "Culture": "ru",
        "Description": description,
    }
    if is_test:
        params["IsTest"] = 1

    return f"https://auth.robokassa.ru/Merchant/Index.aspx?{urlencode(params)}"


# ============================================================================
# ЭНДПОИНТЫ
# ============================================================================

@router.post("/create-payment", response_model=CreatePaymentResponse)
async def create_payment(
    data: CreatePaymentRequest,
    # session: AsyncSession = Depends(get_db_session),
) -> CreatePaymentResponse:
    """
    Создаёт заказ и возвращает ссылку на оплату Robokassa.

    1. Валидирует данные
    2. Генерирует InvoiceID
    3. Создаёт заказ в БД
    4. Формирует подпись
    5. Возвращает payment_url
    """
    if not ROBOKASSA_MERCHANT_LOGIN or not ROBOKASSA_PASSWORD_1:
        raise HTTPException(
            status_code=500,
            detail="Robokassa credentials not configured",
        )

    if data.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    # Генерация уникального InvoiceID
    invoice_id = generate_invoice_id()
    order_number = generate_order_number(invoice_id)
    amount_str = f"{data.amount:.2f}"

    # TODO: Создание заказа в БД
    # order = Order(
    #     order_number=order_number,
    #     user_name=data.user_name,
    #     user_email=data.user_email,
    #     user_phone=data.user_phone,
    #     amount=data.amount,
    #     robokassa_inv_id=invoice_id,
    #     status="pending",
    #     delivery_address=data.user_address,
    #     order_comment=data.order_comment,
    # )
    # session.add(order)
    # await session.commit()
    #
    # for item in data.cart_items:
    #     order_item = OrderItem(
    #         order_id=order.id,
    #         product_id=item.id,
    #         product_name=item.name,
    #         product_price=item.price,
    #         quantity=item.quantity,
    #     )
    #     session.add(order_item)
    # await session.commit()

    # Генерация подписи
    signature = generate_signature(
        ROBOKASSA_MERCHANT_LOGIN,
        amount_str,
        invoice_id,
        password=ROBOKASSA_PASSWORD_1,
    )

    # Формирование URL
    is_test = data.is_test or ROBOKASSA_TEST_MODE
    payment_url = build_payment_url(
        merchant_login=ROBOKASSA_MERCHANT_LOGIN,
        amount=data.amount,
        invoice_id=invoice_id,
        signature=signature,
        email=data.user_email,
        description=f"Заказ {order_number}",
        is_test=is_test,
    )

    # TODO: Сохранение payment_url в БД
    # order.payment_url = payment_url
    # await session.commit()

    return CreatePaymentResponse(
        payment_url=payment_url,
        order_id=1,  # TODO: order.id
        order_number=order_number,
        robokassa_inv_id=invoice_id,
        amount=amount_str,
    )


@router.post("/webhook")
async def robokassa_webhook(
    request: Request,
    # session: AsyncSession = Depends(get_db_session),
) -> str:
    """
    Result URL webhook от Robokassa.

    Вызывается после успешной оплаты.
    Должен вернуть "OK{InvId}" для подтверждения.
    """
    if not ROBOKASSA_PASSWORD_2:
        raise HTTPException(
            status_code=500,
            detail="Robokassa password_2 not configured",
        )

    # Парсинг параметров (поддержка разных форматов)
    content_type = request.headers.get("content-type", "")

    if "application/json" in content_type:
        params = await request.json()
    elif "application/x-www-form-urlencoded" in content_type:
        form = await request.form()
        params = dict(form)
    else:
        # Query string
        params = dict(request.query_params)

    out_sum = params.get("OutSum")
    inv_id = params.get("InvId")
    signature_value = params.get("SignatureValue")

    if not all([out_sum, inv_id, signature_value]):
        raise HTTPException(
            status_code=400,
            detail="Missing required parameters: OutSum, InvId, SignatureValue",
        )

    # Верификация подписи
    expected_signature = generate_signature(
        out_sum,
        inv_id,
        password=ROBOKASSA_PASSWORD_2,
    ).upper()

    if signature_value.upper() != expected_signature:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # TODO: Обновление статуса заказа
    # result = await session.execute(
    #     select(Order).where(
    #         Order.robokassa_inv_id == int(inv_id),
    #         Order.status == "pending",
    #     )
    # )
    # order = result.scalar_one_or_none()
    #
    # if order:
    #     order.status = "paid"
    #     order.paid_at = datetime.now()
    #     await session.commit()
    #
    #     # Отправка уведомлений (Telegram, Email)
    #     # await send_payment_notification(order)

    # Ответ Robokassa (обязательный формат!)
    return f"OK{inv_id}"


@router.get("/check-status/{order_number}")
async def check_payment_status(
    order_number: str,
    # session: AsyncSession = Depends(get_db_session),
) -> dict:
    """
    Проверка статуса оплаты заказа.
    Используется для polling на фронтенде.
    """
    # TODO: Получение заказа из БД
    # result = await session.execute(
    #     select(Order).where(Order.order_number == order_number)
    # )
    # order = result.scalar_one_or_none()
    #
    # if not order:
    #     raise HTTPException(status_code=404, detail="Order not found")
    #
    # return {
    #     "order_number": order.order_number,
    #     "status": order.status,
    #     "amount": float(order.amount),
    #     "paid_at": order.paid_at.isoformat() if order.paid_at else None,
    # }

    return {
        "order_number": order_number,
        "status": "pending",
        "amount": 0,
        "paid_at": None,
    }
