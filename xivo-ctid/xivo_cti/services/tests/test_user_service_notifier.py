import unittest
from xivo_cti.services.user_service_notifier import UserServiceNotifier

import Queue


class TestUserServiceNotifier(unittest.TestCase):

    def setUp(self):
        self.ipbx_id = 'xivo_test'
        self.notifier = UserServiceNotifier()
        self.notifier.events_cti = Queue.Queue()
        self.notifier.ipbx_id = self.ipbx_id

    def tearDown(self):
        pass

    def test_dnd_enabled(self):
        user_id = 34
        ipbx_id = 'xivo_test'
        notifier = UserServiceNotifier()
        notifier.events_cti = Queue.Queue()
        notifier.ipbx_id = ipbx_id
        expected = {"class": "getlist",
                    "config": {"enablednd": True},
                    "function": "updateconfig",
                    "listname": "users",
                    "tid": user_id,
                    "tipbxid": ipbx_id}

        notifier.dnd_enabled(user_id)

        self.assertTrue(notifier.events_cti.qsize() > 0)
        event = notifier.events_cti.get()
        self.assertEqual(event, expected)

    def test_dnd_disabled(self):
        user_id = 34
        ipbx_id = 'xivo_test'
        notifier = UserServiceNotifier()
        notifier.events_cti = Queue.Queue()
        notifier.ipbx_id = ipbx_id
        expected = {"class": "getlist",
                    "config": {"enablednd": False},
                    "function": "updateconfig",
                    "listname": "users",
                    "tid": user_id,
                    "tipbxid": ipbx_id}

        notifier.dnd_disabled(user_id)

        self.assertTrue(notifier.events_cti.qsize() > 0)
        event = notifier.events_cti.get()
        self.assertEqual(event, expected)

    def test_filter_enabled(self):
        user_id = 32

        expected = {"class": "getlist",
                    "config": {"incallfilter": True},
                    "function": "updateconfig",
                    "listname": "users",
                    "tid": user_id,
                    "tipbxid": self.ipbx_id}

        self.notifier.filter_enabled(user_id)
        self.assertTrue(self.notifier.events_cti.qsize() > 0)
        event = self.notifier.events_cti.get()
        self.assertEqual(event, expected)

    def test_filter_disabled(self):
        user_id = 932

        expected = {"class": "getlist",
                    "config": {"incallfilter": False},
                    "function": "updateconfig",
                    "listname": "users",
                    "tid": user_id,
                    "tipbxid": self.ipbx_id}

        self.notifier.filter_disabled(user_id)
        self.assertTrue(self.notifier.events_cti.qsize() > 0, 'No event in queue for filter disabled')
        event = self.notifier.events_cti.get()
        self.assertEqual(event, expected)

    def test_unconditional_fwd_enabled(self):
        user_id = 456
        destination = '234'
        expected = {"class": "getlist",
                    "config": {"enableunc": True,
                               'destunc': destination},
                    "function": "updateconfig",
                    "listname": "users",
                    "tid": user_id,
                    "tipbxid": self.ipbx_id}

        self.notifier.unconditional_fwd_enabled(user_id, destination)

        self.assertTrue(self.notifier.events_cti.qsize() > 0)
        event = self.notifier.events_cti.get()
        self.assertEqual(event, expected)

    def test_rna_fwd_enabled(self):
        user_id = 456
        destination = '234'
        expected = {"class": "getlist",
                    "config": {"enablerna": True,
                               'destrna': destination},
                    "function": "updateconfig",
                    "listname": "users",
                    "tid": user_id,
                    "tipbxid": self.ipbx_id}

        self.notifier.rna_fwd_enabled(user_id, destination)

        self.assertTrue(self.notifier.events_cti.qsize() > 0)
        event = self.notifier.events_cti.get()
        self.assertEqual(event, expected)

    def test_rna_fwd_disabled(self):
        user_id = 456
        destination = '234'
        expected = {"class": "getlist",
                    "config": {"enablerna": False,
                               'destrna': destination},
                    "function": "updateconfig",
                    "listname": "users",
                    "tid": user_id,
                    "tipbxid": self.ipbx_id}

        self.notifier.rna_fwd_disabled(user_id, destination)

        self.assertTrue(self.notifier.events_cti.qsize() > 0)
        event = self.notifier.events_cti.get()
        self.assertEqual(event, expected)

    def test_busy_fwd_enabled(self):
        user_id = 456
        destination = '234'
        expected = {"class": "getlist",
                    "config": {"enablebusy": True,
                               'destbusy': destination},
                    "function": "updateconfig",
                    "listname": "users",
                    "tid": user_id,
                    "tipbxid": self.ipbx_id}

        self.notifier.busy_fwd_enabled(user_id, destination)

        self.assertTrue(self.notifier.events_cti.qsize() > 0)
        event = self.notifier.events_cti.get()
        self.assertEqual(event, expected)

    def test_busy_fwd_disabled(self):
        user_id = 456
        destination = '234'
        expected = {"class": "getlist",
                    "config": {"enablebusy": False,
                               'destbusy': destination},
                    "function": "updateconfig",
                    "listname": "users",
                    "tid": user_id,
                    "tipbxid": self.ipbx_id}

        self.notifier.busy_fwd_disabled(user_id, destination)

        self.assertTrue(self.notifier.events_cti.qsize() > 0)
        event = self.notifier.events_cti.get()
        self.assertEqual(event, expected)

    def test_prepare_message(self):
        self.notifier._prepare_message('123')
        self.assertEqual(self.notifier.STATUS_MESSAGE['tid'], '')