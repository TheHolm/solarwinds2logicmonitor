import configparser
import json
import os.path
import os

import pprint

import solarwinds

pp = pprint.PrettyPrinter(indent=2)

config = configparser.ConfigParser(interpolation=None)

config['Solarwinds'] = {}
config['LogicMonitor'] = {}
config['FileTree'] = {}

config.read("config.ini")

try:
    print('Connecting to Solarwinds on ', config['Solarwinds']['URL'])
    solarwinds_connection = solarwinds.Solarwinds_Session(config['Solarwinds']['APIUser'], config['Solarwinds']['APIKey'], config['Solarwinds']['URL'])
except KeyError as E:
    print("URL,APIUser,APIKey need to be defined in [Soalrwinds] secton of config.ini\n", E)
    quit()

# getting list of Nodes

try:
    custom_properties_list = ",N.CustomProperties." + ",N.CustomProperties.".join(json.loads(config['Solarwinds']['CustomPropertyImportList']))
except json.decoder.JSONDecodeError:
    print('Unable to parse CustomPropertyImportList from config.ini. format is CustomPropertyImportList = ["PropertyA","PropertyB"]')
    quit()

custom_properties = json.loads(config['Solarwinds']['CustomPropertyImportList'])

try:
    custom_properties_list = ",N.CustomProperties." + json.loads(config['Solarwinds']['Level1CustomProperty']) + ",N.CustomProperties." + json.loads(config['Solarwinds']['Level2CustomProperty']) + custom_properties_list
    Level1CustomProperty = str(json.loads(config['Solarwinds']['Level1CustomProperty']))
    Level2CustomProperty = str(json.loads(config['Solarwinds']['Level2CustomProperty']))
except KeyError as E:
    print("Level1CustomProperty,Level1CustomProperty need to be defined in [Solarwinds] secton of config.ini\n", E)
    quit()


generic_fields = {"Caption": None,
                  "IPAddress": 'IPv4Address',
                  "SNMPVersion": None}
SNMPv2_fields = {'Community': 'SNMPv2Community',
                 'RWCommunity': 'SNMPv2RWCommunity'}
SNMPv3_fields = {'N.SNMPv3Credentials.Username': "SNMPv3Username",
                 'N.SNMPv3Credentials.PrivacyMethod': 'SNMPv3PrivacyMethod',
                 'N.SNMPv3Credentials.PrivacyKey': 'SNMPv3PrivacyKey',
                 'N.SNMPv3Credentials.AuthenticationMethod': 'SNMPv3AuthenticationMethod',
                 'N.SNMPv3Credentials.AuthenticationKey': 'SNMPv3AuthenticationKey',
                 'N.SNMPv3Credentials.AuthenticationKeyIsPassword': None
                 }

# SNMPv# paramiter needs special handling as Solarwinds changes fien nemase when returning results.
SNMPv3_fields_list = []
SQL_fields_aliases = {}
for field in SNMPv3_fields.keys():
    SNMPv3_fields_list.append(field + " AS " + field.replace('.', '_'))
    SQL_fields_aliases[field.replace('.', '_')] = field

payload_ICMP = {"query": "SELECT " + ','.join(generic_fields.keys()) + custom_properties_list
                + " FROM Orion.Nodes AS N WHERE SNMPVersion = 0"}
payload_SNMPv2 = {"query": "SELECT " + ','.join(generic_fields.keys()) + ',' + ','.join(SNMPv2_fields.keys()) + custom_properties_list
                  + " FROM Orion.Nodes AS N WHERE SNMPVersion = 2"}
payload_SNMPv3 = {"query": "SELECT " + ','.join(generic_fields.keys()) + ',' + ','.join(SNMPv3_fields_list) + custom_properties_list
                  + " FROM Orion.Nodes AS N WHERE SNMPVersion = 3"}
# payload = {"query": "SELECT Uri,Caption,SysName,NodeID FROM Orion.Nodes AS N"}
# print(payload_ICMP)
# print(payload_SNMPv2)
# print(payload_SNMPv3)
# quit()

response_ICMP = solarwinds_connection.post("Query", data=payload_ICMP).json()["results"]
for solarwinds_node in response_ICMP:
    for property in custom_properties:
        if solarwinds_node[property] is None:
            del solarwinds_node[property]
print("Found ", len(response_ICMP), " ICMP nodes")
# pp.pprint(response_ICMP)

response_SNMPv2 = solarwinds_connection.post("Query", data=payload_SNMPv2).json()["results"]
for solarwinds_node in response_SNMPv2:
    if len(solarwinds_node['RWCommunity']) == 0:
        del solarwinds_node['RWCommunity']
    for property in custom_properties:
        if solarwinds_node[property] is None:
            del solarwinds_node[property]

print("Found ", len(response_SNMPv2), "SNMPv2 nodes")
# pp.pprint(response_SNMPv2)

response_SNMPv3 = solarwinds_connection.post("Query", data=payload_SNMPv3).json()["results"]
for solarwinds_node in response_SNMPv3:
    for property in custom_properties:
        if solarwinds_node[property] is None:
            del solarwinds_node[property]
        # translating aliases back.
    for property in list(solarwinds_node.keys()):
        if property in SQL_fields_aliases.keys():
            solarwinds_node[SQL_fields_aliases[property]] = solarwinds_node[property]
            del solarwinds_node[property]

print("Found ", len(response_SNMPv3), "SNMPv3 nodes")
# pp.pprint(response_SNMPv3)

if not (isinstance(response_ICMP, (list,)) and isinstance(response_SNMPv2, (list,)) and isinstance(response_SNMPv3, (list,))):
    print("internal error, solarwinds response to query is not a list ")
    quit(0)
response = response_ICMP + response_SNMPv2 + response_SNMPv3

print("Found ", len(response), "nodes total")

# Building node tree
device_tree = {}
for solarwinds_node in response:
    try:
        device_tree[solarwinds_node[Level1CustomProperty]][solarwinds_node[Level2CustomProperty]][solarwinds_node['Caption']] = solarwinds_node
    except KeyError:
        if solarwinds_node[Level1CustomProperty] not in device_tree.keys():
            device_tree[solarwinds_node[Level1CustomProperty]] = {}
        if solarwinds_node[Level2CustomProperty] not in device_tree[solarwinds_node[Level1CustomProperty]].keys():
            device_tree[solarwinds_node[Level1CustomProperty]][solarwinds_node[Level2CustomProperty]] = {}
        device_tree[solarwinds_node[Level1CustomProperty]][solarwinds_node[Level2CustomProperty]][solarwinds_node['Caption']] = solarwinds_node
# pp.pprint(device_tree)

# writing to files ( I know that it can be done in previos loop. But I may whant to do something with device_tree in between)
i = 0
for Level1 in device_tree.keys():
    for Level2 in device_tree[Level1].keys():
        for NodeName in device_tree[Level1][Level2].keys():
            node_data = device_tree[Level1][Level2][NodeName]
            # create config isinstance
            node_config = configparser.ConfigParser()
            node_config['node'] = {}
            if int(node_data['SNMPVersion']) not in [0, 2, 3]:
                print("Warning: node ", NodeName, "uses SNMP version", node_data['SNMPVersion'])
                continue
            if int(node_data['SNMPVersion']) == 0:
                node_config['ICMP_Ping'] = {}
            if int(node_data['SNMPVersion']) == 2:
                node_config['SNMPv2'] = {}
            if int(node_data['SNMPVersion']) == 3:
                node_config['SNMPv3'] = {}

            # node_config['SNMPv2'] = {}
            # node_config['SNMPv3'] = {}

            """
            generic_fields
            SNMPv2_fields
            SNMPv3_fields
            custom_properties
            """
            for item in node_data.keys():
                if item in generic_fields.keys():
                    if generic_fields[item] is not None:
                        node_config['node'][generic_fields[item]] = str(node_data[item])
                if item in custom_properties:
                    node_config['node'][item] = str(node_data[item])
                if item in SNMPv2_fields.keys():
                    if SNMPv2_fields[item] is not None:
                        try:
                            node_config['SNMPv2'][SNMPv2_fields[item]] = str(node_data[item])
                        except Exception as E:
                            print('Exception:', E)
                            print('NodeName',  NodeName, "\nitem ", item, '\nSNMPv2_fields[item]', SNMPv2_fields[item], '\nstr(node_data[item]', str(node_data[item]), "\n")

                if item in SNMPv3_fields.keys():
                    if SNMPv3_fields[item] is not None:
                        node_config['SNMPv3'][SNMPv3_fields[item]] = str(node_data[item])
            if NodeName == 'Montessori_burwoodvoice_adsl ':
                pp.pprint(node_data)
                pp.pprint(generic_fields)
                pp.pprint(custom_properties)
                pp.pprint(SNMPv2_fields)
                pp.pprint(SNMPv3_fields)
            # finally writing ini file to disk
            file_path = os.path.join("./device-tree/", str(Level1), str(Level2), str(NodeName.replace('/', '-')) + '.ini')
            # print("Trying to write ", file_path)
            try:
                with open(file_path, 'w') as configfile:
                    node_config.write(configfile)
            except FileNotFoundError:
                if not os.path.isdir(os.path.join("./device-tree/", str(Level1))):
                    os.mkdir(os.path.join("./device-tree/", str(Level1)))
                    print("Created :", os.path.join("./device-tree/", str(Level1)))
                if not os.path.isdir(os.path.join("./device-tree/", str(Level1), str(Level2))):
                    os.mkdir(os.path.join("./device-tree/", str(Level1), str(Level2)))
                    print("Created :", os.path.join("./device-tree/", str(Level1), str(Level2)))
            finally:
                with open(file_path, 'w') as configfile:
                    node_config.write(configfile)
                    i = i + 1


print(i, 'config files was writen')
quit()
