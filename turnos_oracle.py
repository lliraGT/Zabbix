# turnos_oracle.py
# Módulo para consultar turnos desde Oracle usando tablas existentes
# TFSS_TURNOS + TFSS_COREVAP_USERS

import os
import sys
import oracledb
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from horarios import GestorHorarios

logger = logging.getLogger(__name__)

class TurnosOracle:
    """Consulta de turnos desde Oracle usando tablas TFSS existentes"""

    def __init__(self, dsn: str, user: str, password: str):
        """
        Args:
            dsn: Conexión Oracle (formato SID)
            user: Usuario Oracle
            password: Password Oracle
        """
        self.dsn = dsn
        self.user = user
        self.password = password
        self._connection = None

    def _get_connection(self):
        """Obtener conexión Oracle"""
        try:
            if self._connection is None:
                self._connection = oracledb.connect(
                    user=self.user,
                    password=self.password,
                    dsn=self.dsn
                )
                logger.debug("Conexión Oracle establecida")
            return self._connection
        except oracledb.Error as e:
            logger.error(f"Error conectando a Oracle: {e}")
            return None

    def get_oncall_actual(self) -> Optional[Dict[str, str]]:
        """
        Obtiene el contacto on-call según horario actual

        - Horario laboral → Retorna None (usar tag Encargado)
        - Fuera de horario → Consulta turno de TFSS_TURNOS

        Returns:
            Dict con nombre, telefono, username o None
        """
        conn = self._get_connection()
        if not conn:
            return None

        try:
            # Determinar si es horario laboral
            es_laboral = GestorHorarios.es_horario_laboral()

            if es_laboral:
                logger.info("Horario laboral detectado - Se debe usar tag Encargado de Zabbix")
                return None

            # Fuera de horario: obtener fecha del turno activo
            fecha_turno = GestorHorarios.get_fecha_turno_activo()

            if not fecha_turno:
                logger.warning("No se pudo determinar fecha de turno")
                return None

            cursor = conn.cursor()

            # Query: Obtener turno de la fecha específica
            query = """
                SELECT DISTINCT
                    u.FIRSTNAME || ' ' || u.LASTNAME AS NOMBRE_COMPLETO,
                    u.PHONE AS TELEFONO,
                    u.USERNAME,
                    t.AREA,
                    u.DEPARTMENT
                FROM TFSS_TURNOS t
                JOIN TFSS_COREVAP_USERS u ON UPPER(t.USUARIO) = UPPER(u.USERNAME)
                WHERE TRUNC(t.FECHA) = TRUNC(:fecha)
                AND t.OBSERVACION = 'NORMAL'
                AND u.PHONE IS NOT NULL
                AND ROWNUM = 1
            """

            cursor.execute(query, fecha=fecha_turno)
            row = cursor.fetchone()
            cursor.close()

            if row:
                telefono = row[1]
                if telefono and telefono.strip() and telefono != '(null)':
                    logger.info(f"Turno encontrado para fecha {fecha_turno.date()}")
                    return {
                        'nombre': row[0],
                        'telefono': telefono,
                        'username': row[2],
                        'area': row[3] if row[3] else '',
                        'department': row[4] if row[4] else '',
                        'fecha_turno': fecha_turno.strftime('%Y-%m-%d')
                    }
                else:
                    logger.warning(f"Usuario tiene teléfono inválido")
                    return None
            else:
                logger.warning(f"No hay turno registrado para {fecha_turno.date()}")
                return None

        except oracledb.Error as e:
            logger.error(f"Error consultando turno actual: {e}")
            return None

    def get_turno_por_fecha(self, fecha: datetime) -> Optional[Dict[str, str]]:
        """
        Obtiene el turno para una fecha específica

        Args:
            fecha: Fecha a consultar

        Returns:
            Dict con datos del turno o None
        """
        conn = self._get_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor()

            query = """
                SELECT DISTINCT
                    u.FIRSTNAME || ' ' || u.LASTNAME AS NOMBRE_COMPLETO,
                    u.PHONE AS TELEFONO,
                    u.USERNAME,
                    t.AREA,
                    t.FECHA
                FROM TFSS_TURNOS t
                JOIN TFSS_COREVAP_USERS u ON UPPER(t.USUARIO) = UPPER(u.USERNAME)
                WHERE TRUNC(t.FECHA) = TRUNC(:fecha)
                AND t.OBSERVACION = 'NORMAL'
                AND u.PHONE IS NOT NULL
                AND ROWNUM = 1
            """

            cursor.execute(query, fecha=fecha)
            row = cursor.fetchone()
            cursor.close()

            if row:
                telefono = row[1]
                if telefono and telefono.strip() and telefono != '(null)':
                    return {
                        'nombre': row[0],
                        'telefono': telefono,
                        'username': row[2],
                        'area': row[3] if row[3] else '',
                        'fecha': row[4]
                    }
            return None

        except oracledb.Error as e:
            logger.error(f"Error consultando turno por fecha: {e}")
            return None

    def get_proximos_turnos(self, dias: int = 7) -> List[Dict]:
        """
        Obtiene turnos programados para los próximos N días
        Devuelve solo UN registro por día (UNIQUE)

        Args:
            dias: Cantidad de días a consultar

        Returns:
            Lista de turnos programados
        """
        conn = self._get_connection()
        if not conn:
            return []

        try:
            cursor = conn.cursor()

            # Query con subquery para garantizar UNIQUE por fecha
            query = """
                SELECT
                    NOMBRE_COMPLETO,
                    TELEFONO,
                    USERNAME,
                    AREA,
                    FECHA
                FROM (
                    SELECT DISTINCT
                        u.FIRSTNAME || ' ' || u.LASTNAME AS NOMBRE_COMPLETO,
                        u.PHONE AS TELEFONO,
                        u.USERNAME,
                        t.AREA,
                        t.FECHA,
                        ROW_NUMBER() OVER (PARTITION BY TRUNC(t.FECHA) ORDER BY t.FECHA) as rn
                    FROM TFSS_TURNOS t
                    JOIN TFSS_COREVAP_USERS u ON UPPER(t.USUARIO) = UPPER(u.USERNAME)
                    WHERE t.FECHA >= TRUNC(SYSDATE)
                    AND t.FECHA < TRUNC(SYSDATE) + :dias
                    AND t.OBSERVACION = 'NORMAL'
                    AND u.PHONE IS NOT NULL
                )
                WHERE rn = 1
                ORDER BY FECHA
            """

            cursor.execute(query, dias=dias)
            rows = cursor.fetchall()
            cursor.close()

            turnos = []
            for row in rows:
                telefono = row[1]
                if telefono and telefono.strip() and telefono != '(null)':
                    turnos.append({
                        'nombre': row[0],
                        'telefono': telefono,
                        'username': row[2],
                        'area': row[3] if row[3] else '',
                        'fecha': row[4]
                    })

            return turnos

        except oracledb.Error as e:
            logger.error(f"Error consultando próximos turnos: {e}")
            return []

    def get_todos_usuarios_activos(self) -> List[Dict]:
        """
        Obtiene lista de todos los usuarios con teléfono válido
        Útil para ver quién está disponible

        Returns:
            Lista de usuarios activos
        """
        conn = self._get_connection()
        if not conn:
            return []

        try:
            cursor = conn.cursor()

            query = """
                SELECT
                    USERNAME,
                    FIRSTNAME || ' ' || LASTNAME AS NOMBRE_COMPLETO,
                    PHONE,
                    DEPARTMENT,
                    ROL
                FROM TFSS_COREVAP_USERS
                WHERE PHONE IS NOT NULL
                AND PHONE != '(null)'
                ORDER BY FIRSTNAME, LASTNAME
            """

            cursor.execute(query)
            rows = cursor.fetchall()
            cursor.close()

            usuarios = []
            for row in rows:
                usuarios.append({
                    'username': row[0],
                    'nombre': row[1],
                    'telefono': row[2],
                    'department': row[3],
                    'role': row[4]
                })

            return usuarios

        except oracledb.Error as e:
            logger.error(f"Error consultando usuarios activos: {e}")
            return []

    def verificar_conexion(self) -> bool:
        """Verificar si la conexión a Oracle está funcionando"""
        try:
            conn = self._get_connection()
            if conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1 FROM DUAL")
                cursor.fetchone()
                cursor.close()
                logger.info("✓ Conexión Oracle verificada correctamente")
                return True
            return False
        except Exception as e:
            logger.error(f"✗ Error verificando conexión Oracle: {e}")
            return False

    def get_telefono_por_username(self, username: str) -> Optional[str]:
        """
        Obtiene el teléfono de un usuario por su username

        Args:
            username: Username del usuario

        Returns:
            Número de teléfono o None
        """
        conn = self._get_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor()

            query = """
                SELECT PHONE
                FROM TFSS_COREVAP_USERS
                WHERE UPPER(USERNAME) = UPPER(:username)
                AND PHONE IS NOT NULL
                AND PHONE != '(null)'
            """

            cursor.execute(query, username=username)
            row = cursor.fetchone()
            cursor.close()

            if row and row[0]:
                logger.info(f"✓ Teléfono encontrado para {username}: {row[0]}")
                return row[0]
            else:
                logger.warning(f"⚠ No se encontró teléfono para username: {username}")
                return None

        except oracledb.Error as e:
            logger.error(f"Error consultando teléfono: {e}")
            return None

    def close(self):
        """Cerrar conexión Oracle"""
        if self._connection:
            try:
                self._connection.close()
                logger.debug("Conexión Oracle cerrada")
            except:
                pass


