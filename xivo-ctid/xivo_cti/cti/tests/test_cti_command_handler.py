# vim: set fileencoding=utf-8 :
# XiVO CTI Server

# Copyright (C) 2007-2011  Avencall
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

from xivo_cti.cti.cti_command_handler import CTICommandHandler
from xivo_cti.cti.commands.invite_confroom import InviteConfroom
from tests.mock import Mock
from xivo_cti.cti.cti_command import CTICommand
from xivo_cti.ctiserver import CTIServer
from xivo_cti.interfaces.interface_cti import CTI
from xivo_cti.cti.commands.login_id import LoginID


class Test(unittest.TestCase):

    def setUp(self):
        self._msg_1 = {"class": "invite_confroom",
                       "commandid": 737000717,
                       "invitee": "user:pcmdev/3"}
        self._ctiserver = Mock(CTIServer)
        self._cti_connection = CTI(self._ctiserver)

    def tearDown(self):
        pass

    def test_cti_command_handler(self):
        cti_handler = CTICommandHandler(self._cti_connection)

        self.assertTrue(cti_handler is not None)
        self.assertTrue(cti_handler._command_factory is not None)

    def test_parse_message(self):
        cti_handler = CTICommandHandler(self._cti_connection)

        self.assertEqual(len(cti_handler._commands_to_run), 0)

        cti_handler.parse_message(self._msg_1)

        self.assertEqual(len(cti_handler._commands_to_run), 1)
        command = cti_handler._commands_to_run[0]
        self.assertTrue(isinstance(command, InviteConfroom))

    def test_parse_login_id(self):
        cti_handler = CTICommandHandler(self._cti_connection)

        self.assertEqual(len(cti_handler._commands_to_run), 0)

        login_id_msg = {"class": "login_id",
                        "commandid": 1215825599,
                        "company": "default",
                        "git_date": "1326300351",
                        "git_hash": "17484c6",
                        "ident": "X11-LE-28863",
                        "lastlogout-datetime": "2012-01-16T07:43:34",
                        "lastlogout-stopper": "connection_lost",
                        "userlogin": "pascal",
                        "version": "9999",
                        "xivoversion": "1.2"}

        cti_handler.parse_message(login_id_msg)

        self.assertEqual(len(cti_handler._commands_to_run), 1)

        command = cti_handler._commands_to_run[0]

        self.assertTrue(isinstance(command, LoginID))

    def test_run_command(self):
        ret_val = {'message': 'test_return'}
        self.called = False

        def function(command):
            self.called = True
            return ret_val

        function2 = Mock()
        CTICommand.register_callback(function)
        InviteConfroom.register_callback(function2)
        cti_handler = CTICommandHandler(self._cti_connection)
        command = CTICommand.from_dict({'class': 'test_function'})
        cti_handler._commands_to_run.append(command)

        ret = cti_handler.run_commands()

        self.assertTrue(ret_val in ret)
        self.assertTrue(self.called)
        self.assertEqual(len(cti_handler._commands_to_run), 0)