# -*- coding: utf-8 -*-

# Copyright (C) 2007-2013 Avencall
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

import unittest

from hamcrest import *
from mock import Mock
from xivo_cti import dao
from xivo_cti.services.agent.status import AgentStatus
from xivo_cti.services.agent.availability_updater import AgentAvailabilityUpdater
from xivo_cti.services.agent.availability_notifier import AgentAvailabilityNotifier
from xivo_cti.dao.agent_dao import AgentDAO
from xivo_cti.dao.innerdata_dao import InnerdataDAO
from xivo_cti.exception import NoSuchAgentException


class TestAgentAvailabilityUpdater(unittest.TestCase):

    def setUp(self):
        dao.agent = Mock(AgentDAO)
        dao.innerdata = Mock(InnerdataDAO)
        self.agent_availability_updater = AgentAvailabilityUpdater(Mock(AgentAvailabilityNotifier))


    def test_update(self):

        agent_id = 13
        agent_status = AgentStatus.available
        
        self.agent_availability_updater.update(agent_id, agent_status)

        dao.innerdata.set_agent_availability.assert_called_once_with(agent_id, agent_status)
        self.agent_availability_updater.notifier.notify.assert_called_once_with(agent_id)

    def test_update_no_such_agent(self):
        agent_id = 13
        agent_status = AgentStatus.available
        dao.innerdata.set_agent_availability.side_effect = NoSuchAgentException()

        self.assertRaises(NoSuchAgentException, self.agent_availability_updater.update, agent_id, agent_status)