# Función helper para usar fácilmente
def get_numero_oncall(dsn: str, user: str, password: str, fallback: str) -> tuple:
    """
    Obtiene número on-call actual según horario

    Args:
        dsn: Oracle DSN
        user: Usuario Oracle
        password: Password Oracle
        fallback: Número por defecto si no hay turno

    Returns:
        Tupla: (numero_telefono, usar_encargado, info_contacto)
        - numero_telefono: str - Número a llamar (o None si usar encargado)
        - usar_encargado: bool - True si debe usar tag Encargado
        - info_contacto: dict - Información del contacto
    """
    try:
        # Verificar si es horario laboral
        es_laboral = GestorHorarios.es_horario_laboral()

        if es_laboral:
            logger.info("⏰ Horario laboral - Se debe usar tag Encargado de Zabbix")
            return (None, True, {'tipo': 'encargado', 'horario': 'laboral'})

        # Fuera de horario: consultar turno
        turnos = TurnosOracle(dsn, user, password)
        oncall = turnos.get_oncall_actual()
        turnos.close()

        if oncall and oncall['telefono']:
            logger.info(f"✓ On-call de turno: {oncall['nombre']} ({oncall['username']}) - {oncall['telefono']}")
            return (oncall['telefono'], False, oncall)
        else:
            logger.warning(f"⚠ No hay turno activo, usando número fallback: {fallback}")
            return (fallback, False, {'tipo': 'fallback', 'numero': fallback})

    except Exception as e:
        logger.error(f"✗ Error obteniendo número on-call: {e}")
        logger.warning(f"Usando número fallback: {fallback}")
        return (fallback, False, {'tipo': 'fallback', 'numero': fallback, 'error': str(e)})

