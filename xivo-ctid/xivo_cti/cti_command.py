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

import logging
import random
import string
import threading
import time
from xivo_cti import cti_fax
from xivo_cti import cti_config
from xivo_cti.statistics.queuestatisticmanager import QueueStatisticManager
from xivo_cti.statistics.queuestatisticencoder import QueueStatisticEncoder

logger = logging.getLogger('cti_command')

REQUIRED_LOGIN_FIELD = ['company', 'userlogin', 'ident',
                       'xivoversion', 'git_hash', 'git_date']

LOGINCOMMANDS = [
    'login_pass', 'login_capas'
    ]

REGCOMMANDS = [
    'logout',

    'getipbxlist',
    'keepalive',

    'history',
    'faxsend',
    'filetransfer',
    'chitchat',

    'logfromclient',
    'getqueuesstats',
    'sheet',
    'actionfiche',

    'ipbxcommand'
    ]

IPBXCOMMANDS = [
    # originate-like commands
    'dial', 'originate',
    # transfer-like commands
    'intercept', 'parking',
    'transfer', 'atxfer',
    # hangup-like commands
    'hangup',

    'sipnotify',
    'mailboxcount',
    'meetme',
    'record',
    'listen',

    'agentlogout',
    'queueadd', 'queueremove',
    'queuepause', 'queueunpause',
    'queueremove_all',
    'queuepause_all', 'queueunpause_all',
    ]

XIVOVERSION_NUM = '1.2'
XIVOVERSION_NAME = 'skaro'
ALPHANUMS = string.uppercase + string.lowercase + string.digits


