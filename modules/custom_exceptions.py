"""Custom exceptions"""


class ConfigurationError(Exception):
    def __init__(self, message="Class Configuration must implement setter methods for all attributes"):
        super().__init__(message)


class FlashingError(Exception):
    def __init__(self, message="Error occured during flashing"):
        super().__init__(message)


class LastResultNotRead(Exception):
    def __init__(self, message="Last stored result was not read, "
                               "please read last result before adding new task to queue"):
        super().__init__(message)


class TaskQueueIsEmpty(Exception):
    def __init__(self, message="Task queue  is empty, please add task before setting run event"):
        super().__init__(message)


class Busy(Exception):
    def __init__(self, message="Thread is currently busy with other running task"):
        super().__init__(message)
