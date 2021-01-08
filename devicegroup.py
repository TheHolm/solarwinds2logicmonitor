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
                     'defaultCollectorGroupId',
                     'description',
                     'extra',
                     'fullPath',
                     'name',
                     'disableAlerting',
                     'groupType',
                     'subGroups',
                     )

    def __init__(self, id=None, fullPath="", data={}):
        '''  Just populate file structure. id and fullPath has priority over values in data'''
        # Init vars
        self.data = {}
        for key_id in DeviceGroup.keys_to_store:
            self.data[key_id] = None

        for key_id in data.keys():
        #    if key_id in DeviceGroup.keys_to_store:
                self.data[key_id] = data[key_id]

        if id is not None:
            self.data['id'] = id
        if fullPath != "":
            self.data['fullPath'] = fullPath

        if self.data['id'] is None and self.data['fullPath'] == "":
            raise DeviceGroup_Error('"Id" or "fulPath" have to be provided as paramiters or as part of "data"')
            quit(1)

        self.data['LMSync_Timestamp'] = 0
        self.data['FSSync_Timestamp'] = 0
        self.data['Update_Timestamp'] = int(time.time())

    def clone(self, source):
        '''just copied data to self from other instance of same class'''
        # should I use deep copy instaed?
        if issubclass(source.__class__, DeviceGroup):
            self.data = source.data
        else:
            raise DeviceGroup_Error('Expected subclass of <class DeviceGroup>, got {}.'.format(type(source)))

    def __update_data__(self, source):
        '''copy data to self from source for keys in "DeviceGroup.keys_to_store" list'''
        for key_id in source.keys():
            if key_id in DeviceGroup.keys_to_store:
                self.data[key_id] = source[key_id]

    def __str__(self):
        ''' human readable serialiation '''
        __header_l1__ = "Data was synced with LM: " + ('Never' if self.data['LMSync_Timestamp'] == 0 else (str(time.time() - self.data['LMSync_Timestamp']) + ' seconds ago')) + "\n"
        __header_l2__ = "Data was synced with file system backend: " + ('Never' if self.data['FSSync_Timestamp'] == 0 else (str(time.time() - self.data['FSSync_Timestamp']) + ' seconds ago')) + "\n"
        return(__header_l1__ + __header_l2__ + 'Data:\n' + json.dumps(self.data, indent=4))

    def __eq__(self, other):
        ''' Not implemented '''
        raise DeviceGroup_Error(" == overload is not implemened")
        pass


if __name__ == '__main__':
    quit()
