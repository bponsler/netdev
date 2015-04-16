#!/usr/bin/env python
import sys
from threading import Thread
from time import sleep, ctime
from traceback import print_exc
from os import listdir, system, getuid
from os.path import basename, join, sep, exists, isfile, getmtime

from logPriority import LogPriority
from rule import NetDevRule
from config import NetDevConfig
from pingThread import PingThread


class NetDev(Thread):
    '''The NetDev class acts as a device manager for network devices. It
    loads netdev rule files from a specific configuration directory where
    each rule can execute logic when a network device is found or lost.

    '''
    RulesDir = join(sep, "etc", "netdev", "rules.d")
    ConfigFile = join(sep, "etc", "netdev", "netdev.conf")

    CommentChar = "#"

    def __init__(self):
        '''Constructor.'''
        Thread.__init__(self)
        self.__config = NetDevConfig(self.ConfigFile)

        # Map hostnames to the associated ping thread object
        self.__pingThreadMap = {}

        self.__ruleMap = self.__loadRules()

    def run(self):
        '''Called when the thread is run.'''
        for thread in self.__pingThreadMap.values():
            thread.start()

        self.__shouldRun = True
        while self.__shouldRun:
            self.__handleDeletedFiles()
            self.__handleRuleChanges()
            self.__handleNewFiles()

            sleep(1.0)

    def stop(self):
        '''Called when the thread is stopped.'''
        for thread in self.__pingThreadMap.values():
            thread.stop()

        self.__shouldRun = False

    def __loadRules(self):
        '''Load all of the rules from the configuration directory.'''
        ruleMap = {}

        if exists(self.RulesDir):
            for filename in listdir(self.RulesDir):
                filePath = join(self.RulesDir, filename)
                rules = self.__getRulesForFile(filePath)
                if rules is not None:
                    # Get the last modification time of the file
                    modificationTime = self.__getModificationTime(filePath)

                    ruleMap[filePath] = (rules, modificationTime)

        return ruleMap

    def __getRulesForFile(self, filePath):
        '''Get the rules contained within a single rule file.

        * filePath -- The path to the rule file

        '''
        filename = basename(filePath)
        if isfile(filePath) and filename.lower().endswith(".rules"):
            try:
                return self.__parseFile(filePath)
            except:
                print_exc()
                print "Error parsing file: %s" % filename

        return None

    def __parseFile(self, filename):
        '''Parse a single rule file.

        * filename -- The path to the rule file

        '''
        rules = []

        if exists(filename):
            # Read the file
            fd = open(filename, "r")
            content = fd.read().strip()
            fd.close()

            for line in content.split("\n"):
                line = line.strip()

                # Ignore empty lines, and comments
                if len(line) > 0 and not line.startswith(self.CommentChar):
                    try:
                        rule = NetDevRule(filename, line)
                    except Exception, e:
                        print_exc()
                        print >> sys.stderr, "Warning: Ignoring invalid " \
                            "rule in file: %s" % filename
                        print "      Rule: [%s]" % line
                    else:
                        self.__config.log(
                            LogPriority.Debug,
                            "[%s] created rule: %s" % (filename, line))

                        rules.append(rule)

                        # Create a thread to monitor the hostname associated
                        # with this rule -- only create one thread per
                        # unique host
                        hostname = rule.getHostname()
                        thread = self.__pingThreadMap.get(hostname, None)
                        if thread is None:
                            self.__config.log(
                                LogPriority.Debug,
                                "Created thread to monitor " \
                                    "host: %s" % hostname)

                            thread = PingThread(hostname, config=self.__config)
                            self.__pingThreadMap[hostname] = thread

                        thread.addRule(rule)

        return rules

    def __handleNewFiles(self):
        '''Check for new rule files.'''
        ruleMap = {}

        if exists(self.RulesDir):
            for filename in listdir(self.RulesDir):
                filePath = join(self.RulesDir, filename)
                if filePath not in self.__ruleMap:
                    rules = self.__getRulesForFile(filePath)
                    if rules is not None:
                        self.__config.log(
                            LogPriority.Debug,
                            "Found new rules file: %s" % filePath)

                        modificationTime = self.__getModificationTime(filePath)
                        self.__ruleMap[filePath] = (rules, modificationTime)

    def __handleDeletedFiles(self):
        '''Check for deleted rule files.'''
        for filePath in self.__ruleMap.keys():
            if not exists(filePath):
                self.__config.log(
                    LogPriority.Debug,
                    "Lost rules from file: %s" % filePath)

                del self.__ruleMap[filePath]

    def __handleRuleChanges(self):
        '''Check for changes to rule files.'''
        # Check for changes to rule files
        for filePath, fileTuple in self.__ruleMap.items():
            _, modificationTime = fileTuple
            newTime = self.__getModificationTime(filePath)

            # The file has changed if the modification time is different
            # than the last time the file was updated
            if modificationTime != newTime:
                rules = self.__getRulesForFile(filePath)
                if rules is not None:
                    self.__config.log(
                        LogPriority.Debug,
                        "Loaded rules from file: %s" % filePath)

                    self.__ruleMap[filePath] = (rules, newTime)

    def __getModificationTime(self, filePath):
        return ctime(getmtime(filePath))
        

if __name__ == '__main__':
    # Ensure that the application is run as root
    if getuid() != 0:
        print "Error: %s must be run as root!" % sys.argv[0]
        exit(1)

    nd = NetDev()
    nd.start()

    while True:
        try:
            sleep(0.1)
        except (KeyboardInterrupt, SystemExit):
            break

    nd.stop()
