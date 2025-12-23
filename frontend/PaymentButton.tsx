/**
 * Robokassa Payment Button Component
 *
 * Кнопка для инициации оплаты через Robokassa.
 */
import React, { useState } from "react";
import {
  useRobokassa,
  openPaymentPage,
  type CartItem,
  type PaymentPayload,
} from "./useRobokassa";

// ============================================================================
// ТИПЫ
// ============================================================================

interface PaymentButtonProps {
  /** URL API бекенда */
  apiUrl: string;
  /** Сумма к оплате */
  amount: number;
  /** Данные покупателя */
  userName: string;
  userEmail: string;
  userPhone: string;
  userAddress?: string;
  orderComment?: string;
  /** Товары в корзине */
  cartItems: CartItem[];
  /** Callback при успешной оплате */
  onSuccess?: (orderNumber: string) => void;
  /** Callback при ошибке */
  onError?: (error: Error) => void;
  /** Текст кнопки */
  buttonText?: string;
  /** CSS класс */
  className?: string;
  /** Отключена */
  disabled?: boolean;
}

// ============================================================================
// КОМПОНЕНТ
// ============================================================================

export function PaymentButton({
  apiUrl,
  amount,
  userName,
  userEmail,
  userPhone,
  userAddress,
  orderComment,
  cartItems,
  onSuccess,
  onError,
  buttonText = "Оплатить",
  className = "",
  disabled = false,
}: PaymentButtonProps): React.ReactElement {
  const [isPending, setIsPending] = useState(false);

  const { createPayment, isLoading, error } = useRobokassa({
    apiUrl,
    onSuccess,
    onError,
  });

  const handleClick = async () => {
    if (disabled || isLoading || isPending) return;

    setIsPending(true);

    try {
      const payload: PaymentPayload = {
        amount,
        userName,
        userEmail,
        userPhone,
        userAddress,
        orderComment,
        cartItems,
      };

      const result = await createPayment(payload);

      // Открываем страницу оплаты
      openPaymentPage(result.payment_url);
    } catch (err) {
      console.error("Payment error:", err);
    } finally {
      setIsPending(false);
    }
  };

  const isDisabled = disabled || isLoading || isPending;
  const buttonLabel = isLoading || isPending ? "Загрузка..." : buttonText;

  return (
    <button
      type="button"
      onClick={handleClick}
      disabled={isDisabled}
      className={className}
      style={{
        opacity: isDisabled ? 0.6 : 1,
        cursor: isDisabled ? "not-allowed" : "pointer",
      }}
    >
      {buttonLabel}
    </button>
  );
}

// ============================================================================
// ПРИМЕР ИСПОЛЬЗОВАНИЯ
// ============================================================================

/*
import { PaymentButton } from "./PaymentButton";

function CheckoutPage() {
  const cartItems = [
    { id: 1, name: "Товар 1", price: 1000, quantity: 2 },
    { id: 2, name: "Товар 2", price: 500, quantity: 1 },
  ];

  const total = cartItems.reduce(
    (sum, item) => sum + item.price * item.quantity,
    0
  );

  return (
    <PaymentButton
      apiUrl="https://api.example.com"
      amount={total}
      userName="Иван Иванов"
      userEmail="ivan@example.com"
      userPhone="+79991234567"
      userAddress="Москва, ул. Примерная, д. 1"
      cartItems={cartItems}
      onSuccess={(orderNumber) => {
        console.log("Оплачен заказ:", orderNumber);
        // Редирект на страницу успеха
      }}
      onError={(error) => {
        console.error("Ошибка оплаты:", error);
        // Показать уведомление
      }}
      buttonText="Оплатить заказ"
      className="btn btn-primary"
    />
  );
}
*/
