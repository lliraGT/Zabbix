# config.py
# Configuración centralizada usando variables de entorno

import os
from pathlib import Path
from dotenv import load_dotenv

# Cargar variables de entorno desde archivo .env
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

class Config:
    """Clase para manejar configuración del sistema"""
    
    # ========================================================================
    # ZABBIX CONFIGURATION
    # ========================================================================
    ZABBIX_API_URL = os.getenv('ZABBIX_API_URL')
    ZABBIX_API_TOKEN = os.getenv('ZABBIX_API_TOKEN')
    
    # ========================================================================
    # SLACK CONFIGURATION
    # ========================================================================
    SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL')
    
    # ========================================================================
    # ASTERISK CONFIGURATION
    # ========================================================================
    ASTERISK_HOST = os.getenv('ASTERISK_HOST')
    ASTERISK_PORT = int(os.getenv('ASTERISK_PORT', 5038))
    ASTERISK_AMI_USERNAME = os.getenv('ASTERISK_AMI_USERNAME')
    ASTERISK_AMI_PASSWORD = os.getenv('ASTERISK_AMI_PASSWORD')
    ASTERISK_CALLER_ID = os.getenv('ASTERISK_CALLER_ID', '23073500')
    
    # ========================================================================
    # PHONE NOTIFICATION CONFIGURATION
    # ========================================================================
    ONCALL_PHONE_NUMBER = os.getenv('ONCALL_PHONE_NUMBER')
    
    # ========================================================================
    # MONITORING CONFIGURATION
    # ========================================================================
    POLL_INTERVAL = int(os.getenv('POLL_INTERVAL_SECONDS', 60))
    PROBLEM_LOOKBACK_DAYS = int(os.getenv('PROBLEM_LOOKBACK_DAYS', 10))
    STATE_FILE = os.getenv('STATE_FILE_PATH', 'notified_events.json')
    LOG_FILE = os.getenv('LOG_FILE_PATH', 'monitor_integrated.log')
    
    # ========================================================================
    # SEVERITY MAPPING
    # ========================================================================
    SEVERITY_MAP = {
        3: 'Medium',
        4: 'Critical',
        5: 'Critical'
    }
    
    @classmethod
    def validate(cls):
        """Validar que todas las configuraciones requeridas estén presentes"""
        required_vars = {
            'ZABBIX_API_URL': cls.ZABBIX_API_URL,
            'ZABBIX_API_TOKEN': cls.ZABBIX_API_TOKEN,
            'SLACK_WEBHOOK_URL': cls.SLACK_WEBHOOK_URL,
            'ASTERISK_HOST': cls.ASTERISK_HOST,
            'ASTERISK_AMI_USERNAME': cls.ASTERISK_AMI_USERNAME,
            'ASTERISK_AMI_PASSWORD': cls.ASTERISK_AMI_PASSWORD,
            'ONCALL_PHONE_NUMBER': cls.ONCALL_PHONE_NUMBER,
        }
        
        missing_vars = [var for var, value in required_vars.items() if not value]
        
        if missing_vars:
            raise ValueError(
                f"Faltan las siguientes variables de entorno requeridas: {', '.join(missing_vars)}\n"
                f"Por favor verifica tu archivo .env"
            )
        
        return True
    
    @classmethod
    def display_config(cls):
        """Mostrar configuración actual (ocultando secretos)"""
        def mask_secret(value, show_chars=4):
            """Enmascara un secreto mostrando solo los últimos caracteres"""
            if not value:
                return "*** NO CONFIGURADO ***"
            if len(value) <= show_chars:
                return "*" * len(value)
            return "*" * (len(value) - show_chars) + value[-show_chars:]
        
        print("=" * 70)
        print("CONFIGURACIÓN DEL SISTEMA")
        print("=" * 70)
        print(f"Zabbix API URL: {cls.ZABBIX_API_URL}")
        print(f"Zabbix API Token: {mask_secret(cls.ZABBIX_API_TOKEN, 8)}")
        print(f"Slack Webhook: {mask_secret(cls.SLACK_WEBHOOK_URL, 10)}")
        print(f"Asterisk Host: {cls.ASTERISK_HOST}:{cls.ASTERISK_PORT}")
        print(f"Asterisk User: {cls.ASTERISK_AMI_USERNAME}")
        print(f"Asterisk Password: {mask_secret(cls.ASTERISK_AMI_PASSWORD)}")
        print(f"Caller ID: {cls.ASTERISK_CALLER_ID}")
        print(f"On-Call Phone: {cls.ONCALL_PHONE_NUMBER}")
        print(f"Poll Interval: {cls.POLL_INTERVAL} segundos")
        print(f"Lookback Days: {cls.PROBLEM_LOOKBACK_DAYS} días")
        print("=" * 70)


# Validar configuración al importar
try:
    Config.validate()
except ValueError as e:
    print(f"\n⚠  ERROR DE CONFIGURACIÓN:\n{e}\n")
    raise