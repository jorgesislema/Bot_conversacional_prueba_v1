"""Calcula citas libres a partir de turnos, horario y citas ocupadas.

Qué hace: genera huecos en rejilla de 15 minutos que quepan dentro del
turno del veterinario y del horario del negocio, sin solaparse con
otras citas. Recibe: conexión SQLite, fecha, duración y veterinario
opcional. Devuelve: lista de huecos disponibles. Qué NO hace: no escribe
texto ni reserva citas (la reserva con confirmación es de reglas.py).
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

ZONA = ZoneInfo("Europe/Madrid")
PASO_MINUTOS = 15


@dataclass(frozen=True)
class Hueco:
    """Hueco libre para una cita."""

    inicio: datetime
    fin: datetime
    veterinario_id: int


def _ahora_local(ahora: datetime) -> datetime:
    """Convierte un instante a hora local de Madrid sin zona horaria."""
    return ahora.astimezone(ZONA).replace(tzinfo=None)


def _a_minutos(hora: str) -> int:
    """Convierte HH:MM en minutos desde medianoche."""
    horas, minutos = (int(x) for x in hora.split(":"))
    return horas * 60 + minutos


def dia_abierto(conn: sqlite3.Connection, dia: date) -> bool:
    """Indica si el negocio abre ese día (horario más días especiales).

    Parámetros:
        conn: conexión SQLite con la semilla cargada.
        dia: fecha a consultar.
    Devuelve: falso si es domingo, festivo cerrado o sin horario.
    Ejemplo:
        >>> dia_abierto(iniciar_bd(date(2026, 11, 16)), date(2026, 11, 16))
        True
    """
    especial = conn.execute(
        "SELECT cerrado, hora_apertura, hora_cierre FROM dias_especiales WHERE fecha = ?",
        (dia.isoformat(),),
    ).fetchone()
    if especial is not None:
        if especial["cerrado"]:
            return False
        return True
    fila = conn.execute(
        "SELECT 1 FROM horarios_negocio WHERE dia_semana = ?",
        (dia.weekday(),),
    ).fetchone()
    return fila is not None


def siguiente_dia_abierto(conn: sqlite3.Connection, dia: date) -> date:
    """Devuelve el siguiente día con apertura, empezando por el dado.

    Parámetros:
        conn: conexión SQLite con la semilla cargada.
        dia: fecha desde la que buscar.
    Devuelve: la primera fecha abierta (como mucho 366 días después).
    Errores:
        ValueError si no hay ningún día abierto en un año.
    Ejemplo:
        >>> from datetime import date
        >>> siguiente_dia_abierto(iniciar_bd(date(2026, 11, 16)), date(2026, 12, 25))
        datetime.date(2026, 12, 26)
    """
    candidato = dia
    for _ in range(366):
        if dia_abierto(conn, candidato):
            return candidato
        candidato += timedelta(days=1)
    raise ValueError("sin días abiertos en un año")


def huecos_disponibles(
    conn: sqlite3.Connection,
    dia: date,
    duracion_min: int,
    veterinario_id: int | None,
    ahora: datetime,
) -> list[Hueco]:
    """Calcula los huecos libres de un día en rejilla de 15 minutos.

    Parámetros:
        conn: conexión SQLite con la semilla cargada.
        dia: fecha a consultar.
        duracion_min: duración del servicio en minutos.
        veterinario_id: veterinario concreto o None para cualquiera.
        ahora: instante actual (manda la hora de Madrid).
    Devuelve: huecos ordenados por hora de inicio.
    Ejemplo:
        >>> conn = iniciar_bd(date(2026, 11, 16))
        >>> huecos = huecos_disponibles(conn, date(2026, 11, 17), 30, 1,
        ...     datetime(2026, 11, 16, 10, 0, tzinfo=ZoneInfo("Europe/Madrid")))
        >>> len(huecos) > 0
        True
    """
    ahora_local = _ahora_local(ahora)
    if dia < ahora_local.date() or not dia_abierto(conn, dia):
        return []
    negocio = conn.execute(
        "SELECT hora_apertura, hora_cierre FROM horarios_negocio WHERE dia_semana = ?",
        (dia.weekday(),),
    ).fetchone()
    if negocio is None:
        return []
    especial = conn.execute(
        "SELECT hora_apertura, hora_cierre FROM dias_especiales"
        " WHERE fecha = ? AND cerrado = 0",
        (dia.isoformat(),),
    ).fetchone()
    apertura = especial["hora_apertura"] if especial else negocio["hora_apertura"]
    cierre = especial["hora_cierre"] if especial else negocio["hora_cierre"]
    ap_min = _a_minutos(str(apertura))
    ci_min = _a_minutos(str(cierre))

    if veterinario_id is None:
        filas_turnos = conn.execute(
            "SELECT veterinario_id, hora_inicio, hora_fin FROM turnos"
            " WHERE dia_semana = ? AND veterinario_id IN"
            " (SELECT id FROM veterinarios WHERE activo = 1)",
            (dia.weekday(),),
        ).fetchall()
    else:
        filas_turnos = conn.execute(
            "SELECT veterinario_id, hora_inicio, hora_fin FROM turnos"
            " WHERE dia_semana = ? AND veterinario_id = ?"
            " AND veterinario_id IN (SELECT id FROM veterinarios WHERE activo = 1)",
            (dia.weekday(), veterinario_id),
        ).fetchall()

    citas = conn.execute(
        "SELECT veterinario_id, inicio, fin FROM citas"
        " WHERE substr(inicio, 1, 10) = ?",
        (dia.isoformat(),),
    ).fetchall()

    huecos: list[Hueco] = []
    for turno in filas_turnos:
        ini = max(_a_minutos(str(turno["hora_inicio"])), ap_min)
        fin = min(_a_minutos(str(turno["hora_fin"])), ci_min)
        # La cita debe caber entera: el último inicio posible es fin menos duración.
        tope = fin - duracion_min
        minuto = ini - (ini % PASO_MINUTOS)
        if minuto < ini:
            minuto += PASO_MINUTOS
        while minuto <= tope:
            inicio = datetime(dia.year, dia.month, dia.day, minuto // 60, minuto % 60)
            fin_hueco = inicio + timedelta(minutes=duracion_min)
            if inicio >= ahora_local and not _solapa(
                [c for c in citas if c["veterinario_id"] == turno["veterinario_id"]],
                inicio,
                fin_hueco,
            ):
                huecos.append(Hueco(inicio, fin_hueco, int(turno["veterinario_id"])))
            minuto += PASO_MINUTOS
    huecos.sort(key=lambda h: (h.inicio, h.veterinario_id))
    return huecos


def huecos_negocio(
    conn: sqlite3.Connection, dia: date, duracion_min: int, ahora: datetime
) -> list[Hueco]:
    """Calcula huecos dentro del horario del negocio, sin veterinario.

    Por qué existe: la peluquería se atiende en horario del negocio sin
    veterinario asignado (ver 04, servicios).
    """
    ahora_local = _ahora_local(ahora)
    if dia < ahora_local.date() or not dia_abierto(conn, dia):
        return []
    negocio = conn.execute(
        "SELECT hora_apertura, hora_cierre FROM horarios_negocio WHERE dia_semana = ?",
        (dia.weekday(),),
    ).fetchone()
    if negocio is None:
        return []
    especial = conn.execute(
        "SELECT hora_apertura, hora_cierre FROM dias_especiales"
        " WHERE fecha = ? AND cerrado = 0",
        (dia.isoformat(),),
    ).fetchone()
    apertura = especial["hora_apertura"] if especial else negocio["hora_apertura"]
    cierre = especial["hora_cierre"] if especial else negocio["hora_cierre"]
    citas = conn.execute(
        "SELECT inicio, fin FROM citas WHERE veterinario_id IS NULL"
        " AND substr(inicio, 1, 10) = ?",
        (dia.isoformat(),),
    ).fetchall()
    huecos: list[Hueco] = []
    minuto = _a_minutos(str(apertura))
    tope = _a_minutos(str(cierre)) - duracion_min
    if minuto % PASO_MINUTOS:
        minuto += PASO_MINUTOS - (minuto % PASO_MINUTOS)
    while minuto <= tope:
        inicio = datetime(dia.year, dia.month, dia.day, minuto // 60, minuto % 60)
        fin_hueco = inicio + timedelta(minutes=duracion_min)
        if inicio >= ahora_local and not _solapa(citas, inicio, fin_hueco):
            huecos.append(Hueco(inicio, fin_hueco, 0))
        minuto += PASO_MINUTOS
    return huecos


def _solapa(
    citas: list[sqlite3.Row], inicio: datetime, fin: datetime
) -> bool:
    """Indica si un intervalo choca con alguna cita existente."""
    for cita in citas:
        ini_cita = datetime.fromisoformat(str(cita["inicio"]))
        fin_cita = datetime.fromisoformat(str(cita["fin"]))
        if inicio < fin_cita and fin > ini_cita:
            return True
    return False
