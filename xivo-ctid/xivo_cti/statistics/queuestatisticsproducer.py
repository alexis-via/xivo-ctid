
class QueueStatisticsProducer(object):

    def __init__(self):
        self.logged_agents = {}
        self.queues_of_agent = {}

    def set_notifier(self, notifier):
        self.notifier = notifier

    def on_queue_added(self, queueid):
        self.logged_agents[queueid] = set()

    def on_agent_added(self, queueid, agentid):
        if agentid not in self.queues_of_agent:
            self.queues_of_agent[agentid] = set()
        self.queues_of_agent[agentid].add(queueid)

    def on_agent_loggedon(self, agentid):
        for queueid in self.queues_of_agent[agentid]:
            self.logged_agents[queueid].add(agentid)
            self._notify_change(queueid)

    def on_agent_loggedoff(self, agentid):
        for queueid in self.queues_of_agent[agentid]:
            self._decrement_agent(queueid, agentid)

    def on_agent_removed(self, queueid, agentid):
        if agentid in self.logged_agents[queueid]:
            self._decrement_agent(queueid, agentid)
        self.queues_of_agent[agentid].remove(queueid)

    def on_queue_removed(self, queueid):
        for agentid in self.queues_of_agent:
            if queueid in self.queues_of_agent[agentid]:
                self.queues_of_agent[agentid].remove(queueid)

    def _decrement_agent(self, queueid, agentid):
        self.logged_agents[queueid].remove(agentid)
        self._notify_change(queueid)

    def _notify_change(self, queueid):
        self.notifier.on_stat_changed({'queue':queueid,
                                          'loggedagents':len(self.logged_agents[queueid])})