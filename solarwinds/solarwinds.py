import requests
import re
import ipaddress
import json

from requests.packages.urllib3.exceptions import InsecureRequestWarning
import urllib.parse
import urllib3.exceptions

import ssl
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.poolmanager import PoolManager
from requests.packages.urllib3.util import ssl_


class TlsAdapter(HTTPAdapter):

    def __init__(self, ssl_options=0, **kwargs):
        self.ssl_options = ssl_options
        super(TlsAdapter, self).__init__(**kwargs)

    def init_poolmanager(self, *pool_args, **pool_kwargs):
        ctx = ssl_.create_urllib3_context(ssl.PROTOCOL_TLS)
        ctx.minimum_version = ssl.TLSVersion.TLSv1_1
        ctx.maximum_version = ssl.TLSVersion.TLSv1_1
        # extend the default context options, which is to disable ssl2, ssl3
        # and ssl compression, see:
        # https://github.com/shazow/urllib3/blob/6a6cfe9/urllib3/util/ssl_.py#L241
        ctx.options |= self.ssl_options
        self.poolmanager = PoolManager(*pool_args,
                                       ssl_context=ctx,
                                       **pool_kwargs)


class Solarwinds_Session:

    def __init__(self, username, password, baseURL):

        if password is None or username is None or baseURL is None:
            raise Exception("Empty URL, username or password")

        self.baseURL = baseURL + "/SolarWinds/InformationService/v3/Json/"

        # login to Soalrwinds
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
        requests.packages.urllib3.disable_warnings()
        # starting session
        self.SessionId = requests.Session()
        self.SessionId.headers.update({'Content-Type': 'application/json'})
        self.SessionId.auth = (username, password)
        adapter = TlsAdapter(ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_3)
        self.SessionId.mount("https://", adapter)

        # Check is account works and have NodeMangemt Rights.
        payload = "{ \"query\" : \"SELECT A.AccountID,A.AllowNodeManagement,A.LastLogin FROM Orion.Accounts AS A WHERE A.AccountID = '"+username+"'\" }"

        self.response = self.SessionId.post(self.baseURL+"Query", data=payload, verify=False, timeout=5)

        # print(self.response.request.headers,"\n\nBody:")
        # print(self.response.request.body,"\n\n")
        # print(self.response.text,"\n\n\n")

        self.response.raise_for_status()

        if self.response.json()['results'][0]['AllowNodeManagement'] != "Y":
            raise Exception("User " + username + " has no Node Management rights on Solarwinds\n" + self.response.json())

    def get(self, sub_path="", data={}, session_timeout=10, raise_for_timeout=True):
        try:
            self.response = self.SessionId.get(self.baseURL+sub_path, json=data, timeout=session_timeout)
        except urllib3.exceptions.ReadTimeoutError as e:
            if raise_for_timeout:
                raise(e)
            else:
                self.response = None
        else:
            self.response.raise_for_status()
        return(self.response)

    def post(self, sub_path="", data={}, session_timeout=10, raise_for_timeout=True):
        try:
            self.response = self.SessionId.post(self.baseURL+sub_path, json=data, timeout=session_timeout)
        except urllib3.exceptions.ReadTimeoutError as e:
            if raise_for_timeout:
                raise(e)
            else:
                self.response = None
        else:
            self.response.raise_for_status()
        return(self.response)

    def patch(self, sub_path="", data={}, session_timeout=10):
        self.response = self.SessionId.patch(self.baseURL+sub_path, json=data, timeout=session_timeout)
        self.response.raise_for_status()
        return(self.response)


class Solarwinds_Node:

    def __init__(self, solarwinds_session, NodeID=None, NodeIPAddress=None, Type=None, Caption=None, EngineID=3):
        # if NodeID is not provided will create new node in solarwinds
        # otherwise will quer solarwinds to populate values.
        # Caption - str
        # NodeIPAddress - str or IPaddress type.
        # Type - "ICMP" or "SNMP Profile name (SNMP is not implemented)"
        # EngineID where to add node

        self.NodeID = NodeID
        self.uri = None

        if NodeID is None:
            if NodeIPAddress is None:
                # must get at least IP address
                return(None)
            else:
                if isinstance(NodeIPAddress, str):
                    try:
                        self.IPAddress = ipaddress.IPv4Address(NodeIPAddress)
                    except (ipaddress.AddressValueError, ipaddress.NetmaskValueError):
                        # this one will fial again if address is wrong
                        try:
                            self.IPAddress = ipaddress.IPv6Address(NodeIPAddress)
                        except (ipaddress.AddressValueError, ipaddress.NetmaskValueError):
                            # fail to conver address to IPv4 or IPv6Address
                            return(None)
                elif not isinstance(NodeIPAddress, (ipaddress.IPv4Address, ipaddress.IPv6Address)):
                    # provided paramiter is wrong type
                    return(None)
            # By now we at least know IP Address of the node
            self.caption = str(Caption) if Caption is not None else ("Node - " + self.IPAddress.compressed)

            if not isinstance(solarwinds_session, Solarwinds_Session):
                raise Exception("solarwinds_session must be of Type solarwinds.Solarwinds_Session")
            self.solarwinds_session = solarwinds_session

            # lets try to add node
            node_data = {}
            node_data['Caption'] = self.caption
            node_data['EngineID'] = int(EngineID)
            node_data['IPAddress'] = self.IPAddress.compressed
            node_data['IPAddressType'] = "IPv4" if isinstance(self.IPAddress, ipaddress.IPv4Address) else "IPv6"
            if Type in (None, "ICMP"):
                node_data['ObjectSubType'] = "ICMP"
                node_data['SNMPVersion'] = 0
            else:
                raise Exception("Adding SNMP nodes is not yet implemented")

            response = self.solarwinds_session.post("Create/Orion.Nodes", data=node_data)
            response.raise_for_status()
            if response.text != "":
                self.uri = json.loads(response.text)
                self.NodeID = re.search(r'^swis://monitornpm./Orion/Orion.Nodes/NodeID=(\d+)$', self.uri)
                if self.NodeID is not None:
                    self.NodeID = int(self.NodeID[1])
                    # print('Node added ', end=', ', flush=True,  sep='')
                else:
                    raise Exception("Unexpected responce from Solarwinds" + str(response.text))
                # print(response.text, json.loads(response.json))
            else:
                raise Exception("Solarwind is not happy " + str(response.text))

        else:
            if Caption is not None or NodeIPAddress is not None or Type is not None:
                # cant specify detais when accessinf already provisioned node.
                return(None)

    def SetCustomProperties(self, CustomProperties):
        # Custom Properties are in dict { "Alert_Customer": "No", "Alert_HelpDesk": "No", }
        if not isinstance(CustomProperties, dict):
            raise Exception("CustomProperties must be of type <dict> ")
        response = self.solarwinds_session.post(self.uri+'/CustomProperties', CustomProperties)
        response.raise_for_status()

    def SetPollers(self, Pollers, RemoveExtra=True):
        # adding Pollers to node from dictionary, { "N.ResponseTime.ICMP.Native": True, "N.ResponseTime.ICMP.Native": True }
        # if RemoveExtra=True than it will also remove all pollers wich are not listed.
        if not isinstance(Pollers, dict):
            raise Exception("CustomProperties must be of type <dict> ")
        target_pollers_set = Pollers

        payload = {"query": "SELECT Uri,PollerType,p.Enabled FROM Orion.Pollers AS P WHERE P.NetObjectID = " + str(self.NodeID)}
        response = self.solarwinds_session.post("Query", data=payload)
        results = response.json()["results"]
        pollers_to_enable = []
        pollers_to_disable = []
        pollers_to_remove = []
        for attached_poller in results:
            if attached_poller['PollerType'] in target_pollers_set:
                if attached_poller['Enabled'] != target_pollers_set[attached_poller['PollerType']]:
                    if target_pollers_set[attached_poller['PollerType']]:
                        pollers_to_enable.append(attached_poller['Uri'])
                    else:
                        pollers_to_disable.append(attached_poller['Uri'])
            else:  # attached poller are not in the list, need to be removed.
                pollers_to_remove.append(attached_poller['Uri'])
        if len(pollers_to_enable) > 0:
            payload = {"uris": pollers_to_enable, "properties": {'Enabled': True}}
            response = self.solarwinds_session.post('BulkUpdate', data=payload)
            # print('Enabled ', len(pollers_to_enable), ' poller(s)', end=', ', flush=True, sep='')
        if len(pollers_to_disable) > 0:
            payload = {"uris": pollers_to_disable, "properties": {'Enabled': False}}
            response = self.solarwinds_session.post('BulkUpdate', data=payload)
            # print('Disabled ', len(pollers_to_disable), ' poller(s)', end=', ', flush=True, sep='')
        if len(pollers_to_remove) > 0 and RemoveExtra:
            payload = {"uris": pollers_to_remove}
            response = self.solarwinds_session.post('BulkDelete', data=payload)
            # print('Removed ', len(pollers_to_remove), ' poller(s)', end=', ', flush=True, sep='')
        # Checking for missing pollers.
        for requred_poller in target_pollers_set.keys():
            if not any(p['PollerType'] == requred_poller for p in results):
                payload = {
                    "PollerType": requred_poller,
                    "NetObject": "N:" + str(self.NodeID),
                    "NetObjectType": "N",
                    "NetObjectID": int(self.NodeID),
                    "Enabled": target_pollers_set[requred_poller]
                }
                response = self.solarwinds_session.post("Create/Orion.Pollers", data=payload)




    def get_data(self):
        # query data from solarwinds and poulate local variables
        # (not sure that function is requred at all)

        if self.NodeID is not None:
            payload = {'query': 'SELECT Uri,Caption,SysName,NodeID FROM Orion.Nodes AS N WHERE N.NodeID = ' + str(self.NodeID)}
            response = solarwinds_connection.post("Query", data=payload)
            if len(response.json()["results"]) == 1:
                self.uri = response.json()['results']['Uri']
                self.caption = response.json()['results']['Caption']


def Delete_Stale_Nodes(solarwinds_connection):
        payload = {"query": "SELECT N.Uri,N.SysName,N.NodeID,N.Caption,N.LastSystemUpTimePollUtc,N.StatusDescription,N.Status FROM Orion.Nodes AS N WHERE  LastSystemUpTimePollUtc <  '2018-11-01' AND ( Status = 2 ) ORDER BY LastSystemUpTimePollUtc"}
        response = solarwinds_connection.post("Query", data=payload)
        i = 0
        nodes_to_delete = []
        for solarwinds_node in response.json()["results"]:
            i += 1
            payload = {"uris": [solarwinds_node['Uri']]}
            response = solarwinds_connection.post("BulkDelete", data=payload)
            print(i, solarwinds_node['SysName'], '-', solarwinds_node['Caption'], 'was deleted')
            # print(i, solarwinds_node['LastSystemUpTimePollUtc'], solarwinds_node['SysName'], solarwinds_node['Caption'])


if __name__ == '__main__':
    quit()
