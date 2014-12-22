class ProgramError(Exception):

    def __init__(self, message):
        super(ProgramError, self).__init__(message)


class ProcessError(Exception):

    def __init__(self, command, returncode):
        message = ("The following command failed : %s"
                   " - Status code: %d" % (command, returncode))
        super(ProcessError, self).__init__(message)
        self.command = command
        self.returncode = returncode
