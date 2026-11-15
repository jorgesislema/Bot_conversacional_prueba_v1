"""Pruebas del cálculo de huecos (fase 1).

Cubren rejilla de 15 minutos, solapes, días cerrados, fechas pasadas
y encaje dentro de turnos.
"""

from datetime import date, datetime
from zoneinfo import ZoneInfo

from core.esquema import iniciar_bd
from core.huecos import dia_abierto, huecos_disponibles, siguiente_dia_abierto

ZONA = ZoneInfo("Europe/Madrid")
LUNES = date(2026, 11, 16)
AHORA = datetime(2026, 11, 16, 8, 0, tzinfo=ZONA)


def test_huecos_en_rejilla_de_15_minutos() -> None:
    """Todos los huecos empiezan en minutos múltiplos de 15."""
    conn = iniciar_bd(LUNES)
    huecos = huecos_disponibles(conn, date(2026, 11, 17), 30, None, AHORA)
    assert huecos
    for hueco in huecos:
        assert hueco.inicio.minute % 15 == 0
        assert (hueco.fin - hueco.inicio).seconds // 60 == 30


def test_huecos_dentro_del_turno() -> None:
    """Los huecos de Marta en lunes caen entre las 09:00 y las 14:00."""
    conn = iniciar_bd(LUNES)
    huecos = huecos_disponibles(conn, date(2026, 11, 17), 30, 1, AHORA)
    assert huecos
    for hueco in huecos:
        assert hueco.inicio.strftime("%H:%M") >= "09:00"
        assert hueco.fin.strftime("%H:%M") <= "14:00"


def test_solape_con_cita_ocupada_excluido() -> None:
    """Un hueco ocupado por una cita no se ofrece, pero el anterior sí."""
    conn = iniciar_bd(LUNES)
    # Se borran las citas de ejemplo para que el caso sea determinista.
    conn.execute("DELETE FROM citas")
    conn.execute(
        "INSERT INTO citas (veterinario_id, servicio_id, inicio, fin, alias_cliente)"
        " VALUES (1, 1, '2026-11-17T10:00', '2026-11-17T10:30', 'Prueba')"
    )
    huecos = huecos_disponibles(conn, date(2026, 11, 17), 30, 1, AHORA)
    inicios = [h.inicio.strftime("%H:%M") for h in huecos]
    assert "10:00" not in inicios
    assert "09:45" not in inicios  # Se solapa por detrás.
    assert "09:30" in inicios  # Termina justo al empezar la cita.


def test_domingo_cerrado_sin_huecos() -> None:
    """El domingo no hay huecos porque el negocio cierra."""
    conn = iniciar_bd(LUNES)
    domingo = date(2026, 11, 22)
    assert not dia_abierto(conn, domingo)
    assert huecos_disponibles(conn, domingo, 30, None, AHORA) == []


def test_festivo_cerrado_sin_huecos() -> None:
    """El 25 de diciembre no hay huecos y se propone el día abierto siguiente."""
    conn = iniciar_bd(LUNES)
    navidad = date(2026, 12, 25)
    assert not dia_abierto(conn, navidad)
    assert huecos_disponibles(conn, navidad, 30, None, AHORA) == []
    siguiente = siguiente_dia_abierto(conn, navidad)
    assert siguiente > navidad
    assert dia_abierto(conn, siguiente)


def test_fecha_pasada_sin_huecos() -> None:
    """Una fecha anterior a hoy nunca ofrece huecos."""
    conn = iniciar_bd(LUNES)
    ayer = date(2026, 11, 15)
    assert huecos_disponibles(conn, ayer, 30, None, AHORA) == []


def test_limpieza_dental_solo_con_pablo() -> None:
    """Un servicio de 60 min con Pablo el sábado cabe en su turno."""
    conn = iniciar_bd(LUNES)
    sabado = date(2026, 11, 21)
    huecos = huecos_disponibles(conn, sabado, 60, 2, AHORA)
    assert huecos
    for hueco in huecos:
        assert hueco.fin.strftime("%H:%M") <= "14:00"
