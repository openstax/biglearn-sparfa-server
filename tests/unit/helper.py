import json
import unittest

import sparfa_server

try:
    from unittest import mock
except ImportError:
    import mock


from sparfa_server.client.session import BiglearnSession


def create_mocked_session():
    """Use mock to auto-spec a BiglearnSession and return an instance."""
    MockedSession = mock.create_autospec(BiglearnSession)
    return MockedSession()


def create_session_mock(*args):
    """Create a mocked session and add headers."""
    session = create_mocked_session()
    base_attrs = ['headers']
    attrs = dict(
        (key, mock.Mock()) for key in set(args).union(base_attrs)
    )

    session.configure_mock(**attrs)
    session.post.return_value = None
    return session


def build_url(self, *args, **kwargs):
    """A function to proxy to the actual BiglearnSession#build_url method."""
    # We want to assert what is happening with the actual calls to the
    # Internet. We can proxy this.
    return sparfa_server.client.session.BiglearnSession().build_url(*args, **kwargs)


class UnitHelper(unittest.TestCase):

    """Base class for unittests."""

    # Sub-classes must assign the class to this during definition
    described_class = None
    # Sub-classes must also assign a dictionary to this during definition
    example_data = {}

    def create_mocked_session(self):
        """Use mock to auto-spec a BiglearnSession and return an instance."""
        MockedSession = mock.create_autospec(sparfa_server.client.session.BiglearnSession)
        return MockedSession()

    def create_session_mock(self, *args):
        """Create a mocked session and add headers and auth attributes."""
        session = self.create_mocked_session()
        base_attrs = ['headers', 'auth']
        attrs = dict(
            (key, mock.Mock()) for key in set(args).union(base_attrs)
        )
        session.configure_mock(**attrs)
        session.post.return_value = None
        return session

    def create_instance_of_described_class(self):
        """
        Use cls.example_data to create an instance of the described class.

        If cls.example_data is None, just create a simple instance of the
        class.
        """
        if self.example_data and self.session:
            instance = self.described_class(self.example_data,
                                            self.session)
        elif self.example_data and not self.session:
            instance = self.described_class(self.example_data)

        else:
            instance = self.described_class()
            instance.session = self.session

        return instance

    def delete_called_with(self, *args, **kwargs):
        """Use to assert delete was called with JSON."""
        self.method_called_with('delete', args, kwargs)

    def method_called_with(self, method_name, args, kwargs):
        """Assert that a method was called on a session with JSON."""
        mock_method = getattr(self.session, method_name)
        assert mock_method.called is True
        call_args, call_kwargs = mock_method.call_args

        # Data passed to assertion
        data = kwargs.pop('data', None)
        # Data passed to patch
        call_data = call_kwargs.pop('data', None)
        # Data passed by the call to post positionally
        #                                URL, 'json string'
        if call_data is None:
            call_args, call_data = call_args[:1], call_args[1]
        # If data is a dictionary (or list) and call_data exists
        if not isinstance(data, str) and call_data:
            call_data = json.loads(call_data)

        assert args == call_args
        assert data == call_data
        assert kwargs == call_kwargs

    def patch_called_with(self, *args, **kwargs):
        """Use to assert patch was called with JSON."""
        self.method_called_with('patch', args, kwargs)

    def post_called_with(self, *args, **kwargs):
        """Use to assert post was called with JSON."""
        assert self.session.post.called is True
        call_args, call_kwargs = self.session.post.call_args

        # Data passed to assertion
        data = kwargs.pop('data', None)
        # Data passed by the call to post positionally
        #                                URL, 'json string'
        call_args, call_data = call_args[:1], call_args[1]
        # If data is a dictionary (or list) and call_data exists
        if not isinstance(data, str) and call_data:
            call_data = json.loads(call_data)

        assert data == call_data
        assert kwargs == call_kwargs


    def put_called_with(self, *args, **kwargs):
        """Use to assert put was called with JSON."""
        self.method_called_with('put', args, kwargs)

    def setUp(self):
        """Use to set up attributes on self before each test."""
        self.session = self.create_session_mock()
        self.instance = self.create_instance_of_described_class()
        # Proxy the build_url method to the class so it can build the URL and
        # we can assert things about the call that will be attempted to the
        # internet
        self.described_class._build_url = build_url
        self.after_setup()

    def after_setup(self):
        """No-op method to avoid people having to override setUp."""
        pass

