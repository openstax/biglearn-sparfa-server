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
    # see if i can tie in vcr here.
    session.post.return_value = 'this is something, handle me plz'

    return session
