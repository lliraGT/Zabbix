# horarios.py
# Módulo para determinar responsable según horario y día

from datetime import datetime, time, timedelta
import logging

logger = logging.getLogger(__name__)

class GestorHorarios:
    """Determina quién es responsable según horario y día de la semana"""

    # Definición de horarios
    HORARIO_LABORAL_INICIO = time(8, 0)      # 08:00
    HORARIO_LABORAL_FIN = time(17, 0)        # 17:00
    HORARIO_VIERNES_FIN = time(14, 0)        # 14:00 (viernes)

    @staticmethod
    def es_horario_laboral(momento: datetime = None) -> bool:
        """
        Determina si estamos en horario laboral

        Args:
            momento: Datetime a evaluar (default: ahora)

        Returns:
            True si es horario laboral, False si es fuera de horario
        """
        if momento is None:
            momento = datetime.now()

        dia_semana = momento.weekday()  # 0=Lunes, 6=Domingo
        hora_actual = momento.time()

        # Sábado (5) o Domingo (6) → Siempre fuera de horario
        if dia_semana in [5, 6]:
            return False

        # Viernes (4) → Horario laboral hasta 14:00
        if dia_semana == 4:
            return GestorHorarios.HORARIO_LABORAL_INICIO <= hora_actual < GestorHorarios.HORARIO_VIERNES_FIN

        # Lunes (0) a Jueves (3) → Horario laboral 08:00 - 17:00
        return GestorHorarios.HORARIO_LABORAL_INICIO <= hora_actual < GestorHorarios.HORARIO_LABORAL_FIN

    @staticmethod
    def get_fecha_turno_activo(momento: datetime = None) -> datetime:
        """
        Determina qué fecha de turno consultar en TFSS_TURNOS

        Lógica corregida:
        - Lun-Jue 17:00-23:59 → Turno del día actual
        - Lun-Jue 00:00-08:00 → Turno del día anterior (turno que inició ayer)
        - Vie 14:00-23:59 → Turno del viernes
        - Sáb 00:00-23:59 → Turno del sábado
        - Dom 00:00-23:59 → Turno del domingo
        - Lun 00:00-08:00 → Turno del domingo (termina lunes 08:00)
        - Lun 08:00-17:00 → HORARIO LABORAL (usa tag Encargado)
        - Lun 17:00-23:59 → Turno del lunes (nuevo turno nocturno)

        Args:
            momento: Datetime a evaluar (default: ahora)

        Returns:
            Fecha del turno a consultar en TFSS_TURNOS
        """
        if momento is None:
            momento = datetime.now()

        dia_semana = momento.weekday()  # 0=Lunes, 6=Domingo
        hora_actual = momento.time()

        # Función auxiliar para crear fecha sin hora
        def fecha_sin_hora(dt: datetime) -> datetime:
            return dt.replace(hour=0, minute=0, second=0, microsecond=0)

        # Sábado (5) → Buscar turno del sábado
        if dia_semana == 5:
            fecha_turno = fecha_sin_hora(momento)
            logger.debug(f"Sábado → Buscar turno del sábado {fecha_turno.date()}")
            return fecha_turno

        # Domingo (6) → Buscar turno del domingo
        if dia_semana == 6:
            fecha_turno = fecha_sin_hora(momento)
            logger.debug(f"Domingo → Buscar turno del domingo {fecha_turno.date()}")
            return fecha_turno

        # Lunes (0) antes de las 08:00 → Buscar turno del domingo
        if dia_semana == 0 and hora_actual < GestorHorarios.HORARIO_LABORAL_INICIO:
            fecha_turno = fecha_sin_hora(momento) - timedelta(days=1)
            logger.debug(f"Lunes antes de 08:00 → Buscar turno del domingo {fecha_turno.date()}")
            return fecha_turno

        # Martes-Viernes antes de las 08:00 → Buscar turno del día anterior
        if dia_semana in [1, 2, 3, 4] and hora_actual < GestorHorarios.HORARIO_LABORAL_INICIO:
            fecha_turno = fecha_sin_hora(momento) - timedelta(days=1)
            logger.debug(f"Entre semana antes de 08:00 → Buscar turno de ayer {fecha_turno.date()}")
            return fecha_turno

        # Viernes después de 14:00 → Buscar turno del viernes
        if dia_semana == 4 and hora_actual >= GestorHorarios.HORARIO_VIERNES_FIN:
            fecha_turno = fecha_sin_hora(momento)
            logger.debug(f"Viernes después de 14:00 → Buscar turno del viernes {fecha_turno.date()}")
            return fecha_turno

        # Lunes-Jueves después de 17:00 → Buscar turno del día actual
        if dia_semana in [0, 1, 2, 3] and hora_actual >= GestorHorarios.HORARIO_LABORAL_FIN:
            fecha_turno = fecha_sin_hora(momento)
            logger.debug(f"Entre semana después de 17:00 → Buscar turno de hoy {fecha_turno.date()}")
            return fecha_turno

        # Por defecto (horario laboral) → Retornar None para indicar usar tag Encargado
        logger.debug(f"Horario laboral → Usar tag Encargado (no consultar turno)")
        return None

    @staticmethod
    def get_descripcion_horario(momento: datetime = None) -> str:
        """Retorna descripción legible del horario actual"""
        if momento is None:
            momento = datetime.now()

        if GestorHorarios.es_horario_laboral(momento):
            return "HORARIO LABORAL (usar tag Encargado)"
        else:
            return "FUERA DE HORARIO (usar turno on-call)"


# Test del módulo
if __name__ == "__main__":
    print("=" * 70)
    print("TEST DE LÓGICA DE HORARIOS")
    print("=" * 70)
    print()

    # Casos de prueba
    casos = [
        ("2026-01-13 09:00:00", "Lunes 09:00 - Horario laboral"),
        ("2026-01-13 18:00:00", "Lunes 18:00 - Turno nocturno"),
        ("2026-01-14 07:00:00", "Martes 07:00 - Turno nocturno (del lunes)"),
        ("2026-01-14 10:00:00", "Martes 10:00 - Horario laboral"),
        ("2026-01-16 10:00:00", "Viernes 10:00 - Horario laboral"),
        ("2026-01-16 15:00:00", "Viernes 15:00 - Fin de semana inicia"),
        ("2026-01-17 10:00:00", "Sábado 10:00 - Fin de semana"),
        ("2026-01-18 20:00:00", "Domingo 20:00 - Fin de semana"),
        ("2026-01-19 07:00:00", "Lunes 07:00 - Turno domingo termina"),
        ("2026-01-19 09:00:00", "Lunes 09:00 - Horario laboral retoma"),
        ("2026-01-19 18:00:00", "Lunes 18:00 - Turno nocturno nuevo"),
    ]

    for fecha_str, desc in casos:
        momento = datetime.strptime(fecha_str, "%Y-%m-%d %H:%M:%S")
        es_laboral = GestorHorarios.es_horario_laboral(momento)
        fecha_turno = GestorHorarios.get_fecha_turno_activo(momento)
        descripcion = GestorHorarios.get_descripcion_horario(momento)

        print(f"{desc}")
        print(f"  Momento: {momento.strftime('%Y-%m-%d %H:%M')} ({momento.strftime('%A')})")
        print(f"  Tipo: {descripcion}")

        if fecha_turno:
            print(f"  Consultar turno: {fecha_turno.strftime('%Y-%m-%d')} ({fecha_turno.strftime('%A')})")
        else:
            print(f"  Consultar: Tag Encargado de Zabbix")
        print()

    print("=" * 70)
