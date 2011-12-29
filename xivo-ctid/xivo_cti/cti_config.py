# XiVO CTI Server
# vim: set fileencoding=utf-8

# Copyright (C) 2007-2011  Avencall
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

import logging
import urllib2
import cjson
import ssl

logger = logging.getLogger('cti_config')


DAEMONNAME = 'xivo-ctid'
ALARM_DIRECTORY = '/var/lib/%s/alarms' % DAEMONNAME
BUFSIZE_LARGE = 262144
DEBUG_MODE = False
LOGFILENAME = '/var/log/%s.log' % DAEMONNAME
PIDFILE = '/var/run/%s.pid' % DAEMONNAME
PORTDELTA = 0
SSLPROTO = ssl.PROTOCOL_TLSv1
XIVOIP = 'localhost'
XIVO_CONF_FILE = 'http://localhost/cti/json.php/private/configuration'
XIVO_CONF_FILE_DEFAULT = 'file:///etc/pf-xivo/xivo-ctid/default_config.json'
XIVO_CONF_OVER = None


class Config(object):

    instance = None

    def __init__(self, * urilist):
        self.urilist = urilist
        self.ipwebs = None
        self.xc_json = {}
        self.overconf = None

    def update(self):
        # the aim of the urilist would be to handle the URI's one after the other
        # when there is a reachability issue (like it can happen in first steps ...)
        self.update_uri(self.urilist[0])

    def set_ipwebs(self, ipwebs):
        self.ipwebs = ipwebs

    def update_uri(self, uri):
        if uri.find('json') < 0:
            return
        if uri.find(':') < 0:
            return

        # web-interface/tpl/www/bloc/cti/general.php
        # web-interface/action/www/cti/web_services/configuration.php

        try:
            response = urllib2.urlopen(uri)
            self.json_config = response.read().replace('\/', '/')
            self.xc_json = cjson.decode(self.json_config)
        except Exception:
            logger.exception('fetch url %s', uri)

        for profile, profdef in self.xc_json.get('profiles', {}).iteritems():
            if profdef['xlets']:
                for xlet_attr in profdef['xlets']:
                    if 'N/A' in xlet_attr:
                        xlet_attr.remove('N/A')
                    # XXX what should be done when 'tabber' is in xlet_attr ?
                    #     this was currently a no-op due to what looked like a
                    #     programming bug
                    if 'tab' in xlet_attr:
                        del xlet_attr[2]
                    if xlet_attr[1] == 'grid':
                        del xlet_attr[2]

        self.translate()

        if self.overconf:
            self.xc_json['ipbxes'] = self.overconf

    def translate(self):
        """
        Translate the config fetched from the remote IP ipwebs
        in order to have the urllist and IPBX connection items pointing also to this IP.
        The remote access(es) should be allowed there, of course.
        """
        if self.ipwebs is None or self.ipwebs == 'localhost':
            return
        for k, v in self.xc_json.get('ipbxes', {}).iteritems():
            for kk, vv in v.get('urllists', {}).iteritems():
                nl = []
                for item in vv:
                    z = item.replace('://localhost/', '://%s/' % self.ipwebs).replace('/private/', '/restricted/')
                    nl.append(z)
                v['urllists'][kk] = nl
            if 'ipbx_connection' in v:
                v.get('ipbx_connection')['ipaddress'] = self.ipwebs
            cdruri = v.get('cdr_db_uri')
            if cdruri:
                v['cdr_db_uri'] = cdruri.replace('@localhost/', '@%s/' % self.ipwebs)

    def getconfig(self, key = None):
        if key:
            ret = self.xc_json.get(key, {})
        else:
            ret = self.xc_json
        return ret

    def set_rcti_special_profile(self):
        self.xc_json['userstatus']['ctiserver'] = { 'onlystate' : { 'allowed' : ['onlystate'] } }
        self.xc_json['profiles']['ctiserver'] = {
            'regcommands' : 'itm_regcommands', # XXX
            'userstatus': 'ctiserver',
            'preferences': None, # XXX
            'name' : 'CTIServer',
            'ipbxcommands' : None,
            'phonestatus': None,
            'agentstatus': None,
            'channelstatus': None,
            'xlets': None,
            'services' : None
            }

    def set_rcti_override_ipbxes(self, overconf):
        self.overconf = overconf

    @classmethod
    def get_instance(cls):
        if not cls.instance:
            cls.instance = cls(XIVO_CONF_FILE, XIVO_CONF_FILE_DEFAULT)
        return cls.instance