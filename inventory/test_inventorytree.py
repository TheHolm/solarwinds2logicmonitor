import pytest
import inventory
import devicegroup


class Test_Inventory_Tree:

    def test__init__01(self):
        ''' just check that init can run'''
        inventory.Inventory_Tree()

    def test_add_root_grop(self, Inventory_Tree_Instance):
        it = Inventory_Tree_Instance
        groupdata = {
          "name": "Test",
          "fullPath": "Test",
        }
        g0 = devicegroup.DeviceGroup(data=groupdata)
        it.add_group(g0)
        print(it)

    def test_add_01(self, Inventory_Tree_Instance):
        it = Inventory_Tree_Instance
        groupdata = {
          "name": "Horns and Hooves",
          "fullPath": "Customers/Horns and Hooves",
        }
        g0 = devicegroup.DeviceGroup(data=groupdata)
        with pytest.raises(inventory.Inventory_Query_Error):
            it.add_group(g0)  # should fail as no parent yet.
