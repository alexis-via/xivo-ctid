#!/usr/bin/python
# vim: set fileencoding=utf-8 :

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

from tests.mock import Mock
from xivo_cti.dao.userfeaturesdao import UserFeaturesDAO
from xivo_cti.services.user_service_notifier import UserServiceNotifier
from xivo_cti.services.user_service_manager import UserServiceManager
from xivo_cti.funckey.funckey_manager import FunckeyManager
from xivo_cti.dao.phonefunckeydao import PhoneFunckeyDAO
from xivo_cti.services.presence_executor import PresenceExecutor
from xivo_cti.services.user_executor import UserExecutor


class TestUserServiceManager(unittest.TestCase):

    def setUp(self):
        self.user_service_manager = UserServiceManager()
        self.user_features_dao = Mock(UserFeaturesDAO)
        self.phone_funckey_dao = Mock(PhoneFunckeyDAO)
        self.user_service_manager.user_features_dao = self.user_features_dao
        self.user_service_manager.phone_funckey_dao = self.phone_funckey_dao
        self.funckey_manager = Mock(FunckeyManager)
        self.user_service_notifier = Mock(UserServiceNotifier)
        self.user_service_manager.user_service_notifier = self.user_service_notifier
        self.user_service_manager.funckey_manager = self.funckey_manager

    def test_enable_dnd(self):
        user_id = 123

        self.user_service_manager.enable_dnd(user_id)

        self.user_features_dao.enable_dnd.assert_called_once_with(user_id)
        self.user_service_notifier.dnd_enabled.assert_called_once_with(user_id)
        self.funckey_manager.dnd_in_use.assert_called_once_with(user_id, True)

    def test_disable_dnd(self):
        user_id = 241

        self.user_service_manager.disable_dnd(user_id)

        self.user_features_dao.disable_dnd.assert_called_once_with(user_id)
        self.user_service_notifier.dnd_disabled.assert_called_once_with(user_id)
        self.funckey_manager.dnd_in_use.assert_called_once_with(user_id, False)

    def test_set_dnd(self):
        old_enable, self.user_service_manager.enable_dnd = self.user_service_manager.enable_dnd, Mock()
        old_disable, self.user_service_manager.disable_dnd = self.user_service_manager.disable_dnd, Mock()

        user_id = 555

        self.user_service_manager.set_dnd(user_id, True)

        self.user_service_manager.enable_dnd.assert_called_once_with(user_id)

        self.user_service_manager.set_dnd(user_id, False)

        self.user_service_manager.disable_dnd.assert_called_once_with(user_id)

        self.user_service_manager.enable_dnd = old_enable
        self.user_service_manager.disable_dnd = old_disable

    def test_enable_filter(self):
        user_id = 789

        self.user_service_manager.enable_filter(user_id)

        self.user_features_dao.enable_filter.assert_called_once_with(user_id)
        self.user_service_notifier.filter_enabled.assert_called_once_with(user_id)
        self.funckey_manager.call_filter_in_use.assert_called_once_with(user_id, True)

    def test_disable_filter(self):
        user_id = 834

        self.user_service_manager.disable_filter(user_id)

        self.user_features_dao.disable_filter.assert_called_once_with(user_id)
        self.user_service_notifier.filter_disabled.assert_called_once_with(user_id)
        self.funckey_manager.call_filter_in_use.assert_called_once_with(user_id, False)

    def test_enable_unconditional_fwd(self):
        user_id = 543321
        destination = '234'
        self.user_service_manager.phone_funckey_dao.get_dest_unc.return_value = [destination]

        self.user_service_manager.enable_unconditional_fwd(user_id, destination)

        self.user_features_dao.enable_unconditional_fwd.assert_called_once_with(user_id, destination)
        self.user_service_notifier.unconditional_fwd_enabled.assert_called_once_with(user_id, destination)
        self.funckey_manager.unconditional_fwd_in_use.assert_called_once_with(user_id, destination, True)

    def test_disable_unconditional_fwd(self):
        user_id = 543
        destination = '1234'
        fwd_key_dest = '102'
        self.phone_funckey_dao.get_dest_unc.return_value = [fwd_key_dest]

        self.user_service_manager.disable_unconditional_fwd(user_id, destination)

        self.user_features_dao.disable_unconditional_fwd.assert_called_once_with(user_id, destination)
        self.user_service_notifier.unconditional_fwd_disabled.assert_called_once_with(user_id, destination)
        self.funckey_manager.disable_all_unconditional_fwd.assert_called_once_with(user_id)

    def test_enable_rna_fwd(self):
        user_id = 2345
        destination = '3456'
        self.user_service_manager.phone_funckey_dao.get_dest_rna.return_value = [destination]

        self.user_service_manager.enable_rna_fwd(user_id, destination)

        self.user_features_dao.enable_rna_fwd.assert_called_once_with(user_id, destination)
        self.user_service_notifier.rna_fwd_enabled.assert_called_once_with(user_id, destination)
        self.funckey_manager.disable_all_rna_fwd.assert_called_once_with(user_id)
        self.funckey_manager.rna_fwd_in_use.assert_called_once_with(user_id, destination, True)

    def test_disable_rna_fwd(self):
        user_id = 2345
        destination = '3456'
        fwd_key_dest = '987'
        self.phone_funckey_dao.get_dest_rna.return_value = [fwd_key_dest]

        self.user_service_manager.disable_rna_fwd(user_id, destination)

        self.user_features_dao.disable_rna_fwd.assert_called_once_with(user_id, destination)
        self.user_service_notifier.rna_fwd_disabled.assert_called_once_with(user_id, destination)
        self.funckey_manager.disable_all_rna_fwd.assert_called_once_with(user_id)

    def test_enable_busy_fwd(self):
        user_id = 2345
        destination = '3456'
        fwd_key_dest = '3456'
        self.phone_funckey_dao.get_dest_busy.return_value = [fwd_key_dest]

        self.user_service_manager.enable_busy_fwd(user_id, destination)

        self.user_features_dao.enable_busy_fwd.assert_called_once_with(user_id, destination)
        self.user_service_notifier.busy_fwd_enabled.assert_called_once_with(user_id, destination)
        self.funckey_manager.disable_all_busy_fwd.assert_called_once_with(user_id)
        self.funckey_manager.busy_fwd_in_use.assert_called_once_with(user_id, destination, True)

    def test_disable_busy_fwd(self):
        user_id = 2345
        destination = '3456'
        fwd_key_dest = '666'
        self.phone_funckey_dao.get_dest_busy.return_value = [fwd_key_dest]

        self.user_service_manager.disable_busy_fwd(user_id, destination)

        self.user_features_dao.disable_busy_fwd.assert_called_once_with(user_id, destination)
        self.user_service_notifier.busy_fwd_disabled.assert_called_once_with(user_id, destination)
        self.funckey_manager.disable_all_busy_fwd.assert_called_once_with(user_id)

    def test_enable_busy_fwd_not_funckey(self):
        user_id = 2345
        destination = '3456'
        fwd_key_dest = '666'
        self.phone_funckey_dao.get_dest_busy.return_value = [fwd_key_dest]

        self.user_service_manager.enable_busy_fwd(user_id, destination)

        self.user_features_dao.enable_busy_fwd.assert_called_once_with(user_id, destination)
        self.user_service_notifier.busy_fwd_enabled.assert_called_once_with(user_id, destination)

    def test_disconnect(self):
        user_id = 95
        self.user_service_manager.user_features_dao = Mock(UserFeaturesDAO)
        self.user_service_manager.presence_executor = Mock(PresenceExecutor)
        self.user_service_manager.user_executor = Mock(UserExecutor)

        self.user_service_manager.disconnect(user_id)

        self.user_service_manager.user_features_dao.disconnect.assert_called_once_with(user_id)
        self.user_service_manager.presence_executor.disconnect.assert_called_once_with(user_id)
        self.user_service_manager.user_executor.notify_cti.assert_called_once_with(user_id)