# Test de conexión
if __name__ == "__main__":
    # Configurar logging para el test
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Importar config
    from config import Config

    print("=" * 70)
    print("TEST DE CONEXIÓN ORACLE - SISTEMA DE TURNOS")
    print("Tablas: TFSS_TURNOS + TFSS_COREVAP_USERS")
    print("=" * 70)
    print()

    # Verificar que las variables estén configuradas
    if not Config.ORACLE_DSN or not Config.ORACLE_USER or not Config.ORACLE_PASSWORD:
        print("✗ ERROR: Variables Oracle no configuradas en config.py")
        sys.exit(1)

    print(f"Conectando a: {Config.ORACLE_DSN}")
    print(f"Usuario: {Config.ORACLE_USER}")
    print()

    turnos = TurnosOracle(
        dsn=Config.ORACLE_DSN,
        user=Config.ORACLE_USER,
        password=Config.ORACLE_PASSWORD
    )

    # Test 1: Verificar conexión
    print("1. Verificando conexión...")
    if turnos.verificar_conexion():
        print("   ✓ Conexión exitosa")
    else:
        print("   ✗ Error en conexión")
        sys.exit(1)

    print()

    # Test 2: Consultar turno actual (HOY)
    print("2. Consultando turno actual (HOY)...")
    oncall = turnos.get_oncall_actual()
    if oncall:
        print(f"   ✓ On-call: {oncall['nombre']}")
        print(f"     Username: {oncall['username']}")
        print(f"     Teléfono: {oncall['telefono']}")
        print(f"     Área: {oncall['area']}")
        print(f"     Departamento: {oncall['department']}")
    else:
        print("   ⚠ No hay turno activo para hoy")

    print()

    # Test 3: Próximos 7 días
    print("3. Consultando próximos 7 días...")
    proximos = turnos.get_proximos_turnos(7)
    if proximos:
        print(f"   ✓ {len(proximos)} turno(s) programado(s):")
        for t in proximos:
            fecha_str = t['fecha'].strftime('%Y-%m-%d') if hasattr(t['fecha'], 'strftime') else str(t['fecha'])
            print(f"     [{fecha_str}] {t['nombre']} ({t['username']}) - {t['telefono']}")
    else:
        print("   ⚠ No hay turnos programados")

    print()

    # Test 4: Usuarios activos
    print("4. Listando usuarios con teléfono activo...")
    usuarios = turnos.get_todos_usuarios_activos()
    if usuarios:
        print(f"   ✓ {len(usuarios)} usuario(s) con teléfono:")
        for u in usuarios[:10]:  # Mostrar solo primeros 10
            print(f"     - {u['nombre']} ({u['username']}) - {u['telefono']}")
        if len(usuarios) > 10:
            print(f"     ... y {len(usuarios) - 10} más")
    else:
        print("   ⚠ No se encontraron usuarios")

    turnos.close()
    print()
    print("=" * 70)
    print("Test completado")
    print("=" * 70)
