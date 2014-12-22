class ProgramError(Exception):

    def __init__(self, message):
        super(ProgramError, self).__init__(message)


class CommandError(Exception):

    def __init__(self, command, returncode):
        message = ("The following command failed : %s"
                   " - Status code: %d" % (command, returncode))
        super(CommandError, self).__init__(message)
        self.command = command
        self.returncode = returncode
