class ExceptionError(Exception):
    """Класс для уровня ошибок ERROR."""

    pass


class CriticalExceptionError(Exception):
    """Класс для уровня ошибок CRITICAL."""

    pass


class DebugException(Exception):
    """Класс для изменений типа DEBUG."""

    pass
