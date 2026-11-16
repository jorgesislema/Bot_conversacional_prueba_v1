"""Pruebas del panel "Prueba el motor" y del chat en forma de teléfono.

Comprueban que cada acción guiada valida, guarda, deja registro y que el
bot ve el dato nuevo en el mensaje siguiente; y que el HTML del chat
escapa lo que escribe el visitante y muestra siempre la etiqueta de IA.
"""

from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from core.esquema import iniciar_bd
from core.estado import crear_estado
from core.huecos import dia_abierto
from core.reglas import buscar_productos, resolver
from ui.acciones import (
    anadir_producto,
    cambiar_horario,
    cambiar_precio,
    formatear_euros,
    horario_de,
    productos_para_selector,
    ultimos_cambios,
)
from ui.chat import html_barra, html_conversacion

LUNES = date(2026, 11, 16)
AHORA = datetime(2026, 11, 16, 8, 0, tzinfo=ZoneInfo("Europe/Madrid"))


def test_formatear_euros_por_idioma() -> None:
    """Coma decimal en ES y punto en EN."""
    assert formatear_euros(4990) == "49,90 EUR"
    assert formatear_euros(4990, "en") == "49.90 EUR"


def test_cambiar_precio_y_el_bot_lo_ve() -> None:
    """El precio nuevo llega a los hechos del bot sin reiniciar nada."""
    conn = iniciar_bd(LUNES)
    cambio = cambiar_precio(conn, 2, "44,90")
    assert "49,90 EUR -> 44,90 EUR" in cambio.resumen
    assert "15 kg" in cambio.pregunta("es")
    hechos = resolver(conn, crear_estado(), {
        "intencion": "precio_producto", "idioma": "es", "trato": "tu",
        "producto_texto": "pienso perro adulto 15 kg"}, AHORA)
    assert "44,90" in str(hechos)
    assert ultimos_cambios(conn)[0] == cambio.resumen


def test_cambiar_precio_invalido_no_guarda() -> None:
    """Precio negativo o texto: error y sin cambios."""
    conn = iniciar_bd(LUNES)
    with pytest.raises(ValueError, match="error_precio"):
        cambiar_precio(conn, 2, "-3")
    with pytest.raises(ValueError, match="error_producto"):
        cambiar_precio(conn, 9999, "3")
    assert ultimos_cambios(conn) == []


def test_anadir_producto_y_el_bot_lo_encuentra() -> None:
    """Un producto nuevo se encuentra por su nombre al instante."""
    conn = iniciar_bd(LUNES)
    cambio = anadir_producto(conn, "Snack dental para gatos", "snacks", "6,20", 30)
    assert "6,20 EUR" in cambio.resumen
    encontrados = buscar_productos(conn, "snack dental gatos", "es")
    assert any(p["nombre_es"] == "Snack dental para gatos" for p in encontrados)
    assert any("Snack dental para gatos" in o[1] for o in productos_para_selector(conn, "es"))


@pytest.mark.parametrize(
    ("nombre", "categoria", "euros", "stock", "error"),
    [
        ("ab", "snacks", "1", 1, "error_nombre"),
        ("Producto raro", "coches", "1", 1, "error_categoria"),
        ("Producto raro", "snacks", "uno", 1, "error_precio"),
        ("Producto raro", "snacks", "1", -2, "error_stock"),
        ("Cepillo suave", "higiene", "1", 1, "error_nombre_repetido"),
    ],
)
def test_anadir_producto_valida(nombre: str, categoria: str, euros: str,
                                stock: int, error: str) -> None:
    """Cada dato inválido da su propio error traducible."""
    conn = iniciar_bd(LUNES)
    with pytest.raises(ValueError, match=error):
        anadir_producto(conn, nombre, categoria, euros, stock)


def test_cambiar_horario_abrir_y_cerrar() -> None:
    """Cerrar un día lo deja sin horario; abrir el domingo lo habilita."""
    conn = iniciar_bd(LUNES)
    cambio = cambiar_horario(conn, 5, "10:00", "15:00")
    assert horario_de(conn, 5) == ("10:00", "15:00")
    assert "sábado" in cambio.pregunta("es")
    cambiar_horario(conn, 0, "", "", cerrado=True)
    assert horario_de(conn, 0) is None
    assert not dia_abierto(conn, LUNES)
    cambiar_horario(conn, 6, "10:00", "13:00")
    assert dia_abierto(conn, date(2026, 11, 22))


def test_cambiar_horario_invalido() -> None:
    """Cierre antes de apertura o formato malo: error."""
    conn = iniciar_bd(LUNES)
    with pytest.raises(ValueError, match="error_horas"):
        cambiar_horario(conn, 1, "14:00", "09:00")
    with pytest.raises(ValueError, match="error_horas"):
        cambiar_horario(conn, 9, "09:00", "14:00")


def test_chat_escapa_html_del_visitante() -> None:
    """Un mensaje con etiquetas no se interpreta como HTML."""
    salida = html_conversacion(
        [{"rol": "usuario", "texto": "<script>alert(1)</script>", "hora": "10:00"}], "Hoy")
    assert "<script>" not in salida
    assert "&lt;script&gt;" in salida
    assert "mf-cliente" in salida


def test_chat_burbujas_por_rol_y_saltos_de_linea() -> None:
    """Bot a la izquierda, cliente a la derecha, listas con saltos."""
    salida = html_conversacion([
        {"rol": "asistente", "texto": "Tenemos:\n- A\n- B"},
        {"rol": "usuario", "texto": "gracias"},
    ], "Hoy")
    assert salida.index("mf-bot") < salida.index("mf-cliente")
    assert "<br>" in salida


def test_barra_muestra_siempre_la_etiqueta_ia() -> None:
    """La etiqueta de IA va fija en la barra del teléfono (art. 50)."""
    barra = html_barra("Ana", "en línea", "Asistente con IA")
    assert "Asistente con IA" in barra
    assert ">A<" in barra
