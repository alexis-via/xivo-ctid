# -*- coding: UTF-8 -*-

# XiVO CTI Server
# Copyright (C) 2009-2012  Avencall
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# Alternatively, XiVO CTI Server is available under other licenses directly
# contracted with Pro-formatique SARL. See the LICENSE file at top of the
# source tree or delivered in the installable package in which XiVO CTI Server
# is distributed for more details.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import unittest
from datetime import datetime, timedelta
from xivo_dao.alchemy.dbconnection import DBConnection
from xivo_cti.dao.alchemy.base import Base
from xivo_cti.dao.alchemy.cel import CEL
from xivo_cti.dao.celdao import CELDAO
from xivo_cti.dao.helpers.cel_exception import CELException


def _new_datetime_generator(step=timedelta(seconds=1)):
    base_datetime = datetime.now()
    cur_datetime = base_datetime
    while True:
        yield cur_datetime
        cur_datetime = cur_datetime + step


def _new_cel(**kwargs):
    cel_kwargs = {
        'eventtype': '',
        'eventtime': datetime.now(),
        'userdeftype': '',
        'cid_name': u'name1',
        'cid_num': u'num1',
        'cid_ani': '',
        'cid_rdnis': '',
        'cid_dnid': '',
        'exten': u'1',
        'context': 'default',
        'channame': u'SIP/A',
        'appname': '',
        'appdata': '',
        'amaflags': 3,
        'accountcode': '',
        'peeraccount': '',
        'uniqueid': '1',
        'linkedid': '1',
        'userfield': '',
        'peer': '',
    }
    cel_kwargs.update(kwargs)
    return CEL(**cel_kwargs)


class TestCELDAO(unittest.TestCase):
    _URI = 'sqlite:///:memory:'

    def setUp(self):
        self._connection = DBConnection(self._URI)
        self._connection.connect()
        self._session = self._connection.get_session()
        self._celdao = CELDAO(self._session)

        Base.metadata.create_all(self._connection.get_engine(), [CEL.__table__])

        self._datetime_gen = _new_datetime_generator()

    def tearDown(self):
        Base.metadata.drop_all(self._connection.get_engine(), [CEL.__table__])

        self._connection.close()

    def _insert_cels(self, cels):
        for cel in cels:
            self._session.add(cel)
        self._session.commit()

    def test_caller_id_by_unique_id_when_unique_id_is_present(self):
        self._insert_cels([
            _new_cel(eventtype='CHAN_START', cid_name='name1', cid_num='num1',
                     uniqueid='1'),
            _new_cel(eventtype='APP_START', cid_name='name2', cid_num='num2',
                     uniqueid='2'),
        ])

        self.assertEqual('"name2" <num2>', self._celdao.caller_id_by_unique_id('2'))

    def test_caller_id_by_unique_id_when_unique_id_is_missing(self):
        self._insert_cels([
            _new_cel(eventtype='CHAN_START', cid_name='name1', cid_num='num1',
                     uniqueid='1'),
        ])

        self.assertRaises(CELException, self._celdao.caller_id_by_unique_id, '2')

    def test_channel_by_unique_id_when_channel_is_present(self):
        self._insert_cels([
            _new_cel(eventtype='CHAN_START', uniqueid='1', exten=u'100'),
            _new_cel(eventtype='HANGUP', uniqueid='1'),
            _new_cel(eventtype='CHAN_END', uniqueid='1'),
        ])

        channel = self._celdao.channel_by_unique_id('1')
        self.assertEqual(u'100', channel.exten())

    def test_channel_by_unique_id_when_channel_is_missing(self):
        self._insert_cels([
            _new_cel(eventtype='CHAN_START', uniqueid='2'),
            _new_cel(eventtype='HANGUP', uniqueid='2'),
            _new_cel(eventtype='CHAN_END', uniqueid='2'),
        ])

        self.assertRaises(CELException, self._celdao.channel_by_unique_id, '1')

    def test_channels_for_phone_sip(self):
        phone = {'protocol': 'sip',
                 'name': 'abcdef'}
        cels = [
            _new_cel(eventtype='CHAN_START', channame=u'SIP/abcdef-001', uniqueid=u'1', ),
            _new_cel(eventtype='HANGUP', uniqueid='1', linkedid=u'1'),
            _new_cel(eventtype='CHAN_END', uniqueid='1', linkedid=u'1'),
            _new_cel(eventtype='CHAN_START', channame=u'SIP/ghijkl-001', uniqueid=u'2', linkedid=u'2'),
            _new_cel(eventtype='HANGUP', uniqueid='2', linkedid=u'2'),
            _new_cel(eventtype='CHAN_END', uniqueid='2', linkedid=u'2'),
        ]
        self._insert_cels(cels)

        channels = self._celdao.channels_for_phone(phone)

        self.assertEqual(len(channels), 1)
        self.assertEqual(channels[0].linked_id(), u'1')

    def test_channels_for_phone_sccp(self):
        phone = {'protocol': 'sccp',
                 'name': '101'}
        cels = [
            _new_cel(eventtype='CHAN_START', channame=u'sccp/101@SEP001122334455-1', uniqueid=u'1', ),
            _new_cel(eventtype='HANGUP', uniqueid='1', linkedid=u'1'),
            _new_cel(eventtype='CHAN_END', uniqueid='1', linkedid=u'1'),
            _new_cel(eventtype='CHAN_START', channame=u'sccp/102@SEP001122334455-1', uniqueid=u'2', linkedid=u'2'),
            _new_cel(eventtype='HANGUP', uniqueid='2', linkedid=u'2'),
            _new_cel(eventtype='CHAN_END', uniqueid='2', linkedid=u'2'),
        ]
        self._insert_cels(cels)

        channels = self._celdao.channels_for_phone(phone)

        self.assertEqual(len(channels), 1)
        self.assertEqual(channels[0].linked_id(), u'1')
