from os.path import exists

from logPriority import LogPriority


class NetDevConfig:
    '''The NetDevConfig class encapsulates the configuration file for
    netdev. It handles reading and parsing the file and making the
    configuration options externally available.

    '''
    CommentChar = "#"

    # Name of the log priority setting
    LogPriority = "netdev_log"

    def __init__(self, filename):
        '''
        * filename -- The netdev config file

        '''
        self.__settings = {
            self.LogPriority: LogPriority.Error,
            }

        self.__parseConfig(filename)

        # Grab specific configuration settings
        priority = self.get(NetDevConfig.LogPriority)
        self.__logPriority = LogPriority.getValue(priority)

    def get(self, key, default=None):
        '''Get a setting from the configuration.

        * key -- The name of the setting
        * default -- The value returned if the setting does not exist

        '''
        return self.__settings.get(key, default)

    def log(self, priority, message):
        '''Log a message at the given priority level.

        * priority -- The priority for the logged message
        * message -- The message to log

        '''
        priorityValue = LogPriority.getValue(priority)
        if priorityValue >= self.__logPriority:
            print "netdev: %s" % message

    def __parseConfig(self, filename):
        '''Parse the netdev config file.

        * filename -- The netdev config file

        '''
        # Do nothing if the file does not exist
        if not exists(filename):
            return

        fd = open(filename, "r")
        content = fd.read().strip()
        fd.close()

        lines = content.split("\n")
        for line in lines:
            # Ignore empty lines and comments
            if len(line) == 0 or line.startswith(self.CommentChar):
                self.__parseSetting(line)

    def __parseSetting(self, line):
        '''Parse a single line from the netdev config file.

        * line -- A line from the netdev config file

        '''
        parts = line.split("=")
        if len(parts) == 2:
            key, value = parts

            # Handle unknown settings
            if key not in self.__settings:
                print >> sys.stderr, "Warning: Config specified " \
                    "unknown setting: %s" % key
                return

            self.__settings[key] = value
