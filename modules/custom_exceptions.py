"""Custom exceptions"""


class ConfigurationError(Exception):
    def __init__(self, message="Class Configuration must implement setter methods for all attributes"):
        super().__init__(message)


class FlashingError(Exception):
    def __init__(self, message="Error occured during flashing"):
        super().__init__(message)
