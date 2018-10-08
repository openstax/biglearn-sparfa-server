class BiglearnError(Exception):
    """The base exception class."""

    def __init__(self, resp):
        super(BiglearnError, self).__init__(resp)
        #: Response code that triggered the error
        self.response = resp
        self.code = resp.status_code
        self.errors = []
        try:
            error = resp.json()
            #: List of errors provided by GitHub
            if error.get('errors'):
                self.msg = error.get('errors')
        except:  # Amazon S3 error
            self.msg = resp.content or '[No message]'

    def __repr__(self):
        return '<{0} [{1}]>'.format(self.__class__.__name__,
                                    self.msg or self.code)

    def __str__(self):
        return '{0} {1}'.format(self.code, self.msg)

    @property
    def message(self):
        """The actual message returned by the API."""
        return self.msg


class TransportError(BiglearnError):
    """Catch-all exception for errors coming from Requests."""

    msg_format = 'An error occurred while making a request to Biglearn API: {0}'

    def __init__(self, exception):
        super().__init__(exception)
        self.exception = exception
        self.msg = self.msg_format.format(str(exception))

    def __str__(self):
        return '{0}: {1}'.format(type(self.exception), self.msg)


class ConnectionError(TransportError):
    """Exception for errors in connecting to
    or reading data from Biglearn API"""

    msg_format = 'A connection-level exception occurred: {0}'


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


class NotFoundError(ClientError):
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

# TODO: Add in other HTTP exception classes ex. 403, 406, etc.
error_classes = {
    400: BadRequest,
    403: Forbidden,
    404: NotFoundError,
    502: BadGateway,
    503: ServiceUnavailable,
    504: GatewayTimeout
}


def response_error_for(response):
    """Returns the appropriate initialized exception class for a response"""
    klass = error_classes.get(response.status_code)
    if klass is None:
        if 400 <= response.status_code < 500:
            klass = ClientError
        if 500 <= response.status_code < 600:
            klass = ServerError
    return None if klass is None else klass(response)
