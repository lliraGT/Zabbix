#!/bin/bash
#==============================================================================
# Zabbix to Slack Connector
# vicente.rodriguez@millicom.com / Millicom TTC
# 
# This script monitors Zabbix problems and sends notifications to Slack
# Adapted from original zabbix_to_snmp.sh
#==============================================================================

# Configuration
v_time=30  # seconds between checks
v_ruta="/opt/zabbix_slack_connector/zabbix_slack_connector"  # Path to your installation directory
log="$v_ruta/log.txt"

# Alert directories
v_alerts="$v_ruta/alerts"
v_status="$v_alerts/status.tmp"
v_all_status="$v_alerts/all_status.tmp"
v_file_status="$v_alerts/file_status.tmp"

# Severity-specific status files
v_prior_critical="$v_alerts/prior_critical.tmp"
v_prior_medium="$v_alerts/prior_medium.tmp"
v_prior_minor="$v_alerts/prior_minor.tmp"
v_new_critical="$v_alerts/new_critical.tmp"
v_new_medium="$v_alerts/new_medium.tmp"
v_new_minor="$v_alerts/new_minor.tmp"

# Create directories if they don't exist
mkdir -p "$v_alerts"
mkdir -p "$v_ruta/api"

function send_to_slack() {
    
    #Send alert to Slack using Python script
    #Reads from file and processes each line
    
    while read line; do
        v_resource=$(echo "$line" | awk -F";" '{print $1}')
        if [ "$v_resource" != "" ]; then
            event_id=$(echo "$line" | awk -F";" '{print $1}')
            hostname=$(echo "$line" | awk -F";" '{print $2}')
            visible_name=$(echo "$line" | awk -F";" '{print $3}')
            problem_name=$(echo "$line" | awk -F";" '{print $4}')
            severity=$(echo "$line" | awk -F";" '{print $5}')
            timestamp=$(echo "$line" | awk -F";" '{print $6}')
            group_name=$(echo "$line" | awk -F";" '{print $7}')
            
            # Call Python script to send Slack notification
            python3 -c "
import sys
sys.path.append('$v_ruta/api')
from slack_notifier import send_slack_notification
send_slack_notification(
    event_id='$event_id',
    hostname='$hostname',
    visible_name='$visible_name',
    problem_name='$problem_name',
    severity='$severity',
    timestamp='$timestamp',
    group_name='$group_name'
)
"
            
            echo "[$( date +'%Y-%m-%d %H:%M:%S' )] Sent Slack notification for event $event_id - $severity - $problem_name" >> "$log"
        fi
    done < "$1"
}

function check_status() {
    
    #Check status changes between previous and new problems
    #Send notifications for resolved and new problems
    
    v_prior="$1"
    v_new="$2"
    
    # Clear file status
    cat /dev/null > "$v_file_status"
    
    # Get all current unresolved problems
    python3 "$v_ruta/api/get_all_problems_nok.py" | sort -u > "$v_all_status"
    
    # Check for resolved problems
    while read line; do
        event_id=$(echo "$line" | awk -F";" '{print $1}')
        hostname=$(echo "$line" | awk -F";" '{print $2}')
        problem_name=$(echo "$line" | awk -F";" '{print $4}')
        group_name=$(echo "$line" | awk -F";" '{print $7}')
        
        # If event is not in current problems, it has been resolved
        if [ $(cat "$v_all_status" | grep -c "$event_id") -eq 0 ]; then
            severity="Clear"
            timestamp=$(date +'%Y-%m-%d %H:%M:%S')
            echo "$event_id;$hostname;$hostname;$problem_name;$severity;$timestamp;$group_name" >> "$v_file_status"
        fi
    done < "$v_prior"
    
    # Send resolved problem notifications
    send_to_slack "$v_file_status"
    
    # Check for new problems
    diff "$v_new" "$v_prior" | awk -F"< " '{print $2}' | sed '/^ *$/d' | awk -F';' '{print $1 ";" $2 ";" $3 ";" $4 ";" $5 ";" $6 ";" $7}' > "$v_file_status"
    
    # Update prior status
    cp "$v_new" "$v_prior"
    
    # Send new problem notifications
    send_to_slack "$v_file_status"
}

#==============================================================================
# MAIN EXECUTION
#==============================================================================

echo "==========================================" >> "$log"
echo "[INFO] STARTING ZABBIX TO SLACK CONNECTOR" >> "$log"
echo "[INFO] Start time: $(date)" >> "$log"
echo "==========================================" >> "$log"

# Create initial status files if they don't exist
if [[ ! -f "$v_prior_minor" ]]; then
    echo "[INFO] Creating $v_prior_minor" >> "$log"
    cat /dev/null > "$v_prior_minor"
fi

if [[ ! -f "$v_prior_medium" ]]; then
    echo "[INFO] Creating $v_prior_medium" >> "$log"
    cat /dev/null > "$v_prior_medium"
fi

if [[ ! -f "$v_prior_critical" ]]; then
    echo "[INFO] Creating $v_prior_critical" >> "$log"
    cat /dev/null > "$v_prior_critical"
fi

# Send startup notification to Slack
python3 -c "
import sys
sys.path.append('$v_ruta/api')
from slack_notifier import send_simple_slack_message
send_simple_slack_message('🚀 Zabbix to Slack Connector started successfully')
" 2>> "$log"

# Main monitoring loop
while true; do
    echo "" >> "$log"
    echo "===> Check started: $(date)" >> "$log"
    
    # Get current problems from Zabbix
    python3 "$v_ruta/api/get_problems.py" 2>> "$log" | sort -u > "$v_status"
    
    # Split by severity
    cat "$v_status" | grep ";Minor" > "$v_new_minor"
    cat "$v_status" | grep ";Medium" > "$v_new_medium"
    cat "$v_status" | grep ";Critical" > "$v_new_critical"
    
    # Check status for each severity level
    check_status "$v_prior_critical" "$v_new_critical"
    check_status "$v_prior_medium" "$v_new_medium"
    check_status "$v_prior_minor" "$v_new_minor"
    
    echo "<=== Check completed: $(date)" >> "$log"
    
    # Wait before next check
    sleep "$v_time"
done
