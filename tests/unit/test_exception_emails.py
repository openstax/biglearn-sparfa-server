from unittest.mock import patch

from celery.exceptions import TimeoutError
from sparfa_server.tasks.calcs import run_matrix_calcs_task
from sparfa_server.tasks.exception_emails import DevExceptionEmail

@patch('boto.ses.connection.SESConnection')
@patch('boto.ses.connect_to_region')
@patch('sparfa_server.api.fetch_matrix_calculations')
def test_exception_emails(fetch, connect, connection):
    fetch.side_effect = TimeoutError()
    connect.return_value = connection

    run_matrix_calcs_task.apply()

    connect.assert_called_once_with(
        DevExceptionEmail.AWS_REGION,
        aws_access_key_id=DevExceptionEmail.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=DevExceptionEmail.AWS_SECRET_ACCESS_KEY
    )

    connection.send_email.assert_called_once()
    send_email_args, send_email_kwargs = connection.send_email.call_args
    assert send_email_args[0] == DevExceptionEmail.EXCEPTION_SENDER
    assert send_email_args[1].startswith(
        '[Biglearn-SPARFA-Server] A TimeoutError occurred in Celery task with ID '
    )
    assert send_email_args[2] is None
    assert send_email_args[3] == DevExceptionEmail.EXCEPTION_RECIPIENTS
    assert send_email_kwargs['format'] == 'text'
    assert send_email_kwargs['text_body'].startswith(
        'A TimeoutError occurred in Celery task with ID '
    )
