import os
import time
import json

import fs_backend


class FS_Session:

    def __init__(self, root_path):
        ''' does not do much , just check that path exisits '''

        if root_path is None:
            raise fs_backend.FS_Session_Error("Empty root_path")

        self.root_path = str(root_path)
        if not os.access(self.root_path, os.W_OK):
            raise fs_backend.FS_Session_Error("Can't open root dir " + self.root_path + " for writing")

    def __call_API__(self, httpMethod, resourcePath, payload='', params='', session_timeout=5):
        ''' Make a call to LM API endpoint returns json'''
        ''' payload, params - can be and should be a dicitionary '''
        '''
        try:
            self.response = self.SessionId.request(httpMethod, self.baseURL+resourcePath, params=params, data=payload, headers=headers, timeout=session_timeout)
        except urllib3.exceptions.ReadTimeoutError as e:
            raise lm_backend.LM_Session_Database_Error('Connection timeout' + str(e))
        else:
            self.response.raise_for_status()
        return(self.response.json())
        '''
        pass

    def get(self, resourcePath, payload='', params='', session_timeout=10):
        ''' Simple wrper for call_API, saves you affor to passing GET to it'''
        pass

    def post(self, resourcePath, payload='', params='', session_timeout=10):
        ''' Simple wrper for __call_API__, saves you affor to passing POST to it'''
        pass

    def patch(self, resourcePath, payload='', params='', session_timeout=10):
        ''' Simple wrper for __call_API__, saves you affor to passing PATCH to it'''
        pass

    def delete(self, resourcePath, payload='', params='', session_timeout=10):
        ''' Simple wrper for __call_API__, saves you affor to passing DELETE to it'''
        pass


if __name__ == '__main__':
    quit()
