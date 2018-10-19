from logging import getLogger
from json.decoder import JSONDecodeError
from functools import wraps

__logs__ = getLogger(__name__)


class BiglearnError(Exception):
    """The base exception class."""

    def __init__(self, resp):
        super().__init__(resp)
        self.response = resp
        self.code = resp.status_code
        try:
            json = resp.json()
        except JSONDecodeError:
            json = {}
        self.msg = json.get('errors', resp.content)

    def __repr__(self):
        return '<{0} [{1}]>'.format(self.__class__.__name__, self.msg or self.code)

    def __str__(self):
        return '{0} {1}'.format(self.code, self.msg)

    @property
    def message(self):
        """The actual message returned by the API."""
        return self.msg


class ResponseError(BiglearnError):
    """The base exception for errors stemming from Biglearn API or Scheduler responses"""
    pass


class ClientError(ResponseError):
    """Exception class for 4xx responses"""
    pass


class BadRequest(ClientError):
    """Exception class for 400 responses"""
    pass


class Forbidden(ClientError):
    """Exception class for 403 responses"""
    pass


class NotFound(ClientError):
    """Exception class for 404 responses"""
    pass


class ServerError(ResponseError):
    """Exception class for 5xx responses."""
    pass


class BadGateway(ServerError):
    """Exception class for 502 responses"""
    pass


class ServiceUnavailable(ServerError):
    """Exception class for 503 responses"""
    pass


class GatewayTimeout(ServerError):
    """Exception class for 504 responses"""
    pass


_error_classes = {
    400: BadRequest,
    403: Forbidden,
    404: NotFound,
    502: BadGateway,
    503: ServiceUnavailable,
    504: GatewayTimeout
}


def check_status_code(response):
    """Raises the appropriate exception for a response if it has an abnormal status code"""
    klass = _error_classes.get(response.status_code)
    if klass is None:
        if 400 <= response.status_code < 500:
            klass = ClientError
        if 500 <= response.status_code < 600:
            klass = ServerError
    if klass is not None:
        raise klass(response)


def log_exceptions(func, exceptions=(Exception,)):
    @wraps(func)
    def wrapped(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except exceptions as e:
            return __logs__.exception(e)

    return wrapped
