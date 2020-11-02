import time
import json

import logicmonitor


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
            raise logicmonitor.LM_Session_Error('ether id or filePath need to be provided')
            quit(1)
        self.data = {}
        #
        self.LMSync_Timestamp = 0
        self.BackendSync_Timestamp = 0
        for key_id in LM_DeviceGroup.keys_to_store:
            self.data[key_id] = None
        if id is None:
            raise logicmonitor.LM_Session_Error('not implemented')
            quit(1)

        else:
            # lets load data from LM
            result = LM_Session.get('/device/groups/' + str(id))
            if result['status'] != 200:
                raise logicmonitor.LM_Session_Query_Error('Query error' + result['errmsg'])
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
        __header_l2__ = "Data was synced with backend: " + ('Never' if self.BackendSync_Timestamp == 0 else (str(time.time() - self.BackendSync_Timestamp) + ' seconds ago')) + "\n"
        return(__header_l1__ + __header_l2__ + 'Data:\n' + json.dumps(self.data, indent=4))


if __name__ == '__main__':
    quit()
