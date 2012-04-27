import logging

logger = logging.getLogger("QueueStatisticsProducer")

class QueueStatisticsProducer(object):

    LOGGEDAGENT_STATNAME = "Xivo-LoggedAgents"

    def __init__(self):
        self.queues_of_agent = {}
        self.logged_agents = set()

    def set_notifier(self, notifier):
        self.notifier = notifier

    def on_queue_added(self, queueid):
        logger.info('queue id %s added', queueid)

    def on_agent_added(self, queueid, agentid):
        if agentid not in self.queues_of_agent:
            self.queues_of_agent[agentid] = set()
        self.queues_of_agent[agentid].add(queueid)
        if agentid in self.logged_agents:
            self._notify_change(queueid)
        logger.info('agent id %s added to queue id %s', agentid, queueid)

    def on_agent_loggedon(self, agentid):
        self.logged_agents.add(agentid)
        if agentid in self.queues_of_agent:
            for queueid in self.queues_of_agent[agentid]:
                self._notify_change(queueid)

    def on_agent_loggedoff(self, agentid):
        try:
            self.logged_agents.remove(agentid)
        except KeyError:
            pass
        if agentid in self.queues_of_agent:
            for queueid in self.queues_of_agent[agentid]:
                self._notify_change(queueid)

    def on_agent_removed(self, queueid, agentid):
        self.queues_of_agent[agentid].remove(queueid)
        if agentid in self.logged_agents:
            self._notify_change(queueid)

    def on_queue_removed(self, queueid):
        for agentid in self.queues_of_agent:
            if queueid in self.queues_of_agent[agentid]:
                self.queues_of_agent[agentid].remove(queueid)

    def _compute_nb_of_logged_agents(self, queueid):
        nb_of_agent_logged = 0
        for agentid in self.logged_agents:
            if queueid in self.queues_of_agent[agentid]:
                nb_of_agent_logged += 1
        return nb_of_agent_logged

    def _notify_change(self, queueid):
        self.notifier.on_stat_changed({queueid :
                                         { self.LOGGEDAGENT_STATNAME:self._compute_nb_of_logged_agents(queueid)}
                                         })
