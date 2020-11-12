import pytest
import configparser
import json


@pytest.fixture(scope="session")
def sandbox_login_details():
    config = configparser.ConfigParser(interpolation=None)
    config.read("config.ini")
    login_details = {'access_id': json.loads(config['LogicMonitor']['access_id']),
                     'access_key': json.loads(config['LogicMonitor']['access_key']),
                     'company': json.loads(config['LogicMonitor']['company'])}
    return login_details
