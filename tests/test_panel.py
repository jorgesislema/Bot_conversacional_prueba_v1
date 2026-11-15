"""Pruebas del panel: validación y cambio en caliente (fase 4)."""

from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from core.esquema import iniciar_bd
from core.estado import crear_estado
from core.reglas import resolver
from ui.panel import (
    cargar_tabla,
    euros_a_centimos,
    guardar_tabla,
    resumen_ventas,
    validar_horas,
    validar_stock,
)

LUNES = date(2026, 11, 16)
AHORA = datetime(2026, 11, 16, 8, 0, tzinfo=ZoneInfo("Europe/Madrid"))


def test_euros_a_centimos_con_coma_y_punto() -> None:
    """Acepta coma o punto decimal."""
    assert euros_a_centimos("49,90") == 4990
    assert euros_a_centimos("49.90") == 4990
    assert euros_a_centimos("30") == 3000


def test_euros_rechaza_negativos_y_texto() -> None:
    """Un precio negativo o no numérico da error_precio."""
    with pytest.raises(ValueError, match="error_precio"):
        euros_a_centimos("-5")
    with pytest.raises(ValueError, match="error_precio"):
        euros_a_centimos("mucho")


def test_stock_rechaza_decimales_y_negativos() -> None:
    """El stock debe ser entero mayor o igual a cero."""
    assert validar_stock(3) == 3
    with pytest.raises(ValueError, match="error_stock"):
        validar_stock(-1)
    with pytest.raises(ValueError, match="error_stock"):
        validar_stock("3,5")


def test_horas_rechaza_cierre_anterior() -> None:
    """El cierre debe ser posterior a la apertura."""
    validar_horas("09:00", "14:00")
    with pytest.raises(ValueError, match="error_horas"):
        validar_horas("14:00", "09:00")


def test_guardar_precio_y_bot_responde_nuevo() -> None:
    """Cambio en caliente: el bot da el precio nuevo enseguida."""
    conn = iniciar_bd(LUNES)
    original = cargar_tabla(conn, "productos")
    editado = original.copy()
    editado.loc[editado["sku"] == "P002", "precio_eur"] = 44.90
    assert guardar_tabla(conn, "productos", original, editado,
                         ("nombre_es", "nombre_en", "descripcion_es",
                          "descripcion_en", "precio_eur", "stock")) == 1
    hechos = resolver(conn, crear_estado(), {
        "intencion": "precio_producto", "idioma": "es", "trato": "tu",
        "producto_texto": "pienso perro adulto 15 kg"}, AHORA)
    assert hechos["datos"]["precio"] == "44,90 EUR"


def test_guardar_rechaza_stock_negativo() -> None:
    """Un stock negativo no se guarda."""
    conn = iniciar_bd(LUNES)
    original = cargar_tabla(conn, "productos")
    editado = original.copy()
    editado.loc[editado["sku"] == "P002", "stock"] = -2
    with pytest.raises(ValueError, match="error_stock"):
        guardar_tabla(conn, "productos", original, editado, ("stock",))
    fila = conn.execute("SELECT stock FROM productos WHERE sku = 'P002'").fetchone()
    assert fila["stock"] == 12


def test_guardar_registra_evento() -> None:
    """Cada guardado deja rastro en registro_eventos."""
    conn = iniciar_bd(LUNES)
    original = cargar_tabla(conn, "productos")
    editado = original.copy()
    editado.loc[editado["sku"] == "P001", "stock"] = 99
    guardar_tabla(conn, "productos", original, editado, ("stock",))
    fila = conn.execute(
        "SELECT detalle FROM registro_eventos ORDER BY id DESC LIMIT 1").fetchone()
    assert "productos" in fila["detalle"]


def test_resumen_ventas_muestra_pedidos() -> None:
    """Las ventas registradas aparecen en la pestaña de ventas."""
    conn = iniciar_bd(LUNES)
    conn.execute("INSERT INTO ventas (producto_id, cantidad, total_centimos,"
                 " creado) VALUES (2, 2, 9980, '2026-11-16T10:00')")
    ventas, _ = resumen_ventas(conn)
    assert len(ventas) == 1
    assert ventas.iloc[0]["total_eur"] == 99.80
