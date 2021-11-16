import requests
import urllib3.exceptions

import base64
import time
import hashlib
import hmac

import json

from time import sleep

import lm_backend


class API_Session:

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

        # Check is account works and have NodeMangemt Rights.
        result = self.__call_API__('GET', '/device/devices', params={'size': 1})
        if result['status'] != 200:
            raise lm_backend.LM_Session_Error(str(result))

    def __call_API__(self, httpMethod, resourcePath, payload='', params='', session_timeout=5):
        ''' Make a call to LM API endpoint returns json'''
        ''' payload, params - can be and should be a dicitionary '''

        if httpMethod not in ('GET', 'POST', 'PATCH', 'DELETE'):
            raise lm_backend.LM_Session_Error("Only 'GET', 'PUT', 'PATCH' requests are supported")

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
                   'Accept': 'application/json',
                   'X-Version': '2',
                   'Authorization': auth_header}

        # FIXME: Need add check to fail if sitting in rate limited state for to many round.
        rate_limited = True
        try:
            while rate_limited:
                self.response = self.SessionId.request(httpMethod, self.baseURL+resourcePath, params=params, data=payload, headers=headers, timeout=session_timeout)
                if (int(self.response.status_code) == 429):
                    sleep(1)
                else:
                    rate_limited = False
        except urllib3.exceptions.ReadTimeoutError as e:
            raise lm_backend.LM_Session_Database_Error('Connection timeout' + str(e))
        else:
            # self.response.raise_for_status() # with APIv2 even 404 sometemes is OK.
            pass

        response = dict()
        response['data'] = self.response.json()
        if int(self.response.status_code) != 200:  # need to check what kind of 404 is that
            response['status'] = response['data']['errorCode']
            response['errmsg'] = response['data']['errorMessage']
        else:
            response['status'] = int(self.response.status_code)
            response['errmsg'] = 'OK'
        response['headers'] = dict(self.response.headers)
        # know that coder above is calling for truoble as Headers not always can be represnted as dict.  But LM respones seems to be does not cause any troubles.
        return(response)

    def get(self, resourcePath, payload='', params='', session_timeout=10):
        ''' Simple wrper for call_API, saves you affor to passing GET to it'''
        return(self.__call_API__('GET', resourcePath, payload=payload, params=params, session_timeout=session_timeout))

    def post(self, resourcePath, payload='', params='', session_timeout=10):
        ''' Simple wrper for __call_API__, saves you affor to passing POST to it'''
        return(self.__call_API__('POST', resourcePath, payload=payload, params=params, session_timeout=session_timeout))

    def patch(self, resourcePath, payload='', params='', session_timeout=10):
        ''' Simple wrper for __call_API__, saves you affor to passing PATCH to it'''
        return(self.__call_API__('PATCH', resourcePath, payload=payload, params=params, session_timeout=session_timeout))

    def delete(self, resourcePath, payload='', params='', session_timeout=10):
        ''' Simple wrper for __call_API__, saves you affor to passing DELETE to it'''
        return(self.__call_API__('DELETE', resourcePath, payload=payload, params=params, session_timeout=session_timeout))


if __name__ == '__main__':
    quit()
