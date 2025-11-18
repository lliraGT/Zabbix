# Sistema Integrado de Monitoreo Zabbix con Notificaciones Slack y Telefónicas

Sistema de monitoreo que consulta problemas activos desde Zabbix y envía notificaciones automáticas a través de Slack y llamadas telefónicas (solo para alertas Critical).

---

## 📋 Descripción General

Reemplazo del sistema anterior basado en SNMP traps. Logra **89% de reducción en alertas innecesarias** mediante:
- Filtrado por tags en triggers de Zabbix
- Filtrado por severidad (Medium y Critical únicamente)
- Prevención de duplicados con state tracking

### Flujo de Notificaciones
Problema Zabbix → Slack (Medium/Critical) → Teléfono (solo Critical)
---

## 🎯 Características

- **Slack**: Mensajes formateados con Block Kit (colores, emojis, estructura)
- **Teléfono**: Llamadas automáticas vía Asterisk AMI (solo Critical)
- **Filtrado Inteligente**: Tag `notification=Slack` + severidad
- **State Management**: Evita notificaciones duplicadas
- **Variables de Entorno**: Configuración segura mediante `.env`

---

## 📁 Estructura del Proyecto
proyecto/
├── .env                              # Configuración (NO versionar)
├── .gitignore                        # Protección de archivos sensibles
├── config.py                         # Carga y validación de configuración
├── requirements.txt                  # Dependencias Python
├── monitor_zabbix_integrated.py      # ⭐ Script principal
├── notificaciones_automatizadas.py   # Sistema de llamadas telefónicas
├── api/
│   ├── methods.py                    # API Zabbix (consultas)
│   ├── slack_notifier.py             # Envío Slack
│   ├── get_problems.py               # Script independiente (legacy)
│   └── get_all_problems_nok.py       # Script consulta (legacy)
├── logs/                             # Auto-generado
├── notified_events.json              # Estado (auto-generado)
└── README.md
---

## 🚀 Instalación

### Prerrequisitos
- Python 3.7+
- Acceso a Zabbix API
- Webhook de Slack
- Servidor Asterisk con AMI habilitado

### Pasos

