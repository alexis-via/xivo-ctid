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

import logging
import time
from xivo_cti.cti_anylist import ContextAwareAnyList
from xivo.asterisk import protocol_interface
from xivo.asterisk.protocol_interface import InvalidChannelError

logger = logging.getLogger('phonelist')


class PhonesList(ContextAwareAnyList):

    def __init__(self, innerdata):
        self._innerdata = innerdata
        ContextAwareAnyList.__init__(self, 'phones')
        self._phone_id_by_proto_and_name = {}

    def init_data(self):
        super(PhonesList, self).init_data()
        self._init_reverse_dictionaries()

    def add(self, phone_id):
        super(PhonesList, self).add(phone_id)
        self._add_to_reverse_dictionaries(phone_id)

    def delete(self, phone_id):
        self._remove_from_reverse_dictionaries(phone_id)
        super(PhonesList, self).delete(phone_id)

    def _init_reverse_dictionaries(self):
        phone_id_by_proto_and_name = {}
        for phone_id, phone in self.keeplist.iteritems():
            proto_and_name = phone['protocol'] + phone['name']
            phone_id_by_proto_and_name[proto_and_name] = phone_id
        self._phone_id_by_proto_and_name = phone_id_by_proto_and_name

    def _add_to_reverse_dictionaries(self, phone_id):
        phone = self.keeplist[phone_id]
        proto_and_name = phone['protocol'] + phone['name']
        self._phone_id_by_proto_and_name[proto_and_name] = phone_id

    def _remove_from_reverse_dictionaries(self, phone_id):
        phone = self.keeplist[phone_id]
        proto_and_name = phone['protocol'] + phone['name']
        del self._phone_id_by_proto_and_name[proto_and_name]

    def __createorupdate_comm__(self, phoneid, commid, infos):
        comms = self.keeplist[phoneid]['comms']
        if commid in self.keeplist[phoneid]['comms']:
            if 'calleridnum' in infos and comms[commid].get('calleridnum') != infos['calleridnum']:
                logger.debug('  __createorupdate_comm__ changed calleridnum[%s %s] %s => %s',
                             commid, comms[commid].get('thischannel'), comms[commid].get('calleridnum'), infos['calleridnum'])
            self.keeplist[phoneid]['comms'][commid].update(infos)
        elif 'calleridnum' in infos:
            logger.debug('  __createorupdate_comm__ new calleridnum[%s %s] : %s',
                         commid, infos.get('thischannel'), infos['calleridnum'])
            self.keeplist[phoneid]['comms'][commid] = infos
            self.setlinenum(phoneid, commid)

    def setlinenum(self, phoneid, commid):
        """
        Define a line number for the phone, according to the currently 'busy'
        channels/uniqueids.
        This can not (at the time being, at least) be directly related
        to the line numbers on the physical phones.
        """
        usedlines = []
        for cinfo in self.keeplist[phoneid]['comms'].itervalues():
            if 'linenum' in cinfo:
                usedlines.append(cinfo['linenum'])
        linenum = 1
        while (linenum in usedlines):
            linenum += 1
        self.keeplist[phoneid]['comms'][commid]['linenum'] = linenum

    def ami_newstate(self, phoneid, uid, channel, status):
        self.__createorupdate_comm__(phoneid, uid, {'status': status})

    def ami_dial(self, phoneidsrc, phoneiddst, uidsrc, uiddst, puidsrc, puiddst):
        if phoneidsrc in self.keeplist:
            infos = {'thischannel': puidsrc.get('channel'),
                     'peerchannel': puidsrc.get('dial'),
                     'status': 'calling',
                     'time-dial': 0,
                     'timestamp-dial': time.time(),
                     # 'calleridname' : puidsrc.get('calleridname'),
                     'calleridnum': puidsrc.get('extension')
                     }
            self.__createorupdate_comm__(phoneidsrc, uidsrc, infos)
        if phoneiddst in self.keeplist:
            infos = {'thischannel': puiddst.get('channel'),
                     'peerchannel': puiddst.get('dial'),
                     'status': 'ringing',
                     'time-dial': 0,
                     'timestamp-dial': time.time(),
                     'calleridname': puidsrc.get('calleridname'),
                     'calleridnum': puidsrc.get('calleridnum')
                     }
            self.__createorupdate_comm__(phoneiddst, uiddst, infos)

    def ami_link(self, phoneidsrc, phoneiddst, uidsrc, uiddst, puidsrc, puiddst, clidsrc, cliddst, clidnamesrc, clidnamedst):
        logger.debug(u'phonelist::ami_link(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                     phoneidsrc, phoneiddst, uidsrc, uiddst, puidsrc, puiddst, clidsrc, cliddst, clidnamesrc, clidnamedst)
        if phoneidsrc in self.keeplist:
            infos = {'time-link': 0,
                     'peerchannel': puidsrc['link'],
                     'status': 'linked-caller',
                     'timestamp-link': time.time()
                     }
            if clidnamedst is not None:
                infos['calleridname'] = clidnamedst
            if cliddst is not None:
                infos['calleridnum'] = cliddst
            if uidsrc in self.keeplist[phoneidsrc]['comms']:
                self.__createorupdate_comm__(phoneidsrc, uidsrc, infos)
            else:
                infos['thischannel'] = puidsrc['channel']
                self.__createorupdate_comm__(phoneidsrc, uidsrc, infos)
                logger.debug('phonelist::ami_link %s not found (src)', uidsrc)
            logger.debug('phonelist::ami_link gruik %s %s', phoneidsrc, self.keeplist[phoneidsrc]['comms'])
        if phoneiddst in self.keeplist:
            infos = {'time-link': 0,
                     'peerchannel': puiddst['link'],
                     'status': 'linked-called',
                     'timestamp-link': time.time()
                     }
            if clidnamesrc is not None:
                infos['calleridname'] = clidnamesrc
            if clidsrc is not None:
                infos['calleridnum'] = clidsrc
            if uiddst in self.keeplist[phoneiddst]['comms']:
                self.__createorupdate_comm__(phoneiddst, uiddst, infos)
            else:
                infos['thischannel'] = puiddst['channel']
                self.__createorupdate_comm__(phoneiddst, uiddst, infos)
                logger.debug('phonelist::ami_link %s not found (dst)', uiddst)
            logger.debug('phonelist::ami_link gruik %s %s', phoneiddst, self.keeplist[phoneiddst]['comms'])

    def ami_unlink(self, phoneidsrc, phoneiddst, uidsrc, uiddst, puidsrc, puiddst):
        if phoneidsrc in self.keeplist:
            if uidsrc in self.keeplist[phoneidsrc]['comms']:
                infos = {'status': 'unlinked-caller',
                         'time-link': 0,
                         'timestamp-link': time.time()}
                self.keeplist[phoneidsrc]['comms'][uidsrc].update(infos)
        if phoneiddst in self.keeplist:
            if uiddst in self.keeplist[phoneiddst]['comms']:
                infos = {'status': 'unlinked-called',
                         'time-link': 0,
                         'timestamp-link': time.time()}
                self.keeplist[phoneiddst]['comms'][uiddst].update(infos)

    def ami_rename(self, oldphoneid, newphoneid, oldname, newname, uid):
        # rename channels
        for v in self.keeplist.itervalues():
            for kk in v['comms'].itervalues():
                if kk.get('thischannel') == oldname:
                    kk['thischannel'] = newname
                if kk.get('peerchannel') == oldname:
                    kk['peerchannel'] = newname
        # move channels from one phone to another
        if oldphoneid and newphoneid and oldphoneid != newphoneid:
            if uid in self.keeplist[oldphoneid]['comms'] and uid not in self.keeplist[newphoneid]['comms']:
                self.keeplist[newphoneid]['comms'][uid] = self.keeplist[oldphoneid]['comms'][uid]
                self.setlinenum(newphoneid, uid)
                del self.keeplist[oldphoneid]['comms'][uid]
            else:
                logger.warning('(ami_rename) %s : could not move from %s to %s', uid, oldphoneid, newphoneid)

    def ami_rename_totrunk(self, oldphoneid, oldname, newname, uid):
        tomove = None
        for v in self.keeplist.itervalues():
            for kk in v['comms'].itervalues():
                if kk.get('thischannel') == oldname:
                    kk['thischannel'] = newname
                if kk.get('peerchannel') == oldname:
                    kk['peerchannel'] = newname
        if uid in self.keeplist[oldphoneid]['comms']:
            tomove = self.keeplist[oldphoneid]['comms'][uid]
            # do not remove the reference at once, because, the client side needs to
            # know that the uid has been hanged-up
            # del self.keeplist[oldphoneid]['comms'][uid]
            self.keeplist[oldphoneid]['comms'][uid]['status'] = 'hangup'
        else:
            logger.warning('(ami_rename_totrunk) %s : could not remove %s', uid, oldphoneid)
        return tomove

    def ami_rename_fromtrunk(self, newphoneid, oldname, newname, uid, tomove):
        for v in self.keeplist.itervalues():
            for kk in v['comms'].itervalues():
                if kk.get('thischannel') == oldname:
                    kk['thischannel'] = newname
                if kk.get('peerchannel') == oldname:
                    kk['peerchannel'] = newname
        if tomove and uid not in self.keeplist[newphoneid]['comms']:
            self.keeplist[newphoneid]['comms'][uid] = tomove
            self.setlinenum(newphoneid, uid)
        else:
            logger.warning('(ami_rename_fromtrunk) %s : could not set %s', uid, newphoneid)

    def ami_hold(self, phoneid, uid):
        if phoneid in self.keeplist:
            if uid in self.keeplist[phoneid]['comms']:
                self.keeplist[phoneid]['comms'][uid]['time-hold'] = time.time()
            else:
                logger.warning('ami_hold : no uid %s for phoneid %s', uid, phoneid)
        else:
            logger.warning('ami_hold : no phoneid %s', phoneid)

    def ami_unhold(self, phoneid, uid):
        if phoneid in self.keeplist:
            if uid in self.keeplist[phoneid]['comms']:
                if 'time-hold' in self.keeplist[phoneid]['comms'][uid]:
                    del self.keeplist[phoneid]['comms'][uid]['time-hold']
                self.keeplist[phoneid]['comms'][uid]['time-hold'] = time.time()
            else:
                logger.warning('ami_hold : no uid %s for phoneid %s', uid, phoneid)
        else:
            logger.warning('ami_hold : no phoneid %s', phoneid)

    def ami_hangup(self, uid):
        phoneidlist = []
        for phoneid, phoneprops in self.keeplist.iteritems():
            if uid in phoneprops['comms']:
                phoneprops['comms'][uid]['status'] = 'hangup'
                if phoneid not in phoneidlist:
                    phoneidlist.append(phoneid)
        return phoneidlist

    def clear(self, uid):
        phoneidlist = []
        for phoneid, phoneprops in self.keeplist.iteritems():
            if uid in phoneprops['comms']:
                del phoneprops['comms'][uid]
                if phoneid not in phoneidlist:
                    phoneidlist.append(phoneid)
        return phoneidlist

    def setdisplayhints(self, dh):
        self.display_hints = dh

    def ami_extstatus(self, phoneid, status):
        if phoneid in self.keeplist:
            if status not in self.display_hints:
                status = '-2'
            # changed = not (self.keeplist[phoneid]['hintstatus'] == self.display_hints.get(status))
            changed = not isinstance(self.keeplist[phoneid]['hintstatus'], dict) or not (self.keeplist[phoneid]['hintstatus'].get('code') == status)
            if changed:
                self.keeplist[phoneid]['hintstatus'] = self.display_hints.get(status)
                self.keeplist[phoneid]['hintstatus']['code'] = status
            return changed
        return False

    def ami_parkedcall(self, phoneid, uid, ctuid, exten):
        if phoneid in self.keeplist:
            # write "parque" in unicode !
            infos = {'status': 'linked-caller',
                     'time-link': 0,
                     'timestamp-link': time.time(),
                     'calleridnum': exten,
                     'calleridname': '<parked>'}
            self.__createorupdate_comm__(phoneid, uid, infos)

    def ami_unparkedcall(self, phoneid, uid, ctuid):
        if phoneid in self.keeplist:
            logger.debug('phone::ami_unparkedcall %s %s %s', phoneid, uid, ctuid)
            if uid in self.keeplist[phoneid]['comms']:
                # parked channel
                infos = {'status': 'linked-called',
                         'thischannel': ctuid['channel'],
                         'peerchannel': ctuid['peerchannel'],
                         'time-link': 0,
                         # 'calleridnum' : ctuid['parkexten-callback'],
                         'timestamp-link': time.time()}
                self.keeplist[phoneid]['comms'][uid].update(infos)
            else:
                # cfrom
                infos = {'status': 'linked-caller',
                         'thischannel': ctuid['channel'],
                         'peerchannel': ctuid['peerchannel'],
                         'time-link': 0,
                         # 'calleridnum' : ctuid['parkexten-callback']
                         'timestamp-link': time.time()}
                self.keeplist[phoneid]['comms'][uid] = infos
                self.setlinenum(phoneid, uid)

    def status(self, phoneid):
        tosend = {}
        if phoneid in self.keeplist:
            tosend = {'class': 'phones',
                      'direction': 'client',
                      'function': 'update',
                      'phoneid': phoneid,
                      'status': self.keeplist[phoneid]}
        return tosend

    def ami_meetmejoin(self, phoneid, uid, meetmenum):
        if phoneid in self.keeplist:
            if uid in self.keeplist[phoneid]['comms']:
                infos = {'timestamp-link': time.time(),
                         'calleridname': '<meetme>',
                         'calleridnum': meetmenum}
                self.keeplist[phoneid]['comms'][uid].update(infos)

    def find_phone_by_channel(self, channel):
        try:
            proto_iface = protocol_interface.protocol_interface_from_channel(channel)
        except InvalidChannelError:
            return None
        phone_id = self.get_phone_id_from_proto_and_name(proto_iface.protocol.lower(), proto_iface.interface)

        if phone_id is None:
            return None
        else:
            return self.keeplist[phone_id]

    def get_main_line(self, user_id):
        users_phones = [phone for phone in self.keeplist.itervalues() if int(phone['iduserfeatures']) == int(user_id)]
        return users_phones[0] if users_phones else None

    def get_phone_id_from_proto_and_name(self, proto, name):
        proto_and_name = proto + name
        return self._phone_id_by_proto_and_name.get(proto_and_name)

    def get_callerid_from_phone_id(self, phone_id):
        phone = self.keeplist[phone_id]
        protocol = phone['protocol']
        if protocol == 'sccp':
            return self._compute_callerid_for_sccp_phone(phone)
        else:
            return phone['callerid']

    def _compute_callerid_for_sccp_phone(self, phone):
        return '"%s" <%s>' % (phone['cid_name'], phone['cid_num'])
