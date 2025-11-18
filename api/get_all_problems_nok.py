# vicente.rodriguez@millicom.com / Millicom TTC
# Get all problems without recovery (r_clock == 0)
import sys
import requests
import json
from methods import *
from datetime import datetime, timedelta

dic_problems = get_all_problems()

for problem in dic_problems:
    if problem['r_clock'] == '0':  # without recovery

        # FILTRO: Verificar tag notification=Slack
        eventid = problem['eventid']
        if not has_slack_notification_tag(eventid):
            # Skip este problema si no tiene el tag
            continue
            
        print(problem)
