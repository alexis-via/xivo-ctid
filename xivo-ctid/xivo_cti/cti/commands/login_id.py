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

from xivo_cti.cti.cti_command import CTICommand
from xivo_cti.cti.cti_command_factory import CTICommandFactory


class LoginID(CTICommand):

    COMMAND_CLASS = 'login_id'

    COMPANY = 'company'
    IDENT = 'ident'
    USERLOGIN = 'userlogin'
    SESSIONID = 'sessionid'

    required_fields = [CTICommand.CLASS, USERLOGIN, IDENT, COMPANY]
    conditions = [(CTICommand.CLASS, COMMAND_CLASS)]
    _callbacks = []
    _callbacks_with_params = []

    def __init__(self):
        super(LoginID, self).__init__()
        self.command_class = self.COMMAND_CLASS
        self.company = None
        self.ident = None
        self.userlogin = None

    def _init_from_dict(self, msg):
        super(LoginID, self)._init_from_dict(msg)
        self.company = msg[self.COMPANY]
        self.ident = msg[self.IDENT]
        self.userlogin = msg[self.USERLOGIN]


CTICommandFactory.register_class(LoginID)
