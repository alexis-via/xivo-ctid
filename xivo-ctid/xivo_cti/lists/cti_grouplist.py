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

import logging
import time
from xivo_cti.cti_anylist import AnyList

logger = logging.getLogger('grouplist')


class GroupList(AnyList):

    queuelocationprops = ['Paused', 'Status', 'Membership', 'Penalty', 'LastCall', 'CallsTaken',
                          'Xivo-QueueMember-StateTime']
    queuestats = ['Abandoned', 'Max', 'Completed', 'ServiceLevel', 'Weight', 'Holdtime',
                  'Xivo-Join', 'Xivo-Link', 'Xivo-Lost', 'Xivo-Wait', 'Xivo-TalkingTime', 'Xivo-Rate',
                  'Calls']

    def __init__(self, newurls=[], virtual=False):
        self.anylist_properties = {'name': 'groups',
                                   'urloptions': (1, 5, True)}
        AnyList.__init__(self, newurls)

    def update(self):
        ret = AnyList.update(self)
        self.reverse_index = {}
        for idx, ag in self.keeplist.iteritems():
            if ag['name'] not in self.reverse_index:
                self.reverse_index[ag['name']] = idx
            else:
                logger.warning('2 groups have the same name')
        return ret

    def hasqueue(self, queuename):
        return queuename in self.reverse_index

    def idbyqueuename(self, queuename):
        if queuename in self.reverse_index:
            idx = self.reverse_index[queuename]
            if idx in self.keeplist:
                return idx

    def getcontext(self, queueid):
        return self.keeplist[queueid]['context']

    def queueentry_rename(self, queueid, oldchan, newchan):
        if queueid in self.keeplist:
            if oldchan in self.keeplist[queueid]['channels']:
                self.keeplist[queueid]['channels'][newchan] = self.keeplist[queueid]['channels'][oldchan]
                del self.keeplist[queueid]['channels'][oldchan]
            else:
                logger.warning('queueentry_rename : channel %s is not in queueid %s',
                               oldchan, queueid)
        else:
            logger.warning('queueentry_rename : no such queueid %s', queueid)

    def queueentry_update(self, queueid, channel, position, entrytime, calleridnum, calleridname):
        if queueid in self.keeplist:
            self.keeplist[queueid]['channels'][channel] = { 'position' : position,
                                                            'entrytime' : entrytime,
                                                            'calleridnum' : calleridnum,
                                                            'calleridname' : calleridname }
        else:
            logger.warning('queueentry_update : no such queueid %s', queueid)

    def queueentry_remove(self, queueid, channel):
        if queueid in self.keeplist:
            if channel in self.keeplist[queueid]['channels']:
                del self.keeplist[queueid]['channels'][channel]
            else:
                logger.warning('queueentry_remove : channel %s is not in queueid %s',
                            channel, queueid)
        else:
            logger.warning('queueentry_remove : no such queueid %s', queueid)

    def queuememberupdate(self, queueid, location, event):
        changed = False
        if queueid in self.keeplist:
            if location not in self.keeplist[queueid]['agents_in_queue']:
                self.keeplist[queueid]['agents_in_queue'][location] = {}
                changed = True
            thisqueuelocation = self.keeplist[queueid]['agents_in_queue'][location]
            for prop in self.queuelocationprops:
                if prop in event:
                    if prop in thisqueuelocation:
                        if thisqueuelocation[prop] != event.get(prop):
                            thisqueuelocation[prop] = event.get(prop)
                            changed = True
                    else:
                        thisqueuelocation[prop] = event.get(prop)
                        changed = True
            if 'Xivo-QueueMember-StateTime' not in thisqueuelocation:
                thisqueuelocation['Xivo-QueueMember-StateTime'] = time.time()
                changed = True
        else:
            logger.warning('queuememberupdate : no such queueid %s', queueid)
        return changed
    
    def queuememberremove(self, queueid, location):
        changed = False
        if queueid in self.keeplist:
            if location in self.keeplist[queueid]['agents_in_queue']:
                del self.keeplist[queueid]['agents_in_queue'][location]
                changed = True
        else:
            logger.warning('queuememberremove : no such queueid %s', queueid)
        return changed
    
    def update_queuestats(self, queueid, event):
        changed = False
        if queueid in self.keeplist:
            thisqueuestats = self.keeplist[queueid]['queuestats']
            for statfield in self.queuestats:
                if statfield in event:
                    if statfield in thisqueuestats:
                        if thisqueuestats[statfield] != event.get(statfield):
                            thisqueuestats[statfield] = event.get(statfield)
                            changed = True
                    else:
                        thisqueuestats[statfield] = event.get(statfield)
                        changed = True
        else:
            logger.warning('update_queuestats : no such queueid %s', queueid)
        return changed
    
    def get_queues(self):
        return self.keeplist.keys()
    
    def get_queues_byagent(self, agid):
        queuelist = {}
        for qref, ql in self.keeplist.iteritems():
            lst = {}
            if agid in ql['agents_in_queue']:
                agprop = ql['agents_in_queue'][agid]
                for v in self.queuelocationprops:
                    if v in agprop:
                        lst[v] = agprop[v]
                    else:
                        logger.warning('get_queues_byagent : no property %s for agent %s in queue %s',
                                       v, agid, qref)
            lst['context'] = ql['context']
            queuelist[qref] = lst
        return queuelist
