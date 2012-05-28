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

from xivo_cti.dao.alchemy.meetmefeatures import MeetmeFeatures
from xivo_cti.dao.alchemy.staticmeetme import StaticMeetme
from xivo_cti.dao.alchemy import dbconnection

_DB_NAME = 'asterisk'


def _session():
    connection = dbconnection.get_connection(_DB_NAME)
    return connection.get_session()


def get(meetme_id):
    res = _session().query(MeetmeFeatures).filter(MeetmeFeatures.id == int(meetme_id))
    if res.count() == 0:
        raise LookupError
    return res[0]


def find_by_name(meetme_name):
    res = _session().query(MeetmeFeatures).filter(MeetmeFeatures.name == meetme_name)
    if res.count() == 0:
        return ''
    return res[0]


def find_by_confno(meetme_confno):
    res = _session().query(MeetmeFeatures).filter(MeetmeFeatures.confno == meetme_confno)
    if res.count() == 0:
        raise LookupError('No such conference room: %s', meetme_confno)
    return res[0].id

def get_name(meetme_id):
    return get(meetme_id).name

def has_pin(meetme_id):
    meetme = get(meetme_id)
    var_val = _session().query(StaticMeetme.var_val).filter(StaticMeetme.id == meetme.meetmeid)
    try:
        number, pin = var_val[0].var_val.split(',', 1)
    except ValueError:
        return False
    else:
        return len(pin) > 0
