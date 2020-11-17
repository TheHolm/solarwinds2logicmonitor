import pytest
import inventory
import devicegroup


class Test_Inventory_Tree:

    def test__init__01(self):
        ''' just check that init can run'''
        inventory.Inventory_Tree()

    # fullPAth based adds
    def test_add_group_01(self, Inventory_Tree_Instance):
        ''' Adding root group by full path'''
        it = Inventory_Tree_Instance
        groupdata = {
          "id": 1000,
          "name": "Customers",
          "fullPath": "Customers",
        }
        g0 = devicegroup.DeviceGroup(data=groupdata)
        it.add_group(g0)
        print(it, g0)

    def test_add_group_02(self, Inventory_Tree_Instance):
        ''' fail if fullPath ended on /'''
        it = Inventory_Tree_Instance
        groupdata = {
          "name": "NoGroup",
          "fullPath": "NoGroup/",
        }
        g0 = devicegroup.DeviceGroup(data=groupdata)
        with pytest.raises(inventory.Inventory_Query_Error):
            it.add_group(g0)  # should fail as no parent yet.
        print(it, g0)

    def test_add_group_04(self, Inventory_Tree_Instance):
        ''' fail if name fullpPath mismatch '''
        it = Inventory_Tree_Instance
        groupdata = {
            "name": "Hooves and Horns",
            "fullPath": "Customers/Horns and Hooves",
        }
        g0 = devicegroup.DeviceGroup(data=groupdata)
        with pytest.raises(inventory.Inventory_Query_Error):
            it.add_group(g0)  # should fail as no parent yet.
        print(it, g0)

    def test_add_group_03(self, Inventory_Tree_Instance):
        ''' fail when no parent can be found '''
        it = Inventory_Tree_Instance
        groupdata = {
          "name": "Horns and Hooves",
          "fullPath": "NoGroup/Horns and Hooves",
        }
        g0 = devicegroup.DeviceGroup(data=groupdata)
        with pytest.raises(inventory.Inventory_Query_Error):
            it.add_group(g0)  # should fail as no parent yet.
        print(it, g0)

    def test_add_group_07(self, Inventory_Tree_Instance):
        ''' fail when parentId missmach '''
        it = Inventory_Tree_Instance
        groupdata = {
          "parentId": 1234,
          "name": "Horns and Hooves",
          "fullPath": "Customers/Horns and Hooves",
        }
        g0 = devicegroup.DeviceGroup(data=groupdata)
        with pytest.raises(inventory.Inventory_Query_Error):
            it.add_group(g0)  # should fail as no parent yet.
        print(it, g0)

    def test_add_group_05(self, Inventory_Tree_Instance):
        ''' succesful add of child group with updates'''
        it = Inventory_Tree_Instance
        groupdata = {
          "id": 2000,
          "name": None,
          "fullPath": "Customers/Horns and Hooves",
        }
        g0 = devicegroup.DeviceGroup(data=groupdata)
        it.add_group(g0)  # should fail as no parent yet.
        assert g0.data['parentId'] == 1000
        assert g0.data['name'] == 'Horns and Hooves'
        print(it, g0)

    def test_add_group_06(self, Inventory_Tree_Instance):
        ''' succesful add of child group without updates'''
        it = Inventory_Tree_Instance
        groupdata = {
          "id": None,
          "name": None,
          "fullPath": "Customers/Horns and Hooves 2",
        }
        g0 = devicegroup.DeviceGroup(data=groupdata)
        it.add_group(g0, doNotUpdate=True)  # should fail as no parent yet.
        assert g0.data['parentId'] is None
        assert g0.data['name'] is None
        print(it, g0)

    def test_add_group_08(self, Inventory_Tree_Instance):
        ''' fail tryinf to add group with same iD '''
        it = Inventory_Tree_Instance
        groupdata = {
          "id": 2000,
          "name": None,
          "fullPath": "Customers/Horns and Hooves 3",
        }
        g0 = devicegroup.DeviceGroup(data=groupdata)
        with pytest.raises(inventory.Inventory_Query_Error):
            it.add_group(g0)  # should fail as no parent yet.
        print(it, g0)

    def test_add_group_09(self, Inventory_Tree_Instance):
        ''' fail tryinf to add group with same path '''
        it = Inventory_Tree_Instance
        groupdata = {
          "id": None,
          "name": None,
          "fullPath": "Customers/Horns and Hooves",
        }
        g0 = devicegroup.DeviceGroup(data=groupdata)
        with pytest.raises(inventory.Inventory_Query_Error):
            it.add_group(g0)  # should fail as no parent yet.
        print(it, g0)
