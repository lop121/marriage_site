from rest_framework.views import exception_handler
from rest_framework.response import Response


def custom_exception_handler(exc, context):
    # Пробуем стандартный обработчик DRF
    response = exception_handler(exc, context)

    if response is not None:
        # Достаём текст ошибки из исключения
        error_message = str(exc.detail) if hasattr(exc, 'detail') else str(exc)

        # Формируем кастомный ответ
        custom_response = {
            "success": False,
            "error": error_message,  # Ваше сообщение ("You have already sent an offer")
            "status_code": response.status_code  # 400, 403, 404 и т.д.
        }

        # Перезаписываем data и возвращаем response
        response.data = custom_response
        return response

    # Если response=None (например, необработанное исключение)
    error_message = str(exc)
    return Response(
        {
            "success": False,
            "error": error_message,
            "status_code": 500  # Или другой код
        },
        status=500
    )