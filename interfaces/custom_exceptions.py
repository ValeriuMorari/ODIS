"""Custom exceptions"""


class CommandTemplateError(Exception):
    def __init__(self, message="Invalid command template. Example: command(arg1; arg2; ...; argN)"):
        super().__init__(message)


class InvalidInitialization(Exception):
    def __init__(self, message="Method 'initialize' expected as first message"):
        super().__init__(message)


class InvalidCommand(Exception):
    def __init__(self, message="Invalid command accessed. Command was not found within automation component"):
        super().__init__(message)
