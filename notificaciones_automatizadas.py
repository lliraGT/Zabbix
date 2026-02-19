#!/usr/bin/env python3
# notificaciones_automatizadas.py
# Phone notification system with environment variables
import socket
import time
import logging
from datetime import datetime
from typing import Dict, Optional
from config import Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('notificaciones.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class NotificacionAutomatizada:

    def __init__(self,
                 asterisk_host: str = None,
                 asterisk_port: int = None,
                 ami_username: str = None,
                 ami_password: str = None,
                 caller_id_default: str = None):

        # Usar valores de Config si no se proporcionan
        self.asterisk_host = asterisk_host or Config.ASTERISK_HOST
        self.asterisk_port = asterisk_port or Config.ASTERISK_PORT
        self.ami_username = ami_username or Config.ASTERISK_AMI_USERNAME
        self.ami_password = ami_password or Config.ASTERISK_AMI_PASSWORD
        self.caller_id_default = caller_id_default or Config.ASTERISK_CALLER_ID

        logger.info("Sistema inicializado - Asterisk: {}:{}".format(
            self.asterisk_host, self.asterisk_port))

    def _conectar_ami(self) -> Optional[socket.socket]:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((self.asterisk_host, self.asterisk_port))

            banner = sock.recv(1024).decode('utf-8')
            logger.debug("Banner AMI: {}".format(banner.strip()))

            login_cmd = (
                "Action: Login\r\n"
                "Username: {}\r\n"
                "Secret: {}\r\n"
                "\r\n"
            ).format(self.ami_username, self.ami_password)
            sock.sendall(login_cmd.encode('utf-8'))

            time.sleep(0.5)
            response = sock.recv(4096).decode('utf-8')

            if "Success" in response or "accepted" in response:
                logger.debug("Autenticación AMI exitosa")

                sock.settimeout(0.5)
                try:
                    while sock.recv(4096):
                        pass
                except socket.timeout:
                    pass
                sock.settimeout(10)

                return sock
            else:
                logger.error("Autenticación fallida: {}".format(response))
                sock.close()
                return None

        except socket.timeout:
            logger.error("Timeout al conectar con AMI")
            return None
        except Exception as e:
            logger.error("Error al conectar con AMI: {}".format(e))
            return None

    def enviar_notificacion(self,
                          numero: str,
                          mensaje_audio: str,
                          caller_id: Optional[str] = None,
                          datos_adicionales: Optional[Dict[str, str]] = None,
                          timeout: int = 30000) -> Dict:

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        call_id = "notif_{}".format(timestamp)

        if not caller_id:
            caller_id = self.caller_id_default

        logger.info("Iniciando notificación a {} - Audio: {}".format(numero, mensaje_audio))

        sock = self._conectar_ami()
        if not sock:
            error_msg = "No se pudo conectar a Asterisk"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'numero': numero,
                'call_id': call_id,
                'timestamp': datetime.now().isoformat()
            }

        try:
            cmd = (
                "Action: Originate\r\n"
                "ActionID: {}\r\n"
                "Channel: SIP/{}@trunkims\r\n"
                "Application: Playback\r\n"
                "Data: {}\r\n"
                "CallerID: {}\r\n"
                "Timeout: {}\r\n"
                "Async: true\r\n"
            ).format(call_id, numero, mensaje_audio, caller_id, timeout)

            if datos_adicionales:
                for key, value in datos_adicionales.items():
                    cmd += "Variable: {}={}\r\n".format(key, value)

            cmd += "Variable: NOTIF_ID={}\r\n".format(call_id)
            cmd += "Variable: NOTIF_TIMESTAMP={}\r\n".format(timestamp)
            cmd += "Variable: NOTIF_DEST={}\r\n".format(numero)
            cmd += "\r\n"

            logger.debug("Enviando comando Originate...")
            sock.sendall(cmd.encode('utf-8'))

            time.sleep(1)
            response = ""
            try:
                sock.settimeout(3)
                response = sock.recv(8192).decode('utf-8')
            except socket.timeout:
                logger.warning("Timeout esperando respuesta de Originate")

            logger.debug("Respuesta AMI: {}...".format(response[:200]))

            try:
                logoff_cmd = "Action: Logoff\r\n\r\n"
                sock.sendall(logoff_cmd.encode('utf-8'))
            except:
                pass

            sock.close()

            if "Success" in response:
                logger.info("✓ Notificación enviada exitosamente a {}".format(numero))
                return {
                    'success': True,
                    'message': 'Notificación enviada exitosamente',
                    'numero': numero,
                    'call_id': call_id,
                    'mensaje_audio': mensaje_audio,
                    'caller_id': caller_id,
                    'timestamp': datetime.now().isoformat()
                }
            else:
                logger.warning("Respuesta inesperada de Asterisk para {}".format(numero))
                return {
                    'success': False,
                    'error': 'Respuesta inesperada de Asterisk',
                    'numero': numero,
                    'call_id': call_id,
                    'timestamp': datetime.now().isoformat()
                }

        except Exception as e:
            error_msg = "Error al enviar notificación: {}".format(e)
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'numero': numero,
                'call_id': call_id,
                'timestamp': datetime.now().isoformat()
            }
        finally:
            if sock:
                try:
                    sock.close()
                except:
                    pass


# Mensajes de audio disponibles
MENSAJES_AUDIO = {
    'bienvenida': 'demo-congrats',
    'recordatorio': 'hello-world',
    'urgente': 'demo-congrats',

    # AUDIOS PERSONALIZADOS
    'alerta_critica': 'es/alerta_critica',
}


def enviar_notificacion_simple(numero: str, mensaje: str = 'bienvenida') -> Dict:
    """
    Función simplificada para enviar notificación
    Usa configuración desde Config (variables de entorno)
    """
    sistema = NotificacionAutomatizada()

    audio = MENSAJES_AUDIO.get(mensaje, MENSAJES_AUDIO['bienvenida'])

    resultado = sistema.enviar_notificacion(
        numero=numero,
        mensaje_audio=audio,
        datos_adicionales={
            'TIPO_MENSAJE': mensaje,
            'ORIGEN': 'sistema_automatico'
        }
    )

    return resultado


if __name__ == "__main__":
    print("="*70)
    print("SISTEMA DE NOTIFICACIONES AUTOMATIZADAS")
    print("Tigo Guatemala - CORE & VAP")
    print("="*70)
    print()

    # Mostrar configuración
    Config.display_config()
    print()

    print("EJEMPLO 1: Notificación simple")
    print("-" * 70)

    resultado = enviar_notificacion_simple(
        numero=Config.ONCALL_PHONE_NUMBER,
        mensaje='bienvenida'
    )

    if resultado['success']:
        print("✓ Notificación enviada exitosamente")
        print("  Call ID: {}".format(resultado['call_id']))
        print("  Número: {}".format(resultado['numero']))
        print("  Timestamp: {}".format(resultado['timestamp']))
    else:
        print("✗ Error: {}".format(resultado['error']))

    print()
    print("="*70)
    print("Los logs se guardan en: notificaciones.log")
