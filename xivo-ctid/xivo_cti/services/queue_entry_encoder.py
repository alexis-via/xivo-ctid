#!/usr/bin/python
# vim: set fileencoding=utf-8 :

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


class QueueEntryEncoder(object):

    _instance = None

    MSG_TEMPLATE = {'class': 'queueentryupdate',
                    'state': None}

    QUEUE_ENTRY_TEMPLACE = {'position': None,
                            'name': None,
                            'number': None,
                            'join_time': None}

    STATE_TEMPLATE = {'queue_name': None,
                      'queue_id': None,
                      'entries': []}

    def encode(self, queue_name, entries):
        msg = dict(self.MSG_TEMPLATE)
        entry_list = self._build_entry_list(entries)
        msg['state'] = self._build_state(queue_name, entry_list)
        return msg

    def _encode_queue_entry(self, queue_entry):
        result = dict(self.QUEUE_ENTRY_TEMPLACE)

        result['position'] = queue_entry.position
        result['name'] = queue_entry.name
        result['number'] = queue_entry.number
        result['join_time'] = queue_entry.join_time

        return result

    def _build_entry_list(self, queue_entries):
        result = [self._encode_queue_entry(queue_entry)
                  for queue_entry in queue_entries.itervalues()]

        return sorted(result, key=lambda entry: entry['position'])

    def _build_state(self, queue_name, entry_list):
        state = dict(self.STATE_TEMPLATE)

        state['queue_name'] = queue_name
        state['queue_id'] = self.queue_features_dao.id_from_name(queue_name)
        state['entries'] = entry_list

        return state

    @classmethod
    def get_instance(cls):
        if cls._instance == None:
            cls._instance = cls()
        return cls._instance
