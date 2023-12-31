"""Error codes module"""
from enum import IntEnum


class ErrorCode(IntEnum):
    MACRO_NOT_FOUND = 60
    NO_ERROR = 1
    UNKNOWN_ERROR = 6
    INTERFACE_TO_SOAP_NOT_DEFINED = 61
    ODX_CONTAINER_DO_NOT_EXISTS = 62
    FLASH_PROCESS_ERROR = 63
    CLEAR_DTC_ERROR = 64
    FLASH_PRECONDITIONS_NOT_FULFILLED = 65
    DATASET_PATH_NOT_FOUND = 66
    RAW_SERVICE_ERROR = 67
    ODIS_NO_ECU_CONNECTION = 176