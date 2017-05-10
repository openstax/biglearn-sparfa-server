class APIError(Exception):
    """API Base exception"""
    pass


class RequestError(APIError):
    """Exception for issues regarding a request. """
    def __init__(self, exc, *args, **kwargs):
        self.exc = exc
        self.detail = str(exc)
        super().__init__(*args, **kwargs)

    def __str__(self):
        return self.detail
