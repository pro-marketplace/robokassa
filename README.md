# Robokassa Payment Integration

Интеграция платёжной системы Robokassa для приёма онлайн-платежей.

## Что включено

- `backend/robokassa/` — создание заказа и ссылки на оплату
- `backend/robokassa-webhook/` — обработка webhook от Robokassa
- `frontend/useRobokassa.ts` — React хук для работы с API
- `frontend/PaymentButton.tsx` — готовый компонент кнопки оплаты

## Установка

### 1. База данных

Выполни миграцию для создания таблиц заказов:

```sql
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    order_number VARCHAR(50) UNIQUE NOT NULL,
    user_name VARCHAR(255) NOT NULL,
    user_email VARCHAR(255) NOT NULL,
    user_phone VARCHAR(50),
    amount DECIMAL(10, 2) NOT NULL,
    robokassa_inv_id INTEGER UNIQUE,
    status VARCHAR(20) DEFAULT 'pending',
    payment_url TEXT,
    delivery_address TEXT,
    order_comment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    paid_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id) ON DELETE CASCADE,
    product_id VARCHAR(100),
    product_name VARCHAR(255) NOT NULL,
    product_price DECIMAL(10, 2) NOT NULL,
    quantity INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_orders_robokassa_inv_id ON orders(robokassa_inv_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);
```

### 2. Секреты

Добавь секреты в проект:

| Переменная | Описание |
|------------|----------|
| `ROBOKASSA_MERCHANT_LOGIN` | Логин магазина в Robokassa |
| `ROBOKASSA_PASSWORD_1` | Пароль #1 для создания платежей |
| `ROBOKASSA_PASSWORD_2` | Пароль #2 для проверки webhook |

### 3. Backend

Скопируй папки `backend/robokassa/` и `backend/robokassa-webhook/` в свой проект и выполни sync_backend.

### 4. Frontend

Скопируй файлы из `frontend/` в свой проект и используй:

```tsx
import { PaymentButton } from "@/components/PaymentButton";

<PaymentButton
  apiUrl={func2url.robokassa}
  amount={total}
  userName={formData.name}
  userEmail={formData.email}
  userPhone={formData.phone}
  userAddress={formData.address}
  cartItems={cart}
  onSuccess={(orderNumber) => router.push(`/success?order=${orderNumber}`)}
/>
```

### 5. Настройка Robokassa

В личном кабинете Robokassa укажи:

- **Result URL**: `{func2url.robokassa-webhook}`
- **Success URL**: `https://your-site.com/order-success`
- **Fail URL**: `https://your-site.com/order-failed`

## Поток оплаты

```
1. Пользователь нажимает "Оплатить"
   ↓
2. Frontend → POST /robokassa (amount, user_name, cart_items...)
   ↓
3. Backend создаёт заказ в БД, генерирует payment_url
   ↓
4. Frontend редиректит на Robokassa
   ↓
5. Пользователь оплачивает
   ↓
6. Robokassa → POST /robokassa-webhook (OutSum, InvId, SignatureValue)
   ↓
7. Backend проверяет подпись, обновляет status = 'paid'
   ↓
8. Robokassa редиректит на Success URL
```

## API

### POST /robokassa

Создание заказа и получение ссылки на оплату.

**Request:**
```json
{
  "amount": 1500.00,
  "user_name": "Иван Иванов",
  "user_email": "ivan@example.com",
  "user_phone": "+79991234567",
  "user_address": "Москва, ул. Примерная, 1",
  "cart_items": [
    {"id": "1", "name": "Товар", "price": 1500, "quantity": 1}
  ]
}
```

**Response:**
```json
{
  "payment_url": "https://auth.robokassa.ru/...",
  "order_id": 123,
  "order_number": "ORD-20241219-456789"
}
```

### POST /robokassa-webhook

Webhook от Robokassa (вызывается автоматически после оплаты).

**Response:** `OK{InvId}` при успехе

---

## После установки

После копирования файлов расширения, выполни интеграцию с фронтендом:

### Сценарий 1: Есть форма оплаты / checkout

Если в проекте уже есть страница оформления заказа или корзина с формой:

1. Найди компонент формы оплаты (обычно `Checkout.tsx`, `Cart.tsx`, `OrderForm.tsx`)
2. Импортируй `PaymentButton`:
   ```tsx
   import { PaymentButton } from "@/components/extensions/robokassa/PaymentButton";
   ```
3. Замени кнопку отправки формы на `PaymentButton`:
   ```tsx
   <PaymentButton
     apiUrl={func2url.robokassa}
     amount={totalAmount}
     userName={formData.name}
     userEmail={formData.email}
     userPhone={formData.phone}
     userAddress={formData.address}
     cartItems={cartItems}
     onSuccess={(orderNumber) => router.push(`/success?order=${orderNumber}`)}
     onError={(error) => toast.error(error.message)}
   />
   ```
4. Убедись что форма собирает все необходимые данные: имя, email, телефон, адрес

### Сценарий 2: Нет формы оплаты

Если формы оплаты нет, уточни у пользователя:

> Расширение Robokassa установлено! Теперь нужно добавить кнопку оплаты.
>
> Подскажи:
> 1. Где должна быть кнопка оплаты? (страница товара, корзина, отдельная страница)
> 2. Какие данные нужно собирать? (имя, email, телефон, адрес доставки)
> 3. Есть ли уже корзина товаров или это разовая оплата фиксированной суммы?

После ответа пользователя создай форму оплаты с `PaymentButton`.

### Проверка интеграции

После интеграции:
1. Убедись что секреты `ROBOKASSA_MERCHANT_LOGIN`, `ROBOKASSA_PASSWORD_1`, `ROBOKASSA_PASSWORD_2` добавлены
2. Проверь что Result URL в кабинете Robokassa указывает на `{func2url.robokassa-webhook}`
3. Сделай тестовый платёж через интерфейс Robokassa (1 рубль)

> **Важно:** Расширение работает в боевом режиме. Для тестирования используй реальные платежи на минимальную сумму (1₽). Тестовый режим Robokassa не используется — он усложняет интеграцию и требует отдельной настройки.
