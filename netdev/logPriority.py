class LogPriority:
    '''The LogPriority class encapsulates all of the log priorites
    for netdev.

    '''
    Debug = "debug"
    Info = "info"
    Warn = "warn"
    Error = "error"

    # List of all priorities
    Priorities = [
        Debug,
        Info,
        Warn,
        Error,
        ]

    @classmethod
    def getValue(cls, priority):
        '''Return the netdev log priority value.

        * priority -- The priority string name
        '''
        return cls.Priorities.index(priority)
