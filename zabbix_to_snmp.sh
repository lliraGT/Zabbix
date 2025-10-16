#/bin/bash
#Traps notifications ----------------------------------------------------------|
#                                                                              |
#1. HeartBeatNotification .1.3.6.1.4.1.123456.4.0.1                            |
#2. hobbitAlarmNotification .1.3.6.1.4.1.123456.3.0.1                          |
#------------------------------------------------------------------------------|
#
#Ejemplos de varbinds----------------------------------------------------------|
#VAR_BIND1 | ao_AlarmNumber: .1.3.6.1.4.1.123456.1.1.1.1 = 10200201            |
#VAR_BIND2 | ao_AlarmSeverity: .1.3.6.1.4.1.123456.1.1.1.2 = Critical          |
#VAR_BIND3 | ao_AlarmText: .1.3.6.1.4.1.123456.1.1.1.3 = Bloqueo base de datos |
#VAR_BIND4 | ao_ObjectType: .1.3.6.1.4.1.123456.2.1.1.1 = SERVER               |
#VAR_BIND5 | ao_AfectedObject: .1.3.6.1.4.1.123456.2.1.1.2 = Bloqueos          |
#VAR_BIND6 | ao_ResourceName: .1.3.6.1.4.1.123456.1.1.1.4 = bdaltamira02       |
#------------------------------------------------------------------------------|
# seconds for delay
v_time=30
#paths
v_ruta="/etc/zabbix/temip"
log="$v_ruta/log.txt"
#Iniciacion de variables snmp
v_comunidad="isgtrap"
v_iptemipd="10.86.76.227:162"
v_iptemip="10.86.76.118:162"
#varbinds snmp
v_alarmtrap=".1.3.6.1.4.1.123456.3.0.1"
v_alarmnumb=".1.3.6.1.4.1.123456.1.1.1.1"
v_severidad=".1.3.6.1.4.1.123456.1.1.1.2"
v_alarmtext=".1.3.6.1.4.1.123456.1.1.1.3"
v_alarmtype=".1.3.6.1.4.1.123456.2.1.1.1"
v_objeto=".1.3.6.1.4.1.123456.2.1.1.2"
v_resourceoid=".1.3.6.1.4.1.123456.1.1.1.4"
#Fichero de control de numeros de alarmas
v_filealarms="$v_ruta/config/alarmnumber.txt"
#renombre de los hosts para hacer match con la cmdb
v_elemento="$v_ruta/elemento.out"
#Capturamos alertas
v_alerts="$v_ruta/alerts" #path origen
#Ficheros para verificar estados
v_status="$v_alerts/status.tmp"
v_all_status="$v_alerts/all_status.tmp"
v_file_status="$v_alerts/file_status.tmp"
#####
v_prior_critical="$v_alerts/prior_critical.tmp"
v_prior_minor="$v_alerts/prior_minor.tmp"
v_new_critical="$v_alerts/new_critical.tmp"
v_new_minor="$v_alerts/new_minor.tmp"

function send_trap(){
    snmptrap -Ln -v 2c -c $v_comunidad $v_iptemip "" $v_alarmtrap $v_alarmnumb s "$alarmnumber" $v_severidad s "$estado" $v_alarmtext s "$vhost" $v_alarmtype s "SERVER" $v_objeto s "$alarma" $v_resourceoid s "$host"
    snmptrap -Ln -v 2c -c $v_comunidad $v_iptemipd "" $v_alarmtrap $v_alarmnumb s "$alarmnumber" $v_severidad s "$estado" $v_alarmtext s "$vhost" $v_alarmtype s "SERVER" $v_objeto s "$alarma" $v_resourceoid s "$host"
    echo "$alarmaid = $v_iptemip \"\" $v_alarmtrap $v_alarmnumb s \"$alarmnumber\" $v_severidad s \"$estado\" $v_alarmtext s \"$vhost\" $v_alarmtype s \"SERVER\" $v_objeto s \"$alarma\" $v_resourceoid s \"$host\" " >> $log
}

function envia_oid (){
    while read line
        do
            v_resource=`echo $line |awk -F";" '{print $1}'`
            if [ "$v_resource" != "" ]; then
		alarmaid=`echo $line |awk -F";" '{print $1}'`
                host=`echo $line |awk -F";" '{print $2}'`
                alarma=`echo $line |awk -F";" '{print $3}'`
                estado=`echo $line |awk -F";" '{print $4}'`
		grupo=`echo $line |awk -F";" '{print $5}'`
#                alarmnumber=`cat $v_filealarms |grep "$alarma:" |awk -F"," '{print $1}' |awk '{print $1}'`
		alarmnumber=""
                #Coloca el nombre que estara registrado en la CMDB
                #host=`cat $v_elemento |grep $v_resource |awk -F"=" '{print $2}' |sort -n |tail -1 |awk '{print $1}'`
                #vhost=`cat $v_elemento |grep $v_resource |awk -F"=" '{print $3}' |sort -n |tail -1 |awk '{print $1}'`
                #if [ "$host" = "" ]; then
                #        host=$v_resource
                #fi
                #if [ "$vhost" = "" ]; then
                vhost=$host
                #fi

                if [ "$alarmnumber" = "" ]; then
                    alarmnumber=10100001
                fi

		alarmnumber="${alarmnumber}_${grupo}"

                if [ "$estado" = "Critical" ]; then
                    send_trap;
                fi
                if [ "$estado" = "Minor" ]; then
                    send_trap;
                fi
                if [ "$estado" = "Clear" ]; then
                    echo "Envio el trap clear y se elimina del listado de alarmas" >> $log
                    send_trap;
                fi
            fi
    done < $1
}

function check_status () {
    v_prior=$1
    v_new=$2
    # send resolved problems
    cat /dev/null > $v_file_status
    python3 $v_ruta/api/get_all_problems_nok.py | sort -u > $v_all_status

    while read line
    do
        eventid=`echo $line |awk -F";" '{print $1}'`
        host=`echo $line |awk -F";" '{print $2}'`
        problem=`echo $line |awk -F";" '{print $4}'`
	group_name=`echo $line |awk -F";" '{print $7}'`

	if [ `cat $v_all_status | grep -c $eventid` -eq 0 ] ; then #check if alarm recovered
            severity="Clear"
            echo "$eventid;$host;$problem;$severity;$group_name" >> $v_file_status
        fi
    done < $v_prior

    ###
    envia_oid $v_file_status
    # send new problems
    diff $v_new $v_prior | awk -F"< " '{print $2}' | sed '/^ *$/d' | awk -F';' '{print $1 ";" $2 ";" $4 ";" $5 ";" $7}' > $v_file_status # awk = return 2nd row and remove < , sed = clean 1st line
    cp $v_new $v_prior
    ###
    envia_oid $v_file_status
}


############################ MAIN ############################
echo "[INFO] STARTING ZABBIX2TEMIP" >> $log

if [[ ! -f "$v_prior_minor" ]]; then
    echo "$v_prior_minor dont exists on your filesystem. Creating file..." >> $log
    cat /dev/null > $v_prior_minor
fi

if [[ ! -f "$v_prior_critical" ]]; then
    echo "$v_prior_critical dont exists on your filesystem. Creating file..." >> $log
    cat /dev/null > $v_prior_critical
fi

while true
do
    python3 $v_ruta/api/get_problems.py | sort -u > $v_status
    cat $v_status | grep ";Minor" > $v_new_minor
    cat $v_status | grep ";Critical" > $v_new_critical

    echo "===> Inicio: `date`" >> $log
    check_status $v_prior_critical $v_new_critical;
    check_status $v_prior_minor $v_new_minor;
    echo "<=== Finaliza: `date`" >> $log

    sleep $v_time;
done
