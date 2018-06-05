class TipicaException(Exception):
    message = "An unknown exception occurred."

    def __init__(self, message=None, **kwarg):
        msg = message or self.message
        if len(kwarg):
            try:
                msg = msg % kwarg
            except Exception:
                pass

        super(TipicaException, self).__init__(msg)


class TimeoutExpired(TipicaException):
    message = "Timeout expired."


class DriverFailed(TipicaException):
    message = "Failed to execute ipmitool: %(err)s"


class DriverNotSupported(TipicaException):
    message = "Tipica driver %(driver)s does not support %(command)s."
