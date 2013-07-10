# -*- coding: UTF-8 -*-

# Copyright (C) 2013  Avencall
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

import logging

from xivo_cti import dao
from xivo_cti.dao.agent_dao import AgentNonACDStatus
from xivo_cti.services.call.direction import CallDirection

logger = logging.getLogger(__name__)


class AgentStatusManager(object):

    def __init__(self, agent_availability_computer, scheduler):
        self._agent_availability_computer = agent_availability_computer
        self.scheduler = scheduler

    def agent_logged_in(self, agent_id):
        self._agent_availability_computer.compute(agent_id)

    def agent_logged_out(self, agent_id):
        dao.agent.set_on_wrapup(agent_id, False)
        self._agent_availability_computer.compute(agent_id)

    def device_in_use(self, agent_id, direction):
        if direction == CallDirection.incoming:
            call_status = AgentNonACDStatus.incoming
        else:
            call_status = AgentNonACDStatus.outgoing
        dao.agent.set_on_call_nonacd(agent_id, call_status)
        self._agent_availability_computer.compute(agent_id)

    def device_not_in_use(self, agent_id):
        dao.agent.set_on_call_nonacd(agent_id, AgentNonACDStatus.no_call)
        self._agent_availability_computer.compute(agent_id)

    def acd_call_start(self, agent_id):
        dao.agent.set_on_call_acd(agent_id, True)
        self._agent_availability_computer.compute(agent_id)

    def acd_call_end(self, agent_id):
        dao.agent.set_on_call_acd(agent_id, False)
        self._agent_availability_computer.compute(agent_id)

    def agent_in_wrapup(self, agent_id, wrapup_time):
        dao.agent.set_on_wrapup(agent_id, True)
        self.scheduler.schedule(wrapup_time,
                                self.agent_wrapup_completed,
                                agent_id)

        dao.agent.set_on_call_acd(agent_id, False)
        self._agent_availability_computer.compute(agent_id)

    def agent_wrapup_completed(self, agent_id):
        dao.agent.set_on_wrapup(agent_id, False)
        self._agent_availability_computer.compute(agent_id)

    def agent_paused_all(self, agent_id):
        self._agent_availability_computer.compute(agent_id)

    def agent_unpaused(self, agent_id):
        self._agent_availability_computer.compute(agent_id)
