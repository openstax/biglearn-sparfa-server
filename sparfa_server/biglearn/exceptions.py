from json.decoder import JSONDecodeError
from functools import wraps


class BiglearnError(Exception):
    """The base exception class for Biglearn requests."""

    def __init__(self, response):
        super().__init__(response)
        self.response = response
        self.code = response.status_code
        try:
            json = response.json()
        except JSONDecodeError:
            json = {}
        self.msg = json.get('error', response.text)

    @property
    def message(self):
        """The error message returned by the API."""
        return self.msg

    def __str__(self):
        return '{0} {1}'.format(self.code, self.msg)

    def __repr__(self):
        return '<{0} [{1}]>'.format(self.__class__.__name__, str(self))


class ResponseError(BiglearnError):
    """The base exception for errors stemming from Biglearn API or Scheduler responses"""
    pass


class ClientError(ResponseError):
    """Exception class for 4xx responses"""
    pass


class BadRequest(ClientError):
    """Exception class for 400 responses"""
    pass


class Unauthorized(ClientError):
    """Exception class for 401 responses"""
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


class InternalServerError(ServerError):
    """Exception class for 500 responses."""
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


ERROR_CLASSES = {
    400: BadRequest,
    401: Unauthorized,
    403: Forbidden,
    404: NotFound,
    500: InternalServerError,
    502: BadGateway,
    503: ServiceUnavailable,
    504: GatewayTimeout
}


def raise_if_response_is_http_error(response):
    status = response.status_code
    if 400 <= status < 600:
        raise(ERROR_CLASSES.get(status, ClientError if status < 500 else ServerError)(response))
