# vim: set fileencoding=utf-8 :
# XiVO CTI Server

# Copyright (C) 2007-2012  Avencall
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


from xivo_cti.dao.alchemy.queuemember import QueueMember
from xivo_cti.dao.alchemy import dbconnection
from xivo_cti.dao.helpers.queuemember_formatter import QueueMemberFormatter


class QueueMemberDAO(object):

    def __init__(self, session):
        self._session = session

    def get_queuemembers(self):
        query_result = self._session.query(QueueMember)
        formatted_result = QueueMemberFormatter.format_queuemembers(query_result)
        return formatted_result

    @classmethod
    def new_from_uri(cls, uri):
        connection = dbconnection.get_connection(uri)
        return cls(connection.get_session())