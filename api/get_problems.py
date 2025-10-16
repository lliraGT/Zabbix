# vicente.rodriguez@millicom.com / Millicom TTC
import requests
import json
from methods import *
from datetime import datetime, timedelta

dic_severity = {
    2:'Minor',
    3:'Minor',
    4:'Critical',
    5:'Critical'
}

try:
    dic_problems = get_all_problems()
    for problem in dic_problems:
        if ( problem['r_clock'] == '0' ): # without recovery
            last_month =  datetime.today()-timedelta(days=10) #last week
            cdatetime = datetime.timestamp(last_month)
            if( int(problem['clock']) > int(cdatetime) ):
                dic_events = get_events(problem['eventid'])
#                print(dic_events)
                for hosts in dic_events:
                     host = hosts['hosts']
#                    print(host[0])
#                    print(host[0]['hostid'])
#                    dic_groups = get_groups(host[0]['hostid'])
#                    print(dic_groups)
#                    for group in dic_groups:
                     group_name='monitorPA'
                     if ( int(problem['severity']) in dic_severity.keys() ):
                         print(hosts['eventid'], end=';') # id
                         print(host[0]['host'], end=';') # HostName
                         print(host[0]['name'], end=';') # VisibleName
                         print(problem['name'], end=';') # problem_name
                         print(str(dic_severity[int(problem['severity'])]), end=';') #severity
                         print(datetime.fromtimestamp(int(problem['clock'])), end=';') #date
                         print(group_name) #group
except:
        print("A problem getting data from API occurred: ", datetime.now())

