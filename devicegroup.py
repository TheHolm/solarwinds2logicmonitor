import time
import json


class DeviceGroup_Error(Exception):
    """Base class for other exceptions"""
    pass


class DeviceGroup:
    ''' represent device group in LM or folder on disk, skeleton type got extened in "backend" modules '''
    keys_to_store = ('id',
                     'parentId',
                     'customProperties',
                     'defaultCollectorId',
                     'description',
                     'extra',
                     'fullPath',
                     'name')

    def __init__(self, id=None, fullPath="", data={}):
        '''  Just populate file structure'''
        # Init vars
        self.id = id
        self.fullPath = fullPath
        self.LMSync_Timestamp = 0
        self.BackendSync_Timestamp = 0
        self.Update_Temestamp = time.time()
        self.data = {}
        for key_id in DeviceGroup.keys_to_store:
            self.data[key_id] = None

        for key_id in data.keys():
            if key_id in DeviceGroup.keys_to_store:
                self.data[key_id] = data[key_id]

    def __str__(self):
        ''' human readable serialiation '''
        __header_l1__ = "Data was synced with LM: " + ('Never' if self.LMSync_Timestamp == 0 else (str(time.time() - self.LMSync_Timestamp) + ' seconds ago')) + "\n"
        __header_l2__ = "Data was synced with backend: " + ('Never' if self.BackendSync_Timestamp == 0 else (str(time.time() - self.BackendSync_Timestamp) + ' seconds ago')) + "\n"
        return(__header_l1__ + __header_l2__ + 'Data:\n' + json.dumps(self.data, indent=4))


if __name__ == '__main__':
    quit()
