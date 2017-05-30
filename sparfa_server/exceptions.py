class APIError(Exception):
    """API Base exception"""
    def __init__(self, resp):
        super().__init__(resp)
        self.response = resp
        self.code = resp.status_code
        self.errors = []
        try:
            error = resp.json()
            self.msg = error.get('message')
            if error.get('errors'):
                self.errors = error.get('errors')
        except:
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


class ResponseError(APIError):
    """The base exception for errors stemming from Biglearn API or Scheduler
    responses
    """
    pass


class TransportError(APIError):
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


class NotFoundError(ResponseError):
    """Exception class for 406 responses"""
    pass


class ClientError(ResponseError):
    """Catch-all for 400 responses that aren't specific errors."""
    pass


class BadRequest(ResponseError):
    """Exception class for 400 responses"""
    pass


class ServerError(ResponseError):
    """Exception class for 5xx responses."""
    pass

# TODO: Add in other HTTP exception classes ex. 403, 406, etc.
error_classes = {
    400: BadRequest,
    404: NotFoundError,
}


def error_for(response):
    """Returns the appropriate initialized exception class for a response"""
    klass = error_classes.get(response.status_code)
    if klass is None:
        if 400 <= response.status_code < 500:
            klass = ClientError
        if 500 <= response.sttatus_code < 600:
            klass = ServerError
    return klass(response)
