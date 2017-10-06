# Adapted from http://stackabuse.com/how-to-send-an-email-with-boto-and-ses/
# and https://stackoverflow.com/a/45333231
import os
from textwrap import dedent
from datetime import datetime
from boto import ses
from celery import Task

class DevExceptionEmail(object):
    AWS_REGION = os.getenv('AWS_REGION', '')
    AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID', '')
    AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY', '')
    EXCEPTION_SENDER = os.getenv('EXCEPTION_EMAIL_SENDER', 'sender@localhost')
    EXCEPTION_RECIPIENTS = os.getenv('EXCEPTION_EMAIL_RECIPIENTS', 'recipients@localhost')
    EXCEPTION_SUBJECT = "[Biglearn-SPARFA-Server] A {} exception occurred in Celery task with ID {}"
    EXCEPTION_TEXT = dedent("""
      A {} occurred in Celery task with ID {} at {:%Y-%m-%d %H:%M:%S %Z}

      Message: {}

      Backtrace: {}

      Task Info:
        Args: {}
        Kwargs: {}
    """).strip()

    def __init__(self, exc, task_id, args, kwargs, einfo):
        self.sender = EXCEPTION_SENDER
        self.recipients = EXCEPTION_RECIPIENTS
        self.subject = EXCEPTION_SUBJECT.format(exc.__class__.__name__, task_id)
        self.text = EXCEPTION_TEXT.format(
          exc.__class__.__name__, task_id, datetime.now(), exc, einfo.traceback, args, kwargs
        )

    def send(self):
        connection = boto.ses.connect_to_region(
            AWS_REGION,
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY
        )

        return connection.send_email(
            self.sender,
            self.subject,
            None,
            self.recipients,
            format='text',
            text_body=self.text
        )

class DevExceptionEmailTask(Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        DevExceptionEmail(exc, task_id, args, kwargs, einfo).send()
        super(DevExceptionEmailTask, self).on_failure(exc, task_id, args, kwargs, einfo)
