"""Pruebas de la dirección con enlace de Google Maps.

Comprueban que el bot da la dirección y el enlace de la base, que un
cambio en el panel se ve en el mensaje siguiente, que solo se aceptan
enlaces https y que el chat solo hace pulsables los enlaces del bot.
"""

from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from core.esquema import iniciar_bd
from core.estado import crear_estado
from core.flujo import responder
from core.plantillas import cargar_textos, respaldo
from core.proveedor_ia import ProveedorFalso
from core.reglas import enlace_mapa, resolver
from core.validador import validar
from ui.acciones import cambiar_direccion, datos_ubicacion
from ui.chat import html_conversacion

LUNES = date(2026, 11, 16)
AHORA = datetime(2026, 11, 16, 10, 0, tzinfo=ZoneInfo("Europe/Madrid"))
UBICACION = {"intencion": "ubicacion", "idioma": "es", "trato": "tu"}


def test_enlace_se_arma_con_la_direccion() -> None:
    """Sin enlace guardado, se usa la búsqueda pública de Google Maps."""
    enlace = enlace_mapa("Plaza Mayor 1, 28012 Madrid")
    assert enlace.startswith("https://www.google.com/maps/search/?api=1&query=")
    assert "Plaza+Mayor+1" in enlace


def test_enlace_guardado_solo_si_es_https() -> None:
    """Un enlace guardado que no es https se ignora."""
    assert enlace_mapa("X", "https://maps.app.goo.gl/abc") == "https://maps.app.goo.gl/abc"
    assert enlace_mapa("Calle 1", "javascript:alert(1)").startswith("https://www.google.com")


@pytest.mark.parametrize("idioma", ["es", "en"])
def test_respuesta_con_direccion_y_enlace(idioma: str) -> None:
    """La plantilla incluye la dirección y el enlace, y pasa el validador."""
    conn = iniciar_bd(LUNES)
    hechos = resolver(conn, crear_estado(idioma=idioma), dict(UBICACION, idioma=idioma), AHORA)
    assert hechos["tipo_respuesta"] == "ubicacion"
    textos = cargar_textos(idioma)
    for i in range(3):
        texto, _ = respaldo(hechos, textos, evitar_indice=i)
        assert "Plaza Mayor 1, 28012 Madrid" in texto
        assert hechos["datos"]["enlace"] in texto
        assert validar(texto, hechos, "Empezamos.", textos["frases_prohibidas"]) == []


def test_validador_rechaza_enlace_inventado() -> None:
    """Un enlace que no está en los hechos se rechaza."""
    conn = iniciar_bd(LUNES)
    hechos = resolver(conn, crear_estado(), UBICACION, AHORA)
    texto = "Estamos en Plaza Mayor 1, 28012 Madrid. Mapa: https://otro.example/mapa"
    assert "enlace_no_permitido" in validar(texto, hechos, "", [])


def test_ubicacion_no_pasa_por_la_ia() -> None:
    """La IA entiende, pero el texto con el enlace sale fijo de la plantilla."""
    conn = iniciar_bd(LUNES)
    proveedor = ProveedorFalso(jsons=[UBICACION], textos=["Estamos en otro sitio."])
    resultado = responder(conn, crear_estado(), cargar_textos("es"), "donde estan",
                          AHORA, proveedor)
    assert "Plaza Mayor 1" in resultado.texto
    assert "otro sitio" not in resultado.texto


def test_cambio_de_direccion_en_caliente() -> None:
    """La dirección nueva del panel se usa en el mensaje siguiente."""
    conn = iniciar_bd(LUNES)
    cambio = cambiar_direccion(conn, "Gran Vía 20, 28013 Madrid")
    assert cambio.pregunta("es") == "Dónde están?"
    hechos = resolver(conn, crear_estado(), UBICACION, AHORA)
    assert hechos["datos"]["direccion"] == "Gran Vía 20, 28013 Madrid"
    assert "Gran+V%C3%ADa+20" in hechos["datos"]["enlace"]
    cambiar_direccion(conn, "Gran Vía 20, 28013 Madrid", "https://maps.app.goo.gl/xyz")
    assert datos_ubicacion(conn)[1] == "https://maps.app.goo.gl/xyz"


@pytest.mark.parametrize(
    ("direccion", "enlace", "error"),
    [
        ("abc", "", "error_direccion"),
        ("Calle Real 3, Madrid", "http://maps.example", "error_enlace"),
        ("Calle Real 3, Madrid", "javascript:alert(1)", "error_enlace"),
        ("Calle Real 3, Madrid", 'https://x.example/"onmouseover=', "error_enlace"),
    ],
)
def test_cambiar_direccion_valida(direccion: str, enlace: str, error: str) -> None:
    """Dirección corta o enlace no https: error y sin cambios."""
    conn = iniciar_bd(LUNES)
    with pytest.raises(ValueError, match=error):
        cambiar_direccion(conn, direccion, enlace)
    assert datos_ubicacion(conn)[0] == "Plaza Mayor 1, 28012 Madrid"


def test_chat_enlace_pulsable_solo_en_el_bot() -> None:
    """El enlace del bot es pulsable; el del cliente queda como texto."""
    salida = html_conversacion([
        {"rol": "asistente", "texto": "Mapa: https://www.google.com/maps/search/?api=1&query=A."},
        {"rol": "usuario", "texto": "mira https://malo.example"},
    ], "Hoy")
    assert 'href="https://www.google.com/maps/search/?api=1&amp;query=A"' in salida
    assert 'rel="noopener noreferrer"' in salida
    assert 'href="https://malo.example"' not in salida
