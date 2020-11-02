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


class LM_Session:

    def __init__(self, AccessId, AccessKey, Company):
        ''' does not do much , just store Auth data in variables and tests that they a valig by getting some node data '''

        if AccessId is None or AccessKey is None or Company is None:
            raise Exception("Empty AccessId, AccessKey or Company")

        self.AccessId = str(AccessId)
        self.AccessKey = str(AccessKey)
        self.Company = str(Company)

        self.baseURL = 'https://' + self.Company + '.logicmonitor.com/santaba/rest'

        # checking that cre can login to LM
        # starting session
        self.SessionId = requests.Session()
#        self.SessionId.headers.update({'Content-Type': 'application/json'})
#        adapter = TlsAdapter(ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_3)

        # Check is account works and have NodeMangemt Rights.
        result = self.call_API('GET', '/device/devices', params={'size': 1})
        if result['status'] != 200:
            raise LM_Session_Error(str(result))

    def call_API(self, httpMethod, resourcePath, payload='', params='', session_timeout=5):
        ''' Make a call to LM API endpoint returns json'''
        ''' payload, params - can be and should be a dicitionary '''

        if httpMethod not in ('GET', 'POST', 'PATCH', 'DELETE'):
            raise LM_Session_Error("Only 'GET', 'PUT', 'PATCH' requests are supported")

        if not isinstance(payload, str):
            payload = json.dumps(payload)
        # Get current time in milliseconds
        epoch = str(int(time.time()) * 1000)

        # Concatenate Request details
        requestVars = httpMethod + epoch + payload + resourcePath
        # requestVars = httpMethod + epoch + resourcePath

        # Construct signature
        signature = base64.b64encode(hmac.new(self.AccessKey.encode(), msg=requestVars.encode(), digestmod=hashlib.sha256).hexdigest().encode())
        auth_header = 'LMv1 ' + self.AccessId + ':' + signature.decode() + ':' + epoch
        headers = {'Content-Type': 'application/json',
                   'Authorization': auth_header}

        try:
            self.response = self.SessionId.request(httpMethod, self.baseURL+resourcePath, params=params, data=payload, headers=headers, timeout=session_timeout)
        except urllib3.exceptions.ReadTimeoutError as e:
            raise LM_Session_Database_Error('Connection timeout' + str(e))
        else:
            self.response.raise_for_status()
        return(self.response.json())

    def get(self, resourcePath, payload='', params='', session_timeout=10):
        ''' Simple wrper for call_API, saves you affor to passing GET to it'''
        return(self.call_API('GET', resourcePath, payload=payload, params=params, session_timeout=session_timeout))

    def post(self, resourcePath, payload='', params='', session_timeout=10):
        ''' Simple wrper for call_API, saves you affor to passing POST to it'''
        return(self.call_API('POST', resourcePath, payload=payload, params=params, session_timeout=session_timeout))

    def patch(self, resourcePath, payload='', params='', session_timeout=10):
        ''' Simple wrper for call_API, saves you affor to passing PATCH to it'''
        return(self.call_API('PATCH', resourcePath, payload=payload, params=params, session_timeout=session_timeout))

    def delete(self, resourcePath, payload='', params='', session_timeout=10):
        ''' Simple wrper for call_API, saves you affor to passing DELETE to it'''
        return(self.call_API('DELETE', resourcePath, payload=payload, params=params, session_timeout=session_timeout))


class LM_DeviceGroup:
    ''' represent device group in LM or folder on disk'''
    keys_to_store = ('id',
                     'parentId',
                     'customProperties',
                     'defaultCollectorId',
                     'description',
                     'extra',
                     'fullPath',
                     'name')

    def __init__(self, LM_Session, id=None, filePath=None, fileSubPath="/"):
        ''' can be created ether by specifying LM group ID ( data will be pulled from LM or by path to file )'''
        # if not logicmonitor.LM_Session.is_dataclass(LM_Session):
        #    raise LM_Session_Error('LM_Session must be type of logicmonitor.LM_Session. got: ' + type(LM_Session))
        #    quit(1)
        if id is None and filePath is None:
            raise LM_Session_Error('ether id or filePath need to be provided')
            quit(1)
        self.data = {}
        #
        self.LMSync_Timestamp = 0
        self.BackendSync_Timestamp = 0
        for key_id in LM_DeviceGroup.keys_to_store:
            self.data[key_id] = None
        if id is None:
            raise LM_Session_Error('not implemented')
            quit(1)

        else:
            # lets load data from LM
            result = LM_Session.get('/device/groups/' + str(id))
            if result['status'] != 200:
                raise LM_Session_Query_Error('Query error' + result['errmsg'])
                quit(1)
            else:
                for key_id in result['data'].keys():
                    if key_id in LM_DeviceGroup.keys_to_store:
                        self.data[key_id] = result['data'][key_id]
                self.LMSync_Timestamp = int(time.time())

        # now we got copy of data from LM

    def __str__(self):
        ''' human readable serialiation '''
        __header_l1__ = "Data was synced with LM: " + ('Never' if self.LMSync_Timestamp == 0 else (str(time.time() - self.LMSync_Timestamp) + ' seconds ago')) + "\n"
        __header_l2__ = "Data was synced with backend: " + ( 'Never' if self.BackendSync_Timestamp == 0 else (str(time.time() - self.BackendSync_Timestamp) + ' seconds ago') ) + "\n"
        return(__header_l1__ + __header_l2__ + 'Data:\n' + json.dumps(self.data, indent=4))

if __name__ == '__main__':
    quit()
