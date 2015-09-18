from django.test import TestCase
from explorer.tasks import execute_query, snapshot_queries
from explorer.tests.factories import SimpleQueryFactory
from django.core import mail
from mock import Mock, patch
from six.moves import cStringIO


class TestTasks(TestCase):

    @patch('tinys3.Connection')
    def test_async_results(self, mocked_s3):
        conn = Mock()
        conn.upload = Mock()
        conn.upload.return_value = type('obj', (object,), {'url': 'http://s3.com/your-file.csv'})
        mocked_s3.return_value = conn

        q = SimpleQueryFactory(sql='select 1 "a", 2 "b", 3 "c";', title="testquery")
        execute_query(q.id, 'cc@epantry.com')

        output = cStringIO()
        output.write('a,b,c\r\n1,2,3\r\n')

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Report %s is ready' % q.title)
        self.assertEqual(conn.upload.call_args[0][0], '%s.csv' % q.title)
        self.assertEqual(conn.upload.call_args[0][1].getvalue(), output.getvalue())
        self.assertEqual(conn.upload.call_count, 1)

    @patch('tinys3.Connection')
    def test_snapshots(self, mocked_s3):
        conn = Mock()
        conn.upload = Mock()
        conn.upload.return_value = type('obj', (object,), {'url': 'http://s3.com/your-file.csv'})
        mocked_s3.return_value = conn

        SimpleQueryFactory(snapshot=True)
        SimpleQueryFactory(snapshot=True)
        SimpleQueryFactory(snapshot=True)
        SimpleQueryFactory(snapshot=False)

        snapshot_queries()
        self.assertEqual(conn.upload.call_count, 3)