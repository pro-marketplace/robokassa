-- Миграция для Robokassa Payment Integration
-- Создание таблиц orders и order_items

-- Enum для статуса заказа
CREATE TYPE orderstatus AS ENUM ('pending', 'paid', 'cancelled', 'refunded');

-- Таблица заказов
CREATE TABLE core_order (
    id SERIAL PRIMARY KEY,
    order_number VARCHAR(50) UNIQUE NOT NULL,

    -- Данные покупателя
    user_name VARCHAR(255) NOT NULL,
    user_email VARCHAR(255) NOT NULL,
    user_phone VARCHAR(50),

    -- Сумма
    amount NUMERIC(10, 2) NOT NULL,
    currency VARCHAR(10) DEFAULT 'RUB',

    -- Статус
    status orderstatus DEFAULT 'pending' NOT NULL,

    -- Robokassa
    robokassa_inv_id INTEGER UNIQUE,
    payment_url TEXT,

    -- Доставка
    delivery_address TEXT,
    delivery_type VARCHAR(50),
    delivery_cost NUMERIC(10, 2) DEFAULT 0,

    -- Дополнительно
    order_comment TEXT,

    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    paid_at TIMESTAMP
);

-- Индексы для orders
CREATE INDEX idx_core_order_order_number ON core_order(order_number);
CREATE INDEX idx_core_order_user_email ON core_order(user_email);
CREATE INDEX idx_core_order_status ON core_order(status);
CREATE INDEX idx_core_order_robokassa_inv_id ON core_order(robokassa_inv_id);

-- Таблица позиций заказа
CREATE TABLE core_order_item (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES core_order(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL,
    product_name VARCHAR(255) NOT NULL,
    product_price NUMERIC(10, 2) NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Индекс для order_items
CREATE INDEX idx_core_order_item_order_id ON core_order_item(order_id);
