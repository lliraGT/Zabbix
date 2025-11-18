# vicente.rodriguez@millicom.com / Millicom TTC
# Adapted for Slack integration
import requests
import json
from methods import *
from datetime import datetime, timedelta

dic_severity = {
#    2: 'Minor',
    3: 'Medium',  # Changed from Minor to Medium as per requirements
    4: 'Critical',
    5: 'Critical'
}

try:
    dic_problems = get_all_problems()
    for problem in dic_problems:
        if problem['r_clock'] == '0':  # without recovery
        
            # FILTRO: Verificar tag notification=Slack
            eventid = problem['eventid']
            if not has_slack_notification_tag(eventid):
                # Skip este problema si no tiene el tag
                continue

            last_month = datetime.today() - timedelta(days=10)  # last 10 days
            cdatetime = datetime.timestamp(last_month)
            if int(problem['clock']) > int(cdatetime):
                dic_events = get_events(problem['eventid'])
                for hosts in dic_events:
                    host = hosts['hosts']
                    group_name = 'monitorPA'
                    if int(problem['severity']) in dic_severity.keys():
                        # Output format: eventid;hostname;visible_name;problem_name;severity;timestamp;group
                        print(hosts['eventid'], end=';')  # id
                        print(host[0]['host'], end=';')  # HostName
                        print(host[0]['name'], end=';')  # VisibleName
                        print(problem['name'], end=';')  # problem_name
                        print(str(dic_severity[int(problem['severity'])]), end=';')  # severity
                        print(datetime.fromtimestamp(int(problem['clock'])), end=';')  # date
                        print(group_name)  # group
except Exception as e:
    print(f"A problem getting data from API occurred: {datetime.now()} - {str(e)}")
