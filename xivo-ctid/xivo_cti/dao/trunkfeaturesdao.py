#!/usr/bin/python
# vim: set fileencoding=utf-8 :

# Copyright (C) 2012  Avencall
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# Alternatively, XiVO CTI Server is available under other licenses directly
# contracted with Avencall. See the LICENSE file at top of the
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

from xivo_cti.dao.alchemy.usersip import UserSIP
from xivo_cti.dao.alchemy.useriax import UserIAX
from xivo_cti.dao.alchemy.usercustom import UserCustom
from xivo_cti.dao.alchemy.trunkfeatures import TrunkFeatures
from xivo_cti.dao.alchemy import dbconnection

TRUNK_TYPES = ['sip', 'iax', 'custom']


class TrunkFeaturesDAO(object):

    def __init__(self, session):
        self._session = session

    def find_by_proto_name(self, protocol, name):
        if not protocol or protocol not in TRUNK_TYPES:
            raise ValueError('Protocol %s is not allowed', protocol)

        protocol = protocol.lower()
        table, field = self._trunk_table_lookup_field(protocol)

        try:
            protocol_id = (self._session.query(table.id)
                           .filter(field.ilike(name)))[0].id
            trunk_id = (self._session.query(TrunkFeatures.id)
                        .filter(TrunkFeatures.protocolid == protocol_id)
                        .filter(TrunkFeatures.protocol == protocol.lower()))[0].id
        except IndexError:
            raise LookupError('No such trunk')
        else:
            return trunk_id

    def _trunk_table_lookup_field(self, protocol):
        if protocol == 'sip':
            table = UserSIP
            field = UserSIP.name
        elif protocol == 'iax':
            table = UserIAX
            field = UserIAX.name
        elif protocol == 'custom':
            table = UserCustom
            field = UserCustom.interface
        return table, field

    def get_ids(self):
        return [item.id for item in self._session.query(TrunkFeatures.id)]

    @classmethod
    def new_from_uri(cls, uri):
        connection = dbconnection.get_connection(uri)
        return cls(connection.get_session())
