import requests
import urllib3.exceptions

import base64
import time
import hashlib
import hmac

import json

class LM_Session_Error(Exception):
    """Base class for other exceptions"""
    pass


class LM_Session_Database_Error(LM_Session_Error):
    """Raised when Logic Monitor API returns strange and unexpected data. Indicates problem with LM or in this module logic. Raise bug report or ticket with LM """
    pass


class LM_Session_Query_Error(LM_Session_Error):
    """Raised when Logic Monitor API returns error. Check your query data"""
    pass


class LM_Session_Internal_Error(LM_Session_Error):
    """Raised when something wrong with module itself. Raise a bug report"""
    pass


if __name__ == '__main__':
    quit()
