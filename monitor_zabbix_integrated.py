#!/usr/bin/env python3
# monitor_zabbix_integrated.py
# Sistema Integrado: Zabbix -> Slack -> Telefono (Critical)

import time
import json
import logging
from datetime import datetime, timedelta
from config import Config
from api.methods import get_all_problems, get_events, has_slack_notification_tag
from api.slack_notifier import send_slack_notification
from notificaciones_automatizadas import enviar_notificacion_simple
from turnos_oracle import get_numero_oncall, TurnosOracle
from api.methods import get_encargado_tag

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def load_notified_events():
    """Cargar eventos ya notificados desde archivo"""
    try:
        with open(Config.STATE_FILE, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except Exception as e:
        logger.error(f"Error cargando estado: {e}")
        return {}

def save_notified_events(events_dict):
    """Guardar eventos notificados a archivo"""
    try:
        with open(Config.STATE_FILE, 'w') as f:
            json.dump(events_dict, f, indent=2)
    except Exception as e:
        logger.error(f"Error guardando estado: {e}")

def process_problems():
    """Procesar problemas activos y enviar notificaciones"""
    logger.info("=" * 70)
    logger.info("Iniciando verificación de problemas...")

    # Cargar eventos ya notificados
    notified_events = load_notified_events()

    # NUEVO: Determinar modo de notificación según horarios
    numero_default = None
    usar_encargado_global = False

    if Config.USE_TURNOS:
        numero_default, usar_encargado_global, info_turno = get_numero_oncall(
            dsn=Config.ORACLE_DSN,
            user=Config.ORACLE_USER,
            password=Config.ORACLE_PASSWORD,
            fallback=Config.ONCALL_PHONE_NUMBER
        )

        if usar_encargado_global:
            logger.info("⏰ Horario laboral - Notificaciones irán a Encargado del KPI (tag Zabbix)")
        else:
            logger.info(f"🌙 Fuera de horario - Número on-call: {numero_default}")
            if info_turno.get('nombre'):
                logger.info(f"   On-call: {info_turno['nombre']} ({info_turno.get('username', 'N/A')})")
    else:
        numero_default = Config.ONCALL_PHONE_NUMBER
        logger.info(f"⚠ Sistema de turnos desactivado - Usando número fijo: {numero_default}")

    try:
        dic_problems = get_all_problems()
        logger.info(f"Total de problemas encontrados: {len(dic_problems)}")

        new_critical_found = 0
        new_medium_found = 0

        for problem in dic_problems:
            # Solo problemas sin recuperación
            if problem['r_clock'] != '0':
                continue

            eventid = problem['eventid']

            # Verificar tag notification=Slack
            if not has_slack_notification_tag(eventid):
                continue

            # Verificar si es de los últimos N días configurados
            last_month = datetime.today() - timedelta(days=Config.PROBLEM_LOOKBACK_DAYS)
            cdatetime = datetime.timestamp(last_month)
            if int(problem['clock']) <= int(cdatetime):
                continue

            # Verificar si ya fue notificado
            if eventid in notified_events:
                continue

            # Obtener severidad
            severity_code = int(problem['severity'])
            if severity_code not in Config.SEVERITY_MAP:
                continue

            severity = Config.SEVERITY_MAP[severity_code]

            # Obtener información del host
            dic_events = get_events(eventid)
            if not dic_events:
                continue

            for event_info in dic_events:
                host = event_info['hosts']
                if not host:
                    continue

                hostname = host[0]['host']
                visible_name = host[0]['name']
                problem_name = problem['name']
                timestamp = datetime.fromtimestamp(int(problem['clock']))
                group_name = 'monitorPA'

                logger.info(f"Nuevo problema detectado - Event: {eventid}, Severity: {severity}")

                # 1. ENVIAR NOTIFICACIÓN A SLACK (siempre)
                slack_success = send_slack_notification(
                    event_id=eventid,
                    hostname=hostname,
                    visible_name=visible_name,
                    problem_name=problem_name,
                    severity=severity,
                    timestamp=timestamp,
                    group_name=group_name
                )

                if slack_success:
                    logger.info(f"✓ Slack: Notificación enviada para {eventid}")
                else:
                    logger.error(f"✗ Slack: Falló notificación para {eventid}")

                # 2. SI ES CRITICAL -> LLAMADA TELEFÓNICA
                if severity == 'Critical':
                    numero_a_llamar = None
                    nombre_contacto = "Desconocido"

                    # Determinar a quién llamar
                    if Config.USE_TURNOS and usar_encargado_global:
                        # HORARIO LABORAL: Usar tag Encargado
                        username_encargado = get_encargado_tag(eventid)

                        if username_encargado:
                            logger.info(f"📋 Tag Encargado encontrado: {username_encargado}")

                            # Buscar teléfono del encargado en Oracle
                            try:
                                turnos_temp = TurnosOracle(
                                    Config.ORACLE_DSN,
                                    Config.ORACLE_USER,
                                    Config.ORACLE_PASSWORD
                                )
                                numero_a_llamar = turnos_temp.get_telefono_por_username(username_encargado)
                                nombre_contacto = username_encargado
                                turnos_temp.close()

                                if not numero_a_llamar:
                                    logger.warning(f"⚠ No se encontró teléfono para {username_encargado}, usando fallback")
                                    numero_a_llamar = Config.ONCALL_PHONE_NUMBER
                            except Exception as e:
                                logger.error(f"Error consultando teléfono de encargado: {e}")
                                numero_a_llamar = Config.ONCALL_PHONE_NUMBER
                        else:
                            logger.warning("⚠ Tag Encargado no encontrado en trigger, usando on-call de turno")
                            numero_a_llamar = numero_default or Config.ONCALL_PHONE_NUMBER
                    else:
                        # FUERA DE HORARIO: Usar on-call de turno
                        numero_a_llamar = numero_default or Config.ONCALL_PHONE_NUMBER
                        nombre_contacto = info_turno.get('nombre', 'On-call') if 'info_turno' in locals() else 'On-call'

                    logger.info(f"⚠ ALERTA CRITICAL - Llamando a {nombre_contacto}: {numero_a_llamar}")

                    phone_result = enviar_notificacion_simple(
                        numero=numero_a_llamar,
                        mensaje='alerta_critica'
                    )

                    if phone_result['success']:
                        logger.info(f"✓ Teléfono: Llamada iniciada - Call ID: {phone_result['call_id']}")
                        new_critical_found += 1
                    else:
                        logger.error(f"✗ Teléfono: Error en llamada - {phone_result.get('error', 'Unknown')}")
                else:
                    new_medium_found += 1

                # Marcar como notificado
                notified_events[eventid] = {
                    'timestamp': datetime.now().isoformat(),
                    'severity': severity,
                    'hostname': hostname,
                    'problem': problem_name
                }

        # Guardar estado actualizado
        save_notified_events(notified_events)

        logger.info(f"Resumen: {new_critical_found} Critical, {new_medium_found} Medium notificados")

    except Exception as e:
        logger.error(f"Error procesando problemas: {e}", exc_info=True)

def main():
    """Loop principal de monitoreo"""
    logger.info("=" * 70)
    logger.info("SISTEMA DE MONITOREO INTEGRADO ZABBIX")
    logger.info("Slack + Notificaciones Telefónicas")
    logger.info("Tigo Guatemala - Millicom TTC")
    logger.info("=" * 70)

    # Mostrar configuración (con secretos enmascarados)
    Config.display_config()

    logger.info("=" * 70)
    logger.info("Sistema iniciado correctamente")
    logger.info("=" * 70)

    while True:
        try:
            process_problems()
            logger.info(f"Esperando {Config.POLL_INTERVAL} segundos hasta próxima verificación...\n")
            time.sleep(Config.POLL_INTERVAL)

        except KeyboardInterrupt:
            logger.info("\n" + "=" * 70)
            logger.info("Sistema detenido por usuario")
            logger.info("=" * 70)
            break
        except Exception as e:
            logger.error(f"Error en loop principal: {e}", exc_info=True)
            time.sleep(Config.POLL_INTERVAL)

if __name__ == "__main__":
    main()
