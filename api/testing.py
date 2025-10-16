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
            "user": UNAME,
            "password": PWORD},
        "id": 1
    })
print(json.dumps(r.json(), indent=4, sort_keys=True))
AUTHTOKEN = r.json()["result"]

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
    print(json.dumps(problems.json(), indent=4, sort_keys=True))
    return problems.json()["result"]

get_all_problems()
