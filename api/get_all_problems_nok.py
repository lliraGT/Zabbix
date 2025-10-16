# vicente.rodriguez@millicom.com / Millicom TTC
import sys
import requests
import json
from methods import *
from datetime import datetime, timedelta

dic_problems = get_all_problems()
#dic_problems = get_triggers_in_problems()

for problem in dic_problems:
    if ( problem['r_clock'] == '0' ): # without recovery
        print(problem)
