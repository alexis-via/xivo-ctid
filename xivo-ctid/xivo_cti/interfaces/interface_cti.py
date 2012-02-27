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

import cjson
import logging
import os
import time


from xivo_cti.cti.cti_command_handler import CTICommandHandler
from xivo_cti import cti_command, cti_config
from xivo_cti.interfaces import interfaces
from xivo_cti.cti.commands.login_id import LoginID
import random
from xivo_cti.cti.cti_command_runner import CTICommandRunner

logger = logging.getLogger('interface_cti')

ALLOWED_OS = ['x11', 'win', 'mac', 'ctiserver', 'web', 'android', 'ios']


class serialJson(object):
    def decode(self, linein):
        # Output of the cjson.decode is a Unicode object, even though the
        # non-ASCII characters have not been decoded.
        # Without the .decode('utf-8'), some Unicode character (try asian, not european)
        # will not be interpreted correctly.
        v = cjson.decode(linein.decode('utf-8').replace('\\/', '/'))
        return v

    def encode(self, obj):
        obj['timenow'] = time.time()
        return cjson.encode(obj)


class CTI(interfaces.Interfaces):

    kind = 'CTI'
    sep = '\n'

    def __init__(self, ctiserver):
        interfaces.Interfaces.__init__(self, ctiserver)
        self.connection_details = {}
        self.serial = serialJson()
        self.transferconnection = {}
        self._cti_command_handler = CTICommandHandler(self)
        self._cti_command_runner = CTICommandRunner()
        self.user_service_manager = None
        self._register_login_callbacks()

    def connected(self, connid):
        """
        Send a banner at login time
        """
        interfaces.Interfaces.connected(self, connid)
        self.connid.sendall('XiVO CTI Server Version xx (on %s)\n'
                            % (' '.join(os.uname()[:3])))

    def _register_login_callbacks(self):
        LoginID.register_callback_params(self.receive_login_id, ['userlogin',
                                                                 'company',
                                                                 'cti_connection'])

    def disconnected(self, msg):
        logger.info('disconnected %s', msg)
        self.logintimer.cancel()
        if self.transferconnection and self.transferconnection.get('direction') == 'c2s':
            logger.info('%s got the file ...', self.transferconnection.get('faxobj').fileid)
        try:
            ipbxid = self.connection_details['ipbxid']
            user_id = self.connection_details['userid']
            self._manage_logout(ipbxid, user_id, msg)
        except KeyError:
            logger.warning('Could not retrieve the user user_id %s',
                           self.connection_details)

    def manage_connection(self, msg):
        if self.transferconnection:
            if self.transferconnection.get('direction') == 'c2s':
                faxobj = self.transferconnection.get('faxobj')
                self.logintimer.cancel()
                logger.info('%s transfer connection : %d received', faxobj.fileid, len(msg))
                faxobj.setbuffer(msg)
                faxobj.launchasyncs()
        else:
            multimsg = msg.split(self.sep)
            for usefulmsgpart in multimsg:
                cmd = self.serial.decode(usefulmsgpart)
                return self._run_functions(cmd)
        return []

    def _run_functions(self, decoded_command):
        replies = []

        # Commands from the cti_command.Command class
        command = cti_command.Command(self, decoded_command)
        replies.extend(command.parse())

        # Commands from the CTICommandHandler
        self._cti_command_handler.parse_message(decoded_command)
        replies.extend(self._cti_command_handler.run_commands())

        return [reply for reply in replies if reply]

    def set_as_transfer(self, direction, faxobj):
        logger.info('%s set_as_transfer %s', faxobj.fileid, direction)
        self.transferconnection = {'direction': direction,
                                   'faxobj': faxobj}

    def reply(self, msg):
        if self.transferconnection:
            if self.transferconnection.get('direction') == 's2c':
                self.connid.sendall(msg)
                logger.info('transfer connection %d sent', len(msg))
        else:
            self.connid.sendall(self.serial.encode(msg) + '\n')

    def _manage_logout(self, ipbxid, user_id, msg):
        self._disconnect_user(ipbxid, user_id)

    def loginko(self, errorstring):
        logger.warning('user can not connect (%s) : sending %s',
                       self.details, errorstring)
        # self.logintimer.cancel() + close
        tosend = {'class': 'loginko',
                  'error_string': errorstring}
        return self.serial.encode(tosend)

    def _disconnect_user(self, ipbxid, user_id):
        """
        Change the user's status to disconnected
        """
        try:
            innerdata = self._ctiserver.safe[ipbxid]
            userstatus = innerdata.xod_status['users'][user_id]
            innerdata.handle_cti_stack('set', ('users', 'updatestatus', user_id))
            userstatus['availstate'] = 'disconnected'
            userstatus['connection'] = None
            userstatus['last-logouttimestamp'] = time.time()
            innerdata.handle_cti_stack('empty_stack')
        except KeyError:
            logger.warning('Could not update user status %s', user_id)

    def receive_login_id(self, login, company, connection):
        if connection != self:
            return []

        ipbxid = self._ctiserver.myipbxid
        safe = self._ctiserver.safe[ipbxid]
        userid = safe.user_find(login, company)

        if userid:
            self.connection_details.update({'ipbxid': ipbxid,
                                            'userid': userid})

        session_id = ''.join(random.sample(cti_config.ALPHANUMS, 10))
        self.connection_details['prelogin'] = {'sessionid': session_id}

        return 'message', {'sessionid': session_id,
                           'class': 'login_id'}


class CTIS(CTI):
    kind = 'CTIS'
