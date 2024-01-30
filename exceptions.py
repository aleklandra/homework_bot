class SendExceptionError(Exception):
    """Класс для уровня ошибок ERROR. Их пересылаем в ТГ."""

    pass


class NotSendExceptionError(Exception):
    """Остальные ошибки. Их не пересылаем в ТГ."""

    pass
