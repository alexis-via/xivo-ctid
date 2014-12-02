# -*- coding: utf-8 -*-

# Copyright (C) 2007-2014 Avencall
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

import argparse
import logging
import time
import xivo_cti
from xivo_dao import cti_service_dao, cti_preference_dao, cti_profile_dao, \
    cti_main_dao, cti_displays_dao, cti_context_dao, cti_phonehints_dao, \
    cti_userstatus_dao, cti_sheets_dao, cti_directories_dao

logger = logging.getLogger('cti_config')

default_config = {
    'debug': False,
    'foreground': False,
    'pidfile': '/var/run/%s.pid' % xivo_cti.DAEMONNAME,
    'logfile': '/var/log/%s.log' % xivo_cti.DAEMONNAME,
    'db_uri': 'postgresql://asterisk:proformatique@localhost/asterisk',
    'bus': {
        'exchange_name': 'xivo-cti',
        'exchange_type': 'direct',
        'exchange_durable': True,
        'binding_key': 'call_form_result',
    },
}
cli_config = {}


def init(args):
    global config

    parser = _new_parser()
    parsed_args = parser.parse_args(args)
    _process_parsed_args(parsed_args)
    db_config = _DbConfig()
    db_config.update()
    config = ChainMap(cli_config, db_config.getconfig(), default_config)
    # TODO: read the config file here
    # TODO: add the config file config to the config chainmap


def _new_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', action='store_true')
    parser.add_argument('-f', '--foreground', action='store_true')
    parser.add_argument('-p', '--pidfile')
    parser.add_argument('-l', '--logfile')
    return parser


def _process_parsed_args(parsed_args):
    global cli_config

    if parsed_args.debug:
        cli_config['debug'] = parsed_args.debug
    if parsed_args.foreground:
        cli_config['foreground'] = parsed_args.foreground
    if parsed_args.pidfile:
        cli_config['pidfile'] = parsed_args.pidfile
    if parsed_args.logfile:
        cli_config['logfile'] = parsed_args.logfile


class ChainMap(object):

    def __init__(self, *dicts):
        self._dicts = list(dicts)

    def __getitem__(self, key):
        v = self.get(key)
        if v is None:
            raise KeyError('{key} not found'.format(key=key))

        return v

    def get(self, key, default=None):
        for d in self._dicts:
            if key in d:
                return d[key]

        return default

    def push_at(self, i, d):
        self._dicts.insert(i, d)


xivo_cti.config = ChainMap(cli_config, default_config)


class _DbConfig(object):

    def __init__(self):
        self.xc_json = {}

    def update(self):
        start_time = time.time()
        self.fill_conf()
        logger.info('Config successfully updated in %.6f seconds', (time.time() - start_time))

    def fill_conf(self):
        self.xc_json.update(cti_main_dao.get_config())
        self.xc_json['displays'] = cti_displays_dao.get_config()
        self.xc_json['contexts'] = cti_context_dao.get_config()
        self.xc_json['profiles'] = self._get_profiles()
        self.xc_json['services'] = self._get_services()
        self.xc_json['preferences'] = self._get_preferences()
        self.xc_json['phonestatus'] = cti_phonehints_dao.get_config()
        self.xc_json['userstatus'] = cti_userstatus_dao.get_config()
        self.xc_json['sheets'] = cti_sheets_dao.get_config()
        self.xc_json['directories'] = cti_directories_dao.get_config()

    def _get_profiles(self):
        profiles = cti_profile_dao.get_profiles()
        res = {}
        for profile_key, profile_value in profiles.iteritems():
            new_profile = profile_value
            if 'xlets' in profile_value:
                new_xlet_list = []
                for xlet in profile_value['xlets']:
                    new_xlet = [xlet['name'], xlet['layout']]
                    if xlet['layout'] == 'dock':
                        args = ''
                        args += 'f' if xlet['floating'] else ''
                        args += 'c' if xlet['closable'] else ''
                        args += 'm' if xlet['movable'] else ''
                        args += 's' if xlet['scrollable'] else ''
                        new_xlet.append(args)
                    if xlet['order']:
                        new_xlet.append(str(xlet['order']))
                    new_xlet_list.append(new_xlet)
                    new_profile['xlets'] = new_xlet_list
            res[profile_key] = new_profile
        return res

    def _get_services(self):
        services = cti_service_dao.get_services()
        res = {}
        for service_key, service_value in services.iteritems():
            new_service_key = 'itm_services_%s' % service_key
            new_service_value = [''] if not service_value else service_value
            res[new_service_key] = new_service_value
        return res

    def _get_preferences(self):
        preferences = cti_preference_dao.get_preferences()
        res = {}
        for preference_key, preference_value in preferences.iteritems():
            new_preference_key = 'itm_preferences_%s' % preference_key
            new_preference_value = False if not preference_value else preference_value
            res[new_preference_key] = new_preference_value
        return res

    def getconfig(self, key=None):
        if key:
            ret = self.xc_json.get(key, {})
        else:
            ret = self.xc_json
        return ret
