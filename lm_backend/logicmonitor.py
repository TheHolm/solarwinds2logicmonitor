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
    """Raised when Logic Monitor API returns strange and unexpected data. Indicates problem with LM or in this module logic """
    pass


class LM_Session_Query_Error(LM_Session_Error):
    """Raised when Logic Monitor API returns error. Check your query data"""
    pass


if __name__ == '__main__':
    quit()
