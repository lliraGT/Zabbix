# vicente.rodriguez@millicom.com / Millicom TTC
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import requests
import json
#from datetime import datetime, timedelta

ZABBIX_API_URL = "https://172.20.6.42/zabbix/api_jsonrpc.php"
UNAME = "apizabbix"
PWORD = "TigoPanama2023$"

r = requests.post(ZABBIX_API_URL, verify=False,
    json={
        "jsonrpc": "2.0",
        "method": "user.login",
        "params": {
            "username": UNAME,
            "password": PWORD},
        "id": 1
    })
#print(json.dumps(r.json(), indent=4, sort_keys=True))
print(r.json())
AUTHTOKEN = r.json()["result"]

def get_triggers_in_problems():
    problems = requests.post(ZABBIX_API_URL, verify=False,
    json = {
        "jsonrpc": "2.0",
        "method": "trigger.get",
        "params": {
            "output": [
                "triggerid",
                "description",
                "priority"
            ],
            "filter": {
                "value": 1
            },
            "sortfield": "triggerid",
            "sortorder": "ASC"
        },
        "auth": AUTHTOKEN,
        "id": 1
    })

    return problems.json()["result"]

def get_all_problems():
    problems = requests.post(ZABBIX_API_URL, verify=False,
    json={
        "jsonrpc": "2.0",
            "method": "problem.get",
            "params": {
                "output": "extend",
                "recent": "true",
                "output": ["objectid",  "eventid", "severity", "name", "acknowledged", "clock", "r_clock"],
                "sortfield": ["eventid"],
                "sortorder": "ASC"
            },
            "id": 1,
            "auth": AUTHTOKEN
    })
    return problems.json()["result"]

def get_problem(eventid):
    print(type(eventid))
    print(eventid)
    problems = requests.post(ZABBIX_API_URL,verify=False,
    json={
        "jsonrpc": "2.0",
            "method": "problem.get",
            "params": {
                "output": "extend",
                "eventid": eventid,
                "recent": "true",
                "output": ["objectid",  "eventid", "severity", "name", "acknowledged", "clock", "r_clock"],
                "sortfield": ["eventid"],
                "sortorder": "ASC"
            },
            "id": 1,
            "auth": AUTHTOKEN
    })

    return problems.json()["result"]

def get_events(eventid):
    events = requests.post(ZABBIX_API_URL,verify=False,
    json = {
        "jsonrpc": "2.0",
        "method": "event.get",
        "params": {
            "output": "extend",
            "eventids": eventid,
            "selectHosts": [ "host", "name", "description"],
            "output": ["eventid", "value"],
            "sortorder": "DESC"
        },
        "auth": AUTHTOKEN,
        "id": 1
    })

    return events.json()["result"]

def get_groups(hostid):
    groups = requests.post(ZABBIX_API_URL,verify=False,
    json = {
        "jsonrpc": "2.0",
        "method": "hostgroup.get",
        "params": {
            "hostids": hostid,
            "output": ["name", "hostid", "groupid"],
        },
        "auth": AUTHTOKEN,
        "id": 1
    })
    return groups.json()["result"]