```bash
# 1. Clonar/copiar proyecto
cd /ruta/proyecto

# 2. Instalar dependencias
pip install -r requirements.txt --break-system-packages

# 3. Configurar .env (copiar desde .env.example)
cp .env.example .env
nano .env

# 4. Validar configuración
python3 config.py
⚙️ Configuración (.env)
Archivo .env con todas las variables necesarias:
# Zabbix
ZABBIX_API_URL=https://<zabbix-server>/api_jsonrpc.php
ZABBIX_API_TOKEN=<token>

# Slack
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/<webhook>

# Asterisk
ASTERISK_HOST=<ip>
ASTERISK_PORT=5038
ASTERISK_AMI_USERNAME=<user>
ASTERISK_AMI_PASSWORD=<pass>
ASTERISK_CALLER_ID=<caller_id>

# Notificaciones
ONCALL_PHONE_NUMBER=<numero>

# Monitoreo
POLL_INTERVAL_SECONDS=60
PROBLEM_LOOKBACK_DAYS=10
STATE_FILE_PATH=notified_events.json
LOG_FILE_PATH=monitor_integrated.log
📖 Uso
Ejecución Manual (Testing)
python3 monitor_zabbix_integrated.py
Ejecución como Servicio (Producción)
Crear /etc/systemd/system/zabbix-monitor.service:
[Unit]
Description=Zabbix Monitor - Slack & Phone Notifications
After=network.target

[Service]
Type=simple
User=<usuario>
WorkingDirectory=<ruta_proyecto>
ExecStart=/usr/bin/python3 <ruta_proyecto>/monitor_zabbix_integrated.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
Comandos:
sudo systemctl enable zabbix-monitor.service
sudo systemctl start zabbix-monitor.service
sudo systemctl status zabbix-monitor.service
sudo systemctl restart zabbix-monitor.service
sudo journalctl -u zabbix-monitor.service -f
🔧 Configuración en Zabbix
Para que un trigger sea procesado, debe tener el tag:
Tag: notification
Value: Slack
Mapeo de Severidades
Código
Nombre Zabbix
Acción
2
Warning
❌ Ignorado
3
Average
✅ Slack (Medium)
4
High
✅ Slack + 📞 (Critical)
5
Disaster
✅ Slack + 📞 (Critical)
🔄 Flujo del Sistema
1. Polling cada 60s → Consulta Zabbix API
   ├─ Filtro: tag = notification:Slack
   ├─ Filtro: r_clock = 0 (sin recovery)
   └─ Filtro: últimos N días

2. Para cada problema nuevo:
   ├─ Verificar si ya fue notificado (notified_events.json)
   ├─ Enviar a Slack (Medium/Critical)
   └─ Si Critical → Llamada telefónica

3. Guardar en notified_events.json
State Management
notified_events.json:
{
  "eventid_123": {
    "timestamp": "2024-11-18T10:30:00",
    "severity": "Critical",
    "hostname": "servidor-01",
    "problem": "Descripción del problema"
  }
}
🧪 Pruebas
# Validar configuración
python3 config.py

# Test Slack (envía mensaje de prueba)
python3 api/slack_notifier.py

# Test teléfono (hace llamada de prueba)
python3 notificaciones_automatizadas.py

# Test completo (modo interactivo)
python3 monitor_zabbix_integrated.py
📝 Logs
Archivo
Contenido
monitor_integrated.log
Log principal
notificaciones.log
Log de llamadas telefónicas
Comandos útiles:
# Ver en tiempo real
tail -f monitor_integrated.log

# Buscar errores
grep ERROR monitor_integrated.log

# Ver estado
cat notified_events.json | python3 -m json.tool
🐛 Troubleshooting
No se envían notificaciones a Slack
# Verificar config
python3 config.py

# Test directo
python3 api/slack_notifier.py

# Verificar tags en Zabbix
No se realizan llamadas
# Test conectividad Asterisk
telnet <asterisk_host> 5038

# Test directo
python3 notificaciones_automatizadas.py
Notificaciones duplicadas
# Verificar instancias corriendo
ps aux | grep monitor_zabbix_integrated

# Ver estado
cat notified_events.json

# Reiniciar estado (CUIDADO)
rm notified_events.json
🔐 Seguridad
✅ Variables de entorno (no hardcodeadas)
✅ .gitignore protege .env
✅ Logs enmascaran credenciales
🔒 .env debe tener permisos 600
🔒 Usuario sin privilegios root
🔒 Rotar tokens periódicamente
📈 Resultados
Métrica
Antes
Después
Mejora
Alertas diarias
~1000+
~110
89% ↓
Tiempo respuesta
5-10 min
1-2 min
70% ↑
Falsos positivos
Alto
Bajo
Efectivo
🔄 Mantenimiento
Comandos Periódicos
# Limpiar logs antiguos (>30 días)
find . -name "*.log" -mtime +30 -delete

# Backup configuración
tar -czf backup_$(date +%Y%m%d).tar.gz .env notified_events.json

# Actualizar desde git
git pull origin main
sudo systemctl restart zabbix-monitor.service
🚧 Roadmap
Fase 2 (Próxima)
[ ] Sistema de turnos (rotación automática on-call)
[ ] Horarios (notificaciones solo en horario laboral)
[ ] Escalamiento (lista de contactos, reintentos)
[ ] Notificaciones de resolución
Fase 3 (Futuro)
[ ] Dashboard web
[ ] Integración MS Teams
[ ] Múltiples canales (SMS, Email, WhatsApp)
[ ] ML para predicción de problemas
📚 Componentes del Sistema
config.py
Carga variables de .env
Valida configuración requerida
Centraliza constantes
api/methods.py
Funciones para consultar Zabbix API
get_all_problems(): Obtiene problemas activos
get_events(): Detalles de evento
has_slack_notification_tag(): Verifica tag
api/slack_notifier.py
send_slack_notification(): Envía mensaje formateado
Block Kit con colores y emojis
Manejo de errores
notificaciones_automatizadas.py
Clase NotificacionAutomatizada
Conexión AMI a Asterisk
enviar_notificacion_simple(): Wrapper fácil de usar
monitor_zabbix_integrated.py
Loop principal (polling cada 60s)
Integra Slack + Teléfono
State management
Logging completo
📄 Archivos Importantes
.env
NO VERSIONAR - Contiene todas las credenciales
.gitignore
Protege:
.env
*.log
notified_events.json
__pycache__/
requirements.txt
requests>=2.28.0
urllib3>=1.26.0
python-dotenv>=1.0.0
🎯 Notas de Implementación
Decisiones de Diseño
Polling vs Webhook: Se eligió polling por simplicidad y compatibilidad con Zabbix existente
State File: JSON simple para persistencia entre reinicios
Tag-based filtering: Más flexible que configurar Actions en Zabbix
Severity mapping: Solo Medium/Critical para reducir ruido
Limitaciones Conocidas
No procesa eventos resueltos automáticamente
State file puede crecer indefinidamente (requiere limpieza manual)
Un solo número on-call (sin escalamiento aún)
Llamadas sin confirmación de recepción
💡 Tips de Uso
Testing inicial: Usar tag en pocos triggers, monitorear comportamiento
Logs: Revisar diariamente primeras semanas
State file: Backup antes de actualizaciones
Números de prueba: Usar internos antes de producción
Horarios: Considerar zonas horarias en futuras versiones
Versión: 1.0.0
Última actualización: Noviembre 2024