class Command(object):
    def __init__(self, connection, thiscommand):
        self._config = cti_config.Config.get_instance()
        self._connection = connection
        self._ctiserver = self._connection._ctiserver
        self._commanddict = thiscommand
        self._othermessages = list()
        self._queue_statistic_manager = QueueStatisticManager()
        self._queue_statistic_encoder = QueueStatisticEncoder()

    def parse(self):
        self.command = self._commanddict.get('class')
        self.commandid = self._commanddict.get('commandid')

        self.ipbxid = self._connection.connection_details.get('ipbxid')
        self.userid = self._connection.connection_details.get('userid')
        self.innerdata = self._ctiserver.safe.get(self.ipbxid)

        # identifiers for the requester
        self.ripbxid = self._commanddict.get('ipbxid', self.ipbxid)
        self.ruserid = self._commanddict.get('userid', self.userid)
        self.rinnerdata = self._ctiserver.safe.get(self.ripbxid)

        # identifiers for the requested
        self.tipbxid = self._commanddict.get('tipbxid', self.ipbxid)
        self.tinnerdata = self._ctiserver.safe.get(self.tipbxid)

        messagebase = {'class': self.command}
        if self.commandid:
            messagebase['replyid'] = self.commandid

        if self.command in REGCOMMANDS and not self._connection.connection_details.get('logged'):
            messagebase['error_string'] = 'notloggedyet'

        elif self.command in LOGINCOMMANDS or self.command in REGCOMMANDS:
            if self.ripbxid:
                regcommands = self.rinnerdata.get_user_permissions('regcommands', self.ruserid)
                if regcommands:
                    if self.command not in regcommands:
                        logger.warning('user %s/%s : unallowed command %s',
                                       self.ripbxid, self.ruserid, self.command)
                        messagebase['warning_string'] = 'unallowed'
                else:
                    logger.warning('user %s/%s : unallowed command %s - empty regcommands',
                                   self.ripbxid, self.ruserid, self.command)
                    messagebase['warning_string'] = 'no_regcommands'

            methodname = 'regcommand_%s' % self.command
            if hasattr(self, methodname) and 'warning_string' not in messagebase:
                try:
                    ztmp = getattr(self, methodname)()
                    if ztmp is None or len(ztmp) == 0:
                        messagebase['warning_string'] = 'return_is_none'
                    elif isinstance(ztmp, str):
                        messagebase['error_string'] = ztmp
                    else:
                        messagebase.update(ztmp)
                except Exception:
                    logger.exception('Exception')
                    messagebase['warning_string'] = 'exception'
            else:
                messagebase['warning_string'] = 'unimplemented'
        else:
            return []

        ackmessage = {'message': messagebase}
        if 'error_string' in messagebase:
            ackmessage['closemenow'] = True

        z = [ackmessage]
        for extramessage in self._othermessages:
            bmsg = extramessage.get('message')
            bmsg['class'] = self.command
            z.append({'dest': extramessage.get('dest'),
                      'message': bmsg})
        return z

    def regcommand_login_pass(self):
        head = 'LOGINFAIL - login_pass'
        # user authentication
        missings = []
        for argum in ['hashedpassword']:
            if argum not in self._commanddict:
                missings.append(argum)
        if len(missings) > 0:
            logger.warning('%s - missing args : %s', head, missings)
            return 'missing:%s' % ','.join(missings)

        this_hashed_password = self._commanddict.get('hashedpassword')
        cdetails = self._connection.connection_details

        ipbxid = cdetails.get('ipbxid')
        userid = cdetails.get('userid')
        sessionid = cdetails.get('prelogin').get('sessionid')

        if ipbxid and userid:
            ref_hashed_password = self._ctiserver.safe[ipbxid].user_get_hashed_password(userid, sessionid)
            if ref_hashed_password != this_hashed_password:
                logger.warning('%s - wrong hashed password', head)
                return 'login_password'
        else:
            logger.warning('%s - undefined user : probably the login_id step failed', head)
            return 'login_password'

        reply = {'capalist': [self._ctiserver.safe[ipbxid].user_get_ctiprofile(userid)]}
        return reply

    def regcommand_login_capas(self):
        head = 'LOGINFAIL - login_capas'
        missings = []
        for argum in ['state', 'capaid', 'lastconnwins', 'loginkind']:
            if argum not in self._commanddict:
                missings.append(argum)
        if len(missings) > 0:
            logger.warning('%s - missing args : %s', head, missings)
            return 'missing:%s' % ','.join(missings)

        # settings (in agent mode for instance)
        # userinfo['agent']['phonenum'] = phonenum
        cdetails = self._connection.connection_details

        state = self._commanddict.get('state')
        capaid = self._commanddict.get('capaid')

        iserr = self.__check_capa_connection__(capaid)
        if iserr is not None:
            logger.warning('%s - wrong capaid : %s %s', head, iserr, capaid)
            return iserr

        iserr = self.__check_user_connection__()
        if iserr is not None:
            logger.warning('%s - user connection : %s', head, iserr)
            return iserr

        self.__connect_user__(state, capaid)
        head = 'LOGIN SUCCESSFUL'
        logger.info('%s for %s', head, cdetails)

        if self.userid.startswith('cs:'):
            notifyremotelogin = threading.Timer(2, self._ctiserver.cb_timer,
                                                ({'action': 'xivoremote',
                                                  'properties': None}))
            notifyremotelogin.setName('Thread-xivo-%s' % self.userid)
            notifyremotelogin.start()

        profileclient = self.innerdata.xod_config['users'].keeplist[self.userid].get('profileclient')
        profilespecs = self._config.getconfig('profiles').get(profileclient)

        capastruct = {}
        summarycapas = {}
        if profilespecs:
            for capakind in ['regcommands', 'ipbxcommands',
                             'services', 'preferences',
                             'userstatus', 'phonestatus', 'channelstatus']:
                if profilespecs.get(capakind):
                    tt = profilespecs.get(capakind)
                    cfg_capakind = self._config.getconfig(capakind)
                    if cfg_capakind:
                        details = cfg_capakind.get(tt)
                    else:
                        details = {}
                    capastruct[capakind] = details
                    if details:
                        summarycapas[capakind] = tt
                else:
                    capastruct[capakind] = {}

        reply = {'ipbxid': self.ipbxid,
                 'userid': self.userid,
                 'appliname': profilespecs.get('name'),
                 'capaxlets': profilespecs.get('xlets'),
                 'capas': capastruct,
                 'presence': 'available'}

        self._connection.connection_details['logged'] = True
        self._connection.logintimer.cancel()
        return reply

    def regcommand_logout(self):
        reply = {}
##                        stopper = icommand.struct.get('stopper')
        return reply

## "capaxlets": ["customerinfo-dock-fcms", "dial-dock-fcms", "queues-dock-fcms"],
##  "presencecounter": {"connected": 1},

    def __check_user_connection__(self):
        return

    def __check_capa_connection__(self, capaid):
        cdetails = self._connection.connection_details
        ipbxid = cdetails.get('ipbxid')
        userid = cdetails.get('userid')
        if capaid not in self._config.getconfig('profiles').keys():
            return 'unknownprofile'
        if capaid != self._ctiserver.safe[ipbxid].xod_config['users'].keeplist[userid]['profileclient']:
            return 'wrongprofile'
        # XXX : too much users ?

    def __connect_user__(self, availstate, c):
        cdetails = self._connection.connection_details
        ipbxid = cdetails.get('ipbxid')
        userid = cdetails.get('userid')
        self._ctiserver.safe[ipbxid].xod_status['users'][userid]['connection'] = 'yes'
        self._ctiserver.safe[ipbxid].update_presence(userid, availstate)

    def __disconnect_user__(self):
        cdetails = self._connection.connection_details
        ipbxid = cdetails.get('ipbxid')
        userid = cdetails.get('userid')
        self._ctiserver.safe[ipbxid].xod_status['users'][userid]['connection'] = None
        availstate = self._commanddict.get('availstate')
        # disconnected vs. invisible vs. recordstatus ?
        self._ctiserver.safe[ipbxid].update_presence(userid, availstate)

    # end of login/logout related commands

    def regcommand_chitchat(self):
        reply = {}
        chitchattext = self._commanddict.get('text')
        self._othermessages.append({'dest': self._commanddict.get('to'),
                                   'message': {'to': self._commanddict.get('to'),
                                               'from': '%s/%s' % (self.ripbxid, self.ruserid),
                                                'text': chitchattext}})
        return reply

    def regcommand_actionfiche(self):
        reply = {}
        infos = self._commanddict.get('infos')
        uri = self._config.getconfig('ipbxes').get(self.ripbxid).get('cdr_db_uri')
        self.rinnerdata.fill_user_ctilog(uri,
                                         self.ruserid,
                                         'cticommand:actionfiche',
                                         infos.get('buttonname'))
        logger.info('Received from client : %s' % infos.get('variables'))
        return reply

    def regcommand_history(self):
        phone = self._get_phone_from_user_id(self.ruserid, self.rinnerdata)
        if phone is None:
            reply = self._format_history_reply(None)
        else:
            history = self._get_history_for_phone(phone)
            reply = self._format_history_reply(history)
        return reply

    def _get_phone_from_user_id(self, user_id, innerdata):
        for phone in innerdata.xod_config['phones'].keeplist.itervalues():
            if str(phone['iduserfeatures']) == user_id:
                return phone
        return None

    def _get_history_for_phone(self, phone):
        mode = int(self._commanddict['mode'])
        limit = int(self._commanddict['size'])
        endpoint = self._get_endpoint_from_phone(phone)
        if mode == 0:
            return self._get_outgoing_history_for_endpoint(endpoint, limit)
        elif mode == 1:
            return self._get_answered_history_for_endpoint(endpoint, limit)
        elif mode == 2:
            return self._get_missed_history_for_endpoint(endpoint, limit)
        else:
            return None

    def _get_outgoing_history_for_endpoint(self, endpoint, limit):
        call_history_mgr = self.rinnerdata.call_history_mgr
        result = []
        for sent_call in call_history_mgr.outgoing_calls_for_endpoint(endpoint, limit):
            result.append({'calldate': sent_call.date.isoformat(),
                           'duration': sent_call.duration,
                           # XXX this is not fullname, this is just an extension number like in 1.1
                           'fullname': sent_call.extension})
        return result

    def _get_answered_history_for_endpoint(self, endpoint, limit):
        call_history_mgr = self.rinnerdata.call_history_mgr
        result = []
        for received_call in call_history_mgr.answered_calls_for_endpoint(endpoint, limit):
            result.append({'calldate': received_call.date.isoformat(),
                           'duration': received_call.duration,
                           'fullname': received_call.caller_name})
        return result

    def _get_missed_history_for_endpoint(self, endpoint, limit):
        call_history_mgr = self.rinnerdata.call_history_mgr
        result = []
        for received_call in call_history_mgr.missed_calls_for_endpoint(endpoint, limit):
            result.append({'calldate': received_call.date.isoformat(),
                           'duration': received_call.duration,
                           'fullname': received_call.caller_name})
        return result

    def _get_endpoint_from_phone(self, phone):
        return "%s/%s" % (phone['protocol'].upper(), phone['name'])

    def _format_history_reply(self, history):
        if history is None:
            return {}
        else:
            mode = int(self._commanddict['mode'])
            return {'mode': mode, 'history': history}

    def regcommand_parking(self):
        reply = {}
        for ipbxid, pcalls in self.parkedcalls.iteritems():
            for parkingbay, pprops in pcalls.iteritems():
                tosend = {'class': 'parkcall',
                          'eventkind': 'parkedcall',
                          'ipbxid': ipbxid,
                          'parkingbay': parkingbay,
                          'payload': pprops}
                repstr = self.__cjson_encode__(tosend)
        return reply

    def regcommand_logfromclient(self):
        logger.warning('logfromclient from user %s (level %s) : %s : %s',
                         self.ruserid,
                         self._commanddict.get('level'),
                         self._commanddict.get('classmethod'),
                         self._commanddict.get('message'))

    def regcommand_getqueuesstats(self):
        if 'on' not in self._commanddict:
            return {}
        statistic_results = {}
        for queue_id, params in self._commanddict['on'].iteritems():
            queue_name = self.innerdata.xod_config['queues'].keeplist[queue_id]['name']
            statistic_results[queue_id] = self._queue_statistic_manager.get_statistics(queue_name,
                                                                                        int(params['xqos']),
                                                                                        int(params['window']))
        return self._queue_statistic_encoder.encode(statistic_results)

    def regcommand_filetransfer(self):
        reply = {}
        function = self._commanddict.get('command')
        socketref = self._commanddict.get('socketref')
        fileid = self._commanddict.get('fileid')
        if fileid:
            self.rinnerdata.faxes[fileid].setsocketref(socketref)
            self.rinnerdata.faxes[fileid].setfileparameters(self._commanddict.get('file_size'))
            if function == 'get_announce':
                self._ctiserver.set_transfer_socket(self.rinnerdata.faxes[fileid], 's2c')
            elif function == 'put_announce':
                self._ctiserver.set_transfer_socket(self.rinnerdata.faxes[fileid], 'c2s')
        else:
            logger.warning('empty fileid given %s', self._commanddict)
        return reply

    def regcommand_faxsend(self):
        fileid = ''.join(random.sample(ALPHANUMS, 10))
        reply = {'fileid': fileid}
        self.rinnerdata.faxes[fileid] = cti_fax.Fax(self.rinnerdata, fileid)
        # ruserid gives an entity, which doesn't give a context right away ...
        context = 'default'
        self.rinnerdata.faxes[fileid].setfaxparameters(self.ruserid,
                                                       context,
                                                       self._commanddict.get('destination'),
                                                       self._commanddict.get('hide'))
        self.rinnerdata.faxes[fileid].setrequester(self._connection)
        return reply

    def regcommand_getipbxlist(self):
        return {'ipbxlist': self._config.getconfig('ipbxes').keys()}

    def regcommand_ipbxcommand(self):
        reply = {}
        self.ipbxcommand = self._commanddict.get('command')
        if not self.ipbxcommand:
            return reply
        reply['command'] = self.ipbxcommand
        if self.ipbxcommand not in IPBXCOMMANDS:
            return None
        profileclient = self.rinnerdata.xod_config['users'].keeplist[self.ruserid].get('profileclient')
        profilespecs = self._config.getconfig('profiles').get(profileclient)
        ipbxcommands_id = profilespecs.get('ipbxcommands')
        ipbxcommands = self._config.getconfig('ipbxcommands').get(ipbxcommands_id)
        if self.ipbxcommand not in ipbxcommands:
            logger.warning('profile %s : unallowed ipbxcommand %s (intermediate %s)',
                           profileclient, self.ipbxcommand, ipbxcommands_id)
            return reply

        methodname = 'ipbxcommand_%s' % self.ipbxcommand

        # check whether ipbxcommand is in the users's profile capabilities
        zs = []
        if hasattr(self, methodname):
            try:
                zs = getattr(self, methodname)()
            except Exception:
                logger.exception('exception when calling %s %s', methodname, self._commanddict)

        # if some actions have been requested ...
        if self.commandid:  # pass the commandid on the actionid # 'user action - forwarded'
            baseactionid = 'uaf:%s' % self.commandid
        else:  # 'user action - auto'
            baseactionid = 'uaa:%s' % ''.join(random.sample(ALPHANUMS, 10))
        ipbxreply = 'noaction'
        idz = 0
        for z in zs:
            if 'amicommand' in z:
                params = {'mode': 'useraction',
                          'request': {'requester': self._connection,
                                      'ipbxcommand': self.ipbxcommand,
                                      'commandid': self.commandid},
                          'amicommand': z.get('amicommand'),
                          'amiargs': z.get('amiargs')}
                actionid = '%s-%03d' % (baseactionid, idz)
                ipbxreply = self._ctiserver.myami.get(self.ipbxid).execute_and_track(actionid, params)
            else:
                ipbxreply = z.get('error')
            idz += 1

        reply['ipbxreply'] = ipbxreply
        return reply

    # "any number" :
    # - an explicit number
    # - a phone line given by line:xivo/45
    # - a user given by user:xivo/45 : attempted line will be the first one

    # dial : the requester dials "any number" (originate with source = me)
    # originate : the source will call destination

    # intercept
    # transfer
    # atxfer
    # park

    # hangup : any channel is hanged up

    # for transfers, hangups, ...

    def ipbxcommand_dial(self):
        self._commanddict['source'] = 'user:%s/%s' % (self.ripbxid, self.ruserid)
        reply = self.ipbxcommand_originate()
        return reply

    def parseid(self, item):
        id_as_obj = {}
        try:
            [typev, who] = item.split(':', 1)
            [ipbxid, idv] = who.split('/', 1)
            id_as_obj = {'type': typev,
                         'ipbxid': ipbxid,
                         'id': idv}
        except Exception:
            pass
        return id_as_obj

    # origination
    def ipbxcommand_originate(self):
        src = self.parseid(self._commanddict.get('source'))
        if not src:
            return [{'error': 'source'}]
        dst = self.parseid(self._commanddict.get('destination'))
        if not dst:
            return [{'error': 'destination'}]

        if src.get('ipbxid') != dst.get('ipbxid'):
            return [{'error': 'ipbxids'}]
        if src.get('ipbxid') not in self._ctiserver.safe:
            return [{'error': 'ipbxid'}]

        innerdata = self._ctiserver.safe.get(src.get('ipbxid'))

        orig_protocol = None
        orig_name = None
        orig_number = None
        orig_context = None
        phoneidstruct_src = {}
        phoneidstruct_dst = {}

        if src.get('type') == 'user':
            if src.get('id') in innerdata.xod_config.get('users').keeplist:
                for k, v in innerdata.xod_config.get('phones').keeplist.iteritems():
                    if src.get('id') == str(v.get('iduserfeatures')):
                        phoneidstruct_src = innerdata.xod_config.get('phones').keeplist.get(k)
                        break
                # if not phoneidstruct_src: lookup over agents ?
        elif src.get('type') == 'phone':
            if src.get('id') in innerdata.xod_config.get('phones').keeplist:
                phoneidstruct_src = innerdata.xod_config.get('phones').keeplist.get(src.get('id'))
        elif src.get('type') == 'exten':
            # in android cases
            # there was a warning back to revision 6095 - maybe to avoid making arbitrary calls on behalf
            # of the local telephony system ?
            orig_context = 'mamaop'  # XXX how should we define or guess the proper context here ?
            orig_protocol = 'local'
            orig_name = '%s@%s' % (src.get('id'), orig_context)  # this is the number actually dialed, in local channel mode
            orig_number = src.get('id')  # this is the number that will be displayed as ~ callerid
            orig_identity = ''  # how would we know the identity there ?

        if phoneidstruct_src:
            orig_protocol = phoneidstruct_src.get('protocol')
            orig_name = phoneidstruct_src.get('name')
            orig_number = phoneidstruct_src.get('number')
            orig_identity = phoneidstruct_src.get('useridentity')
            orig_context = phoneidstruct_src.get('context')

        extentodial = None
        dst_identity = None

        if dst.get('type') == 'user':
            if dst.get('id') in innerdata.xod_config.get('users').keeplist:
                for k, v in innerdata.xod_config.get('phones').keeplist.iteritems():
                    if dst.get('id') == str(v.get('iduserfeatures')):
                        phoneidstruct_dst = innerdata.xod_config.get('phones').keeplist.get(k)
                        break
                # if not phoneidstruct_dst: lookup over agents ?
        elif dst.get('type') == 'phone':
            if dst.get('id') in innerdata.xod_config.get('phones').keeplist:
                phoneidstruct_dst = innerdata.xod_config.get('phones').keeplist.get(dst.get('id'))
        elif dst.get('type') == 'voicemail':
            try:
                vmusermsg = innerdata.extenfeatures['extenfeatures']['vmusermsg']
                vm = innerdata.xod_config['voicemails'].keeplist[dst['id']]
                if not vmusermsg['commented']:
                    extentodial = vmusermsg['exten']
                    dst_context = vm['context']
                    dst_identity = 'Voicemail'
                else:
                    extentodial = None
            except KeyError:
                logger.exception('Missing info to call this voicemail')
                extentodial = None
            # XXX especially for the 'dial' command, actually
            # XXX display password on phone in order for the user to know what to type
        elif dst.get('type') == 'meetme':
            if dst.get('id') in innerdata.xod_config.get('meetmes').keeplist:
                meetmestruct = innerdata.xod_config.get('meetmes').keeplist.get(dst.get('id'))
                extentodial = meetmestruct.get('confno')
                dst_identity = 'meetme %s' % meetmestruct.get('name')
                dst_context = meetmestruct.get('context')
            else:
                extentodial = None
        elif dst.get('type') == 'exten':
            extentodial = dst.get('id')
            dst_identity = extentodial
            dst_context = orig_context

        if phoneidstruct_dst:
            extentodial = phoneidstruct_dst.get('number')
            dst_identity = phoneidstruct_dst.get('useridentity')
            dst_context = phoneidstruct_dst.get('context')

        rep = {}
        if orig_protocol and orig_name and orig_number and extentodial:
            rep = {'amicommand': 'originate',
                   'amiargs': (orig_protocol,
                               orig_name,
                               orig_number,
                               orig_identity,
                               extentodial,
                               dst_identity,
                               dst_context)}
        return [rep]

    def ipbxcommand_meetme(self):
        function = self._commanddict['function']
        args = self._commanddict['functionargs']

        if function in ('record',) and len(args) >= 4:
            mxid, usernum, adminnum, status = args[:4]
        elif (function in ('MeetmeMute', 'MeetmeUnmute')
              and len(args) >= 2):
            mxid, usernum = args[:2]
        elif (len(args) >= 3 and function in
              ('MeetmeAccept', 'MeetmeKick', 'MeetmeTalk')):
            mxid, usernum, adminnum = args[:3]
        mid = mxid.split("/", 1)[1]

        meetme_conf = self.innerdata.xod_config['meetmes'].keeplist[mid]
        meetme_status = self.innerdata.xod_status['meetmes'][mid]

        if 'record' in function and status in ('start', 'stop'):
            chan = ''
            for key, value in meetme_status.iteritems():
                if value['usernum'] == usernum:
                    chan = key
            if status == 'start' and chan:
                datestring = time.strftime('%Y%m%d-%H%M%S', time.localtime())
                filename = ('cti-meetme-%s-%s' %
                            (meetme_conf['name'], datestring))
                return [{'amicommand': 'monitor',
                          'amiargs': (chan, filename)}]
            elif status == 'stop':
                return [{'amicommand': 'stopmonitor',
                          'amiargs': (chan,)}]
        elif function in ('MeetmePause',):
            return [{'amicommand': function.lower(),
                      'amiargs': (meetme_conf['confno'], status)}]
        elif function in ('MeetmeKick', 'MeetmeAccept', 'MeetmeTalk'):
            return [{'amicommand': 'meetmemoderation',
                      'amiargs': (function, meetme_conf['confno'],
                                    usernum, adminnum)}]
        elif function in ['MeetmeMute', 'MeetmeUnmute']:
            return [{'amicommand': function.lower(),
                     'amiargs': (meetme_conf['confno'], usernum)}]

    def ipbxcommand_sipnotify(self):
        if 'variables' in self._commanddict:
            variables = self._commanddict.get('variables')
        channel = self._commanddict.get('channel')
        if channel == 'user:special:me':
            uinfo = self.rinnerdata.xod_config['users'].keeplist[self.userid]
            # TODO: Choose the appropriate line if more than one
            line = self.rinnerdata.xod_config['phones'].keeplist[uinfo['linelist'][0]]
            channel = line['identity'].replace('\\', '')
        reply = {'amicommand': 'sipnotify', 'amiargs': (channel, variables)}
        return [reply]

    def ipbxcommand_mailboxcount(self):
        """
        Send a MailboxCount ami command
        """
        if 'mailbox' in self._commanddict:
            return [{'amicommand': 'mailboxcount',
                      'amiargs': (self._commanddict['mailbox'],
                                    self._commanddict['context'])}]

    # transfers
    def ipbxcommand_parking(self):
        src = self.parseid(self._commanddict.get('source'))
        if not src:
            return [{'error': 'source'}]
        dst = self.parseid(self._commanddict.get('destination'))
        if not dst:
            return {'error': 'destination'}

        if src.get('ipbxid') != dst.get('ipbxid'):
            return {'error': 'ipbxids'}
        if src.get('ipbxid') not in self._ctiserver.safe:
            return {'error': 'ipbxid'}

        innerdata = self._ctiserver.safe.get(src.get('ipbxid'))

        if src.get('type') == 'chan':
            if src.get('id') in innerdata.channels:
                channel = src.get('id')
                peerchannel = innerdata.channels.get(channel).peerchannel
        else:
            pass

        if dst.get('type') == 'parking':
            try:
                parkinglot = innerdata.xod_config['parkinglots'].keeplist[dst['id']]['name']
                if parkinglot is not 'default':
                    parkinglot = 'parkinglot_' + parkinglot
            except Exception:
                parkinglot = 'default'

        rep = {'amicommand': 'park',
               'amiargs': (channel, peerchannel, parkinglot, 120000)}
        return [rep, ]

    def ipbxcommand_transfer(self):
        try:
            dst = self.parseid(self._commanddict['destination'])
            transferers_channel = self.innerdata.find_users_channels_with_peer(self.userid)[0]
            channel = self.innerdata.channels[transferers_channel].peerchannel
            dst_context = self.innerdata.xod_config['phones'].get_main_line(self.userid)['context']

            if dst['type'] == 'user':
                extentodial = self.innerdata.xod_config['phones'].get_main_line(dst['id'])['number']
            elif dst['type'] == 'phone' and dst['id'] in self.innerdata.xod_config['phones'].keeplist:
                extentodial = self.innerdata.xod_config['phones'].keeplist[dst['id']]
            elif dst['type'] == 'exten':
                extentodial = dst['id']
            elif dst['type'] == 'voicemail' and dst['id'] in self.innerdata.xod_config['voicemails'].keeplist:
                # *97 vm number
                voicemail = self.innerdata.xod_config['voicemails'].keeplist[dst['id']]
                vm_number = voicemail['mailbox']
                prefix = self.innerdata.extenfeatures['extenfeatures']['vmboxslt']['exten']
                prefix = prefix[:len(prefix) - 1]
                extentodial = prefix + vm_number
                dst_context = voicemail['context']
            elif dst['type'] == 'meetme' and dst['id'] in self.innerdata.xod_config['meetmes'].keeplist:
                extentodial = self.innerdata.xod_config['meetmes'].keeplist[dst['id']]['confno']
            else:
                extentodial = None

            return [{'amicommand': 'transfer',
                      'amiargs': [channel, extentodial, dst_context]}]
        except Exception:
            logger.exception('Failed to transfer call')
            return [{'error': 'Incomplete transfer information'}]

    def ipbxcommand_atxfer(self):
        try:
            exten = self.parseid(self._commanddict['destination'])['id']
            context = self.innerdata.xod_config['phones'].get_main_line(self.userid)['context']
            channel = self.innerdata.find_users_channels_with_peer(self.userid)[0]
        except:
            logger.exception('Atxfer failed %s', self._commanddict)
            return [{'error': 'Incomplete info'}]
        else:
            return [{'amicommand': 'atxfer',
                     'amiargs': [channel, exten, context]}]

    def ipbxcommand_intercept(self):
        try:
            main_line = self.innerdata.xod_config['phones'].get_main_line(self.userid)
            chan_xid = self._commanddict['tointercept']
            chan_id = self.parseid(chan_xid)['id']
            return [{'amicommand': 'transfer',
                     'amiargs': [chan_id,
                                 main_line['number'],
                                 main_line['context']]}]
        except Exception:
            logger.warning('Failed to complete interception')
            return [{'error': 'Incomplete info'}]

    # hangup and one's own line management
    def ipbxcommand_hangup(self):
        channel = self.parseid(self._commanddict.get('channelids'))
        rep = {'amicommand': 'hangup',
               'amiargs': [channel.get('id')]}
        return [rep, ]

    def get_agent_info(self, command_dict):
        if 'agentids' not in command_dict or command_dict['agentids'] == 'agent:special:me':
            command_dict['agentids'] = self.innerdata.xod_config['users'].keeplist[self.userid]['agentid']
        if '/' in command_dict['agentids']:
            ipbx_id, agent_id = command_dict['agentids'].split('/', 1)
        else:
            ipbx_id, agent_id = self.ipbxid, command_dict['agentids']
        innerdata = self._ctiserver.safe[ipbx_id]
        if agent_id in innerdata.xod_config['agents'].keeplist:
            agent = innerdata.xod_config['agents'].keeplist[agent_id]
            status = innerdata.xod_status['agents'][agent_id]
            return agent, status

    def _get_agent_exten(self, command_dict, agent_id):
        if 'agentphonenumber' in command_dict:
            return command_dict['agentphonenumber']
        user_ids = [user['id'] for user in self.innerdata.xod_config['users'].keeplist.itervalues() if user['agentid'] == str(agent_id)]
        return self.innerdata.xod_config['phones'].get_main_line(user_ids[0])['number'] if user_ids else None

    def ipbxcommand_agentlogout(self):
        agent, status = self.get_agent_info(self._commanddict)
        if status['status'] != 'AGENT_LOGGEDOFF':
            return [{'amicommand': 'agentlogoff',
                     'amiargs': [agent['number'], True]}]

    def queue_generic(self, command, dopause=None):
        member = self.parseid(self._commanddict.get('member'))
        if not member:
            return [{'error': 'member'}]
        queue = self.parseid(self._commanddict.get('queue'))
        if not queue:
            return [{'error': 'queue'}]

        innerdata = self._ctiserver.safe.get(queue.get('ipbxid'))
        qsm = self._ctiserver._queuemember_service_manager
        return qsm.queue_generic(innerdata, command, queue, member, dopause)

    def ipbxcommand_queueadd(self):
        return self.queue_generic('add', self._commanddict.get('paused'))

    def ipbxcommand_queueremove(self):
        return self.queue_generic('remove')

    def ipbxcommand_queuepause(self):
        return self.queue_generic('pause', 'true')

    def ipbxcommand_queueunpause(self):
        return self.queue_generic('pause', 'false')

    def ipbxcommand_queuepause_all(self):
        self._commanddict['queue'] = 'queue:xivo/all'
        return self.queue_generic('pause', 'true')

    def ipbxcommand_queueunpause_all(self):
        self._commanddict['queue'] = 'queue:xivo/all'
        return self.queue_generic('pause', 'false')

    def ipbxcommand_queueremove_all(self):
        self._commanddict['queue'] = 'queue:xivo/all'
        return self.queue_generic('remove')

    def ipbxcommand_record(self):
        subcommand = self._commanddict.pop('subcommand')
        channel = self._commanddict.pop('channel')
        # XX take into account ipbxid
        if subcommand == 'start':
            datestring = time.strftime('%Y%m%d-%H%M%S', time.localtime())
            # kind agent => channel = logged-on channel
            # other kind => according to what is provided
            kind = 'phone'
            idv = '7'
            filename = 'cti-monitor-%s-%s-%s' % (datestring, kind, idv)
            rep = {'amicommand': 'monitor',
                   'amiargs': (channel, filename, 'false')}
            # wait the AMI event ack in order to fill status for channel
        elif subcommand == 'stop':
            rep = {'amicommand': 'stopmonitor',
                   'amiargs': (channel,)}
        return [rep]

    def ipbxcommand_listen(self):
        start = self._commanddict['subcommand'] == 'start'
        listeners_line = self.innerdata.xod_config['phones'].get_main_line(self.userid)
        listener_protocol = listeners_line['protocol']
        listener_name = listeners_line['name']
        agent_id = '/'.join(self._commanddict['destination'].split('/')[1:])
        agent_config = self.innerdata.xod_config['agents'].keeplist[agent_id]
        agent_number = agent_config['number']
        channel = 'Agent/%s' % agent_number

        rep = {}

        if start:
            rep = {'amicommand': 'origapplication',
                   'amiargs': ['ChanSpy',
                               '%s,d' % channel,
                               listener_protocol,
                               listener_name,
                               '000',
                               'mamaop']}

        return [rep]
