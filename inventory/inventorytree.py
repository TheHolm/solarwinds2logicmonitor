import sqlite3  # used mostly to speedup searches and introduce more bugs

import devicegroup
import inventory


class Inventory_Tree:

    def __init__(self):
        ''' Just init in-maemory database and some variables.'''
        self.db = sqlite3.connect(':memory:')

        # lets init tables.
        c = self.db.cursor()
        ''' key - in DB id. It is local for DB and only stored in memory.
         id  - External group id - corresponds to on disk oor Logic monitor ids. Not same as key.
         parentKey - in DB key of parrent group. -1 root group.
         parentID - External parent group id.
         name TEXT - Just group name - mandatory
         fullPath TEXT - full path = path from root folder + name '''
        c.execute('''CREATE TABLE groups
                     (key int INTEGER PRIMARY KEY,
                      id INT CHECK ( id > 0 or id IS NULL ),
                      parentKey INT NOT NULL,
                      parentId INT,
                      name TEXT ,
                      fullPath TEXT CHECK (  NOT ( fullPath IS NULL AND name IS NULL )  ) )''')
        c.execute('CREATE INDEX IDX_id ON groups (id)')
        c.execute('CREATE INDEX IDX_parentKey ON groups (parentKey)')
        c.close()
        self.db.commit()
        self.tree = []
        # adding root

    def add_group(self, device_group, parentKey=None):
        '''Add a group database of type device.DeviceGroup, code will try it best to find parrents '''
        # device_group  + parrentKey should have enogh information to locate group parent
        # fullpath - will extract group name ant try to find parrent based on rest of the path
        # Name + parentID or parentKey. If both are Nane than parent is root.
        # Name, id=None, parentKey=None, parentID=None, fullpath=None
        if not issubclass(device_group.__class__, devicegroup.DeviceGroup):
            raise inventory.Inventory_Query_Error('device_grop must be sublass of devicegroup.DeviceGroup. Got ' + str(type(device_group)))
            quit(1)
        g_fullPath = device_group.data['fullPath'] if 'fullPath' in device_group.data else None
        g_name = device_group.data['name'] if 'name' in device_group.data else None

        if g_fullPath not in (None, ''):

            path_list = g_fullPath.split('/')
            name_from_path = path_list[-1]
            if name_from_path == '':
                raise inventory.Inventory_Query_Error('device_group.fullPath can\'t ends with "/"')
                quit(1)
            if g_name in (None, ''):
                device_group.data['name'] = name_from_path
            elif name_from_path != g_name:
                raise inventory.Inventory_Query_Error('device_group.name (' + str(g_name) + ' does not match'
                                                      + 'name derived from device_group.fullPath (' + str(g_fullPath) + ')')
                quit(1)
            if len(path_list) == 1:
                # parent is root.
                parentKey = -1
            else:
                # let's try to find parent based on fullPath
                parent_path = '/'.join(path_list[:-1])
                c = self.db.cursor()
                c.execute('SELECT * FROM groups WHERE fullPath = ? ', (parent_path,))
                results = c.fetchall()  # rowcount() is not fun to use
                if len(results) < 1:
                    # parent not found
                    raise inventory.Inventory_Query_Error('Parent of device_group.name (' + g_fullPath + ') was not found in database')
                    quit(1)
                elif len(results) > 1:
                    # multiple parents found - it seems to be database corruption
                    raise inventory.Inventory_Internal_Error('fullPath search of parent returned multiple values. It should not be possible')
                    quit(1)
                    pass
                else:
                    # it should be only 1, I hope len() only returns int.
                    print(results)
                    pass
        c = self.db.cursor()
        c.execute('INSERT INTO groups (id,parentKey, parentId, name, fullPath ) VALUES (NULL, ? , NULL , ? , ? ) ', (parentKey, g_name, g_fullPath))
        # c.lastrowid


    def get_group(self, ):
        ''' returns devicegroup instance, if it can find it'''
        pass

    def del_group(self):
        pass

    def __str__(self):
        c = self.db.cursor()
        c.execute('SELECT * FROM groups')
        return ( "DB dump" + str(c.fetchall()))
