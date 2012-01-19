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

from xivo_cti.cti.commands.getlist import GetList
from xivo_cti.cti.cti_command import CTICommand
from xivo_cti.cti.cti_command_factory import CTICommandFactory


class UpdateConfig(GetList):

    FUNCTION_NAME = 'updateconfig'

    required_fields = [CTICommand.CLASS, GetList.FUNCTION, GetList.LIST_NAME,
                       GetList.ITEM_ID, GetList.IPBX_ID]
    conditions = [(CTICommand.CLASS, GetList.COMMAND_CLASS),
                  (GetList.FUNCTION, FUNCTION_NAME)]
    _callbacks = []

    def __init__(self):
        super(UpdateConfig, self).__init__()
        self.function = self.FUNCTION_NAME

CTICommandFactory.register_class(UpdateConfig)