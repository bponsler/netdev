import re


class RuleName:
    '''Name of supported types of rules.'''
    Action = "ACTION"
    Hostname = "HOSTNAME"
    Run = "RUN"


class Actions:
    '''Names of supported types of actions.'''
    Discover = "discover"
    Lost = "lost"

    # List of all actions
    AllActions = [
        Discover,
        Lost,
        ]


class NetDevRule:
    '''Each rule is constructed of a series of key value pairs, where each
    pair is separated by a comma. Match keys are conditions used to
    identify the device which the rule is acting upon. When all match
    keys in a rule correspond to the device being handled, then the rule
    is applied and the actions of the assignment keys are invoked. Every
    rule should consist of at least one match key and at least one
    assignment key.

    '''
    MatchOperatorRegEx = "(.*)==(.*)"
    AssignOperatorRegEx = "(.*)[\+?]=(.*)"

    def __init__(self, filename, line):
        '''
        * filename -- The netdev rule file
        * line -- The line (containing a single rule) to parse from the file

        '''
        self.__filename = filename
        self.__foundDevice = False
        self.__action = None
        self.__hostname = None

        self.__matchRules = {}
        self.__assignRules = {}

        # Map rule operator regular expressions to functions that parse
        # that particular type of rule
        self.__operatorFnMap = {
            self.MatchOperatorRegEx: self.__parseMatch,
            self.AssignOperatorRegEx: self.__parseAssign,
            }

        # Map rule names to the function that gets called when the
        # particular rule is executed
        self.__ruleFnMap = {
            RuleName.Run: self.__onRun,
            }

        self.__parseLine(line)

        # Validate the rule
        self.__validateRule()

    def getHostname(self):
        '''Get the hostname for this rule.'''
        return self.__hostname

    def getAction(self):
        '''Get the action for this rule.'''
        return self.__action

    def isAction(self, action):
        '''Determine if this rule contains an action.'''
        return (self.__action == action)

    def isDiscoverRule(self):
        '''Determine if this rule is a discovery rule (i.e., triggers when
        a device is discovered).

        '''
        return self.isAction(Actions.Discover)

    def isLostRule(self):
        '''Determine if this rule is a lost rule (i.e., triggers when
         a device is lost).

         '''
        return self.isAction(Actions.Lost)

    def onNotify(self):
        '''Called when the managed device is discovered or lost.'''
        if self.__checkMatchRules():
            self.__executeRule()

    def __checkMatchRules(self):
        '''Check all of match rules to see if all of the match rules pass.'''
        # Check all match rules
        for key, value in self.__matchRules.iteritems():
            ruleFn = self.__ruleFnMap.get(ruleKey, None)
            if ruleFn is not None:
                ruleFn(value)

        return True  # All match rules passed

    def __executeRule(self):
        '''Execute the rule.'''
        # Execute all of the assign actions
        for ruleKey, ruleValue in self.__assignRules.iteritems():
            ruleFn = self.__ruleFnMap.get(ruleKey, None)
            if ruleFn is not None:
                ruleFn(ruleValue)

    def __onRun(self, runRules):
        '''Called when the a run rule is executed.

        * runRules -- List of commands to run

        '''
        for command in runRules:
            if system(command) != 0:
                print >> sys.stderr, "Error: Failed to execute " \
                    "command for rule: %s" % self.__filename
                print >> sys.stderr, "Failed command: [%s]" % command
                break  # Do not run any more commands

    def __validateRule(self):
        '''Validate the rule.'''
        # Check for required rules
        if self.__hostname is None:
            raise Exception("Rule must define a %s" % RuleName.Hostname)

        # Check for an action
        if self.__action is None:
            raise Exception("Rule must define an %s" % RuleName.Action)

        # Check for valid action
        if self.__action not in Actions.AllActions:
            raise Exception("Rule has unknown " \
                                "action: %s. Valid actions are: " \
                                "%s" % (self.__action, Actions.AllActions))

        # Check for at least one assignment rule
        if len(self.__assignRules) == 0:
            raise Exception("Rule must define at least one assignment rule")

    def __parseLine(self, line):
        '''Parse a single line of the netdev rules file.

        * line -- The line

        '''
        ruleParts = line.split(",")

        for part in ruleParts:
            part = part.strip()  # Remove any extra spaces

            foundMatch = False
            for operatorRegEx, parseFn in self.__operatorFnMap.iteritems():
                pattern = re.compile(operatorRegEx)
                match = pattern.match(part)
                if match is not None:
                    key = match.groups()[0]
                    value = match.groups()[1]

                    # Each value should be surrounded by quotes
                    if len(value) < 2 or value[0] != '"' or value[-1] != '"':
                        raise Exception("Value for rule %s must be " +
                                        "surrounded by quotes" % key)

                    # Remove the quotes
                    value = value[1:-1]

                    # Parse the key value pair
                    parseFn(key, value)
                    foundMatch = True
                    break  # Should only match a single operator

            if not foundMatch:
                raise Exception("Invalid netdev rule: %s" % part)

    def __parseMatch(self, key, value):
        '''Parse a single match rule.

        * key -- The key
        * value -- The value

        '''
        if key == RuleName.Action:
            self.__action = value
            return
        elif key == RuleName.Hostname:
            self.__hostname = value
            return

        self.__matchRules[key] = value

    def __parseAssign(self, key, value):
        '''Parse a single assign rule.

        * key -- The key
        * value -- The value

        '''
        assign = self.__assignRules.get(key, [])
        assign.append(value)
        self.__assignRules[key] = assign
