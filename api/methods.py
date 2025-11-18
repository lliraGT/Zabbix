# vicente.rodriguez@millicom.com / Millicom TTC
# Adapted for Slack integration
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
import requests
import json

# Zabbix API Configuration
ZABBIX_API_URL = "https://172.22.137.204:31080/api_jsonrpc.php"
API_TOKEN = "f299a2249a54dbe788431ba07f103cd114a317315af4376af66b60518fc586db"

# Authenticate to Zabbix API
AUTHTOKEN = API_TOKEN
# Autenticación con API Token Completada

def get_triggers_in_problems():
    """Get active triggers (problems) from Zabbix"""
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
    """Get all recent problems from Zabbix"""
    problems = requests.post(ZABBIX_API_URL, verify=False,
    json={
        "jsonrpc": "2.0",
        "method": "problem.get",
        "params": {
            "recent": True,
            "output": ["objectid", "eventid", "severity", "name", "acknowledged", "clock", "r_clock"],
            "sortfield": ["eventid"],
            "sortorder": "ASC"
        },
        "id": 1,
        "auth": AUTHTOKEN
    })
    return problems.json()["result"]

def get_problem(eventid):
    """Get specific problem by event ID"""
    print(type(eventid))
    print(eventid)
    problems = requests.post(ZABBIX_API_URL, verify=False,
    json={
        "jsonrpc": "2.0",
        "method": "problem.get",
        "params": {
            "eventid": eventid,
            "recent": True,
            "output": ["objectid", "eventid", "severity", "name", "acknowledged", "clock", "r_clock"],
            "sortfield": ["eventid"],
            "sortorder": "ASC"
        },
        "id": 1,
        "auth": AUTHTOKEN
    })
    return problems.json()["result"]

def get_events(eventid):
    """Get event details including host information"""
    events = requests.post(ZABBIX_API_URL, verify=False,
    json = {
        "jsonrpc": "2.0",
        "method": "event.get",
        "params": {
            "eventids": eventid,
            "selectHosts": ["host", "name", "description"],
            "output": ["eventid", "value"],
            "sortorder": "DESC"
        },
        "auth": AUTHTOKEN,
        "id": 1
    })
    return events.json()["result"]

def get_groups(hostid):
    """Get host groups for a specific host"""
    groups = requests.post(ZABBIX_API_URL, verify=False,
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

# ============================================================================
# FUNCIONES PARA FILTRO POR TAG notification=Slack
# Agregadas: 2025-11-06
# ============================================================================

def get_event_tags(eventid):
    """
    Obtiene los tags asociados a un evento específico
    Args:
        eventid: ID del evento de Zabbix
    Returns:
        Lista de diccionarios con los tags del evento
        Ejemplo: [{'tag': 'notification', 'value': 'Slack'}, ...]
    """
    events = requests.post(ZABBIX_API_URL, verify=False,
        json={
            "jsonrpc": "2.0",
            "method": "event.get",
            "params": {
                "output": "extend",
                "eventids": eventid,
                "selectTags": "extend"
            },
            "auth": AUTHTOKEN,
            "id": 1
        })
    
    try:
        result = events.json()["result"]
        if result and len(result) > 0:
            return result[0].get("tags", [])
        return []
    except:
        return []


def has_slack_notification_tag(eventid):
    """
    Verifica si un evento tiene el tag notification=Slack
    Args:
        eventid: ID del evento de Zabbix
    Returns:
        True si tiene el tag notification=Slack, False en caso contrario
    """
    tags = get_event_tags(eventid)
    
    for tag in tags:
        if tag.get("tag", "").lower() == "notification" and tag.get("value", "").lower() == "slack":
            return True
    
    return False

