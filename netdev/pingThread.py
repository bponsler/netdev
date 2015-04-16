from time import sleep
from threading import Thread

from ping import Ping
from logPriority import LogPriority


class PingThread(Thread):
    '''The PingThread class manages pinging a specific network device
    in a thread and notifying any corresponding netdev rules that
    the network device was lost or found.

    '''
    def __init__(self, hostname, config, timeout=500, packetSize=55):
        '''
        * hostname -- The hostname for the network device
        * config -- The NetDevConfig object
        * timeout -- The ping timeout
        * packetSize -- The ping packet size

        '''
        Thread.__init__(self)
        self.__hostname = hostname
        self.__timeout = timeout
        self.__config = config
        self.__foundHost = False

        self.__discoverRules = []  # List of rules to notify on device found
        self.__lostRules = []  # List of rules to notify on device lost

        self.__ping = Ping(self.__hostname, timeout, packetSize)

    def addRule(self, rule):
        '''Add a single rule pertaining to the network device managed
        by this PingThread.

        * rule -- The netdev rule

        '''
        if rule.isDiscoverRule():
            self.__discoverRules.append(rule)
        elif rule.isLostRule():
            self.__lostRules.append(rule)

    def stop(self):
        '''Stop the PingThread.'''
        self.__shouldExit = True

    def run(self):
        '''Called when the PingThread is started.'''
        self.__shouldExit = False
        while not self.__shouldExit:
            foundHost = self.__pingHost()
            if foundHost != self.__foundHost:
                if foundHost:
                    self.__config.log(LogPriority.Info, "Discovered host")

                    # Notify all rules of a discovered device
                    for rule in self.__discoverRules:
                        rule.onNotify()
                else:
                    self.__config.log(LogPriority.Info, "Lost host")

                    # Notify all rules of a lost device
                    for rule in self.__lostRules:
                        rule.onNotify()

                self.__foundHost = foundHost

            sleep(0.1)

    def __pingHost(self):
        '''Handle pinging the network device a single time.'''
        pingTime = self.__ping.do()
        return (pingTime is not None)
