# config.py
# Configuración centralizada - HARDCODED (sin .env por restricciones del servidor)

class Config:
    """Clase para manejar configuración del sistema"""

    # ========================================================================
    # ZABBIX CONFIGURATION
    # ========================================================================
    ZABBIX_API_URL = 'https://172.22.137.204:31080/api_jsonrpc.php'
    ZABBIX_API_TOKEN = 'f299a2249a54dbe788431ba07f103cd114a317315af4376af66b60518fc586db'

    # ========================================================================
    # SLACK CONFIGURATION
    # ========================================================================
    SLACK_WEBHOOK_URL = 'https://hooks.slack.com/services/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'

    # ========================================================================
    # ASTERISK CONFIGURATION
    # ========================================================================
    ASTERISK_HOST = '172.22.57.75'
    ASTERISK_PORT = 5038
    ASTERISK_AMI_USERNAME = 'api_user'
    ASTERISK_AMI_PASSWORD = 'T!G0_T00lsGT#9012'
    ASTERISK_CALLER_ID = '23073500'

    # ========================================================================
    # PHONE NOTIFICATION CONFIGURATION
    # ========================================================================
    ONCALL_PHONE_NUMBER = '40008045'

    # ========================================================================
    # ORACLE TURNOS CONFIGURATION
    # ========================================================================
    #ORACLE_DSN = '172.22.71.131:1521/vapstatd'
    ORACLE_DSN = '(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(HOST=172.22.71.131)(PORT=1521))(CONNECT_DATA=(SID=vapstatd)))'
    ORACLE_USER = 'prepago'
    ORACLE_PASSWORD = 'Bre_7P6h0oAW2X1H'
    USE_TURNOS = True  # Cambiar a True cuando esté listo

    # ========================================================================
    # MONITORING CONFIGURATION
    # ========================================================================
    POLL_INTERVAL = 60
    PROBLEM_LOOKBACK_DAYS = 10
    STATE_FILE = 'notified_events.json'
    LOG_FILE = 'monitor_integrated.log'

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

        # Si USE_TURNOS está activado, validar variables Oracle
        if cls.USE_TURNOS:
            required_vars.update({
                'ORACLE_DSN': cls.ORACLE_DSN,
                'ORACLE_USER': cls.ORACLE_USER,
                'ORACLE_PASSWORD': cls.ORACLE_PASSWORD,
            })

        missing_vars = [var for var, value in required_vars.items() if not value]

        if missing_vars:
            raise ValueError(
                f"Faltan las siguientes variables de entorno requeridas: {', '.join(missing_vars)}\n"
                f"Por favor verifica la configuración en config.py"
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
        print("-" * 70)
        print(f"Sistema de Turnos: {'✓ ACTIVADO' if cls.USE_TURNOS else '✗ DESACTIVADO'}")
        if cls.USE_TURNOS:
            print(f"Oracle DSN: {cls.ORACLE_DSN}")
            print(f"Oracle User: {cls.ORACLE_USER}")
            print(f"Oracle Password: {mask_secret(cls.ORACLE_PASSWORD)}")
        print("=" * 70)


# Validar configuración al importar
try:
    Config.validate()
except ValueError as e:
    print(f"\n⚠  ERROR DE CONFIGURACIÓN:\n{e}\n")
    raise
