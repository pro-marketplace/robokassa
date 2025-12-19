# Robokassa Payment Integration

Интеграция платёжной системы Robokassa для приёма онлайн-платежей.

## Описание

Расширение добавляет возможность принимать оплату через Robokassa:
- Создание платёжных ссылок
- Обработка webhook'ов от Robokassa
- Проверка статуса оплаты
- React компоненты для интеграции в UI

## Зависимости

### Python
```
# Уже есть в проекте
fastapi
pydantic
sqlalchemy
```

### React
```
# Нет дополнительных зависимостей
# Использует стандартный fetch API
```

## Backend

### Эндпоинты

| Метод | Путь | Описание |
|-------|------|----------|
| POST | `/api/robokassa/create-payment` | Создание платежа |
| POST | `/api/robokassa/webhook` | Webhook от Robokassa |
| GET | `/api/robokassa/check-status/{order_number}` | Проверка статуса |

### Файлы

- `backend/router.py` — FastAPI роутер с эндпоинтами
- `backend/models.py` — SQLAlchemy модели Order и OrderItem
- `backend/migration.sql` — SQL миграция для создания таблиц

## Frontend

### Компоненты

- `useRobokassa.ts` — React хук для работы с API
- `PaymentButton.tsx` — Готовая кнопка оплаты

### Утилиты

- `formatPhoneNumber()` — Форматирование телефона
- `isValidEmail()` — Валидация email
- `isValidPhone()` — Валидация телефона
- `openPaymentPage()` — Открытие страницы оплаты

## Интеграция

### 1. Backend

1. Скопировать `backend/models.py` в `app/db/models.py`:
   - Раскомментировать наследование от `BaseModel`
   - Добавить импорт `OrderStatus`

2. Скопировать `backend/router.py` в `app/src/api/v1/routers/robokassa.py`:
   - Раскомментировать импорты из проекта
   - Раскомментировать TODO блоки для работы с БД

3. Подключить роутер в `app/src/api/core/app.py`:
```python
from app.src.api.v1.routers import robokassa
api_router.include_router(robokassa.router)
```

4. Создать миграцию Alembic:
```bash
alembic revision --autogenerate -m "Add orders tables"
alembic upgrade head
```

Или выполнить `backend/migration.sql` напрямую.

### 2. Frontend

1. Скопировать `frontend/useRobokassa.ts` в `app/hooks/`

2. Скопировать `frontend/PaymentButton.tsx` в `app/components/`

3. Использовать в компонентах:
```tsx
import { PaymentButton } from "@/components/PaymentButton";

<PaymentButton
  apiUrl={process.env.NEXT_PUBLIC_API_URL}
  amount={total}
  userName={formData.name}
  userEmail={formData.email}
  userPhone={formData.phone}
  cartItems={cart}
  onSuccess={(orderNumber) => router.push(`/order-success?order=${orderNumber}`)}
/>
```

### 3. Настройка Robokassa

1. Зарегистрироваться на [robokassa.ru](https://robokassa.ru)

2. Создать магазин в личном кабинете

3. В настройках магазина указать:
   - **Result URL**: `https://your-api.com/api/robokassa/webhook`
   - **Success URL**: `https://your-site.com/order-success`
   - **Fail URL**: `https://your-site.com/order-failed`

4. Скопировать учётные данные:
   - MerchantLogin
   - Пароль #1 (для создания платежей)
   - Пароль #2 (для проверки webhook)

## Конфигурация

| Переменная | Описание | Обязательно |
|------------|----------|-------------|
| `ROBOKASSA_MERCHANT_LOGIN` | Логин магазина в Robokassa | Да |
| `ROBOKASSA_PASSWORD_1` | Пароль #1 для подписи платежей | Да |
| `ROBOKASSA_PASSWORD_2` | Пароль #2 для проверки webhook | Да |
| `ROBOKASSA_TEST_MODE` | Тестовый режим (0/1) | Нет |

## Поток оплаты

```
1. Пользователь заполняет форму заказа
   ↓
2. Frontend вызывает POST /create-payment
   ↓
3. Backend создаёт заказ в БД
   ↓
4. Backend генерирует подпись и payment_url
   ↓
5. Frontend редиректит на Robokassa
   ↓
6. Пользователь оплачивает
   ↓
7. Robokassa вызывает webhook
   ↓
8. Backend обновляет статус заказа на "paid"
   ↓
9. Frontend polling'ом проверяет статус
   ↓
10. Редирект на страницу успеха
```

## Тестирование

Для тестовых платежей передайте `isTest: true`:

```tsx
<PaymentButton
  isTest={process.env.NODE_ENV === "development"}
  ...
/>
```

Или установите `ROBOKASSA_TEST_MODE=1` на бекенде.

## Безопасность

- Пароли хранятся только в env переменных
- Все платежи подписываются MD5
- Webhook верифицирует подпись от Robokassa
- Идемпотентность: повторные webhook'и не ломают систему
