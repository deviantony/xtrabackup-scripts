class ProgramError(Exception):

    def __init__(self, message):
        super(ProgramError, self).__init__(message)
