"""
Модели для Robokassa Payment Integration

Добавить в app/db/models.py
"""
import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
    Numeric,
    Enum,
    func,
    select,
)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship, Mapped

# from app.db import BaseModel


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class Order:  # (BaseModel):
    """Заказ с оплатой через Robokassa"""

    __tablename__ = "core_order"

    id = Column(Integer, primary_key=True)
    order_number = Column(String(50), unique=True, nullable=False, index=True)

    # Данные покупателя
    user_name = Column(String(255), nullable=False)
    user_email = Column(String(255), nullable=False, index=True)
    user_phone = Column(String(50))

    # Сумма и валюта
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(10), default="RUB")

    # Статус
    status = Column(
        Enum(OrderStatus),
        default=OrderStatus.PENDING,
        nullable=False,
        index=True,
    )

    # Robokassa
    robokassa_inv_id = Column(Integer, unique=True, index=True)
    payment_url = Column(Text)

    # Доставка
    delivery_address = Column(Text)
    delivery_type = Column(String(50))
    delivery_cost = Column(Numeric(10, 2), default=0)

    # Дополнительно
    order_comment = Column(Text)

    # Timestamps
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    paid_at = Column(DateTime)

    # Связи
    items: Mapped[list["OrderItem"]] = relationship(
        "OrderItem", back_populates="order", lazy="selectin"
    )

    @classmethod
    async def get_by_order_number(
        cls, session: AsyncSession, order_number: str
    ) -> Optional["Order"]:
        result = await session.execute(
            select(cls).where(cls.order_number == order_number)
        )
        return result.scalar_one_or_none()

    @classmethod
    async def get_by_invoice_id(
        cls, session: AsyncSession, invoice_id: int
    ) -> Optional["Order"]:
        result = await session.execute(
            select(cls).where(cls.robokassa_inv_id == invoice_id)
        )
        return result.scalar_one_or_none()


class OrderItem:  # (BaseModel):
    """Позиция заказа"""

    __tablename__ = "core_order_item"

    id = Column(Integer, primary_key=True)
    order_id = Column(
        Integer,
        ForeignKey("core_order.id"),
        nullable=False,
        index=True,
    )
    product_id = Column(Integer, nullable=False)
    product_name = Column(String(255), nullable=False)
    product_price = Column(Numeric(10, 2), nullable=False)
    quantity = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, server_default=func.now())

    # Связи
    order: Mapped["Order"] = relationship("Order", back_populates="items")
