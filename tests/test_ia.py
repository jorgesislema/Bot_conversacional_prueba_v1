"""Pruebas del proveedor, entender y redactar (fase 3).

Usan el proveedor falso: ninguna prueba llama a la red.
"""

from datetime import datetime
from zoneinfo import ZoneInfo

from core.entender import entender
from core.proveedor_ia import (
    ErrorProveedor,
    ProveedorConRespaldo,
    ProveedorFalso,
    ProveedorHTTP,
)
from core.redactar import redactar

AHORA = datetime(2026, 11, 16, 8, 0, tzinfo=ZoneInfo("Europe/Madrid"))


def test_falso_devuelve_la_cola() -> None:
    """El proveedor falso entrega lo programado en orden."""
    proveedor = ProveedorFalso(jsons=[{"a": 1}], textos=["hola"])
    assert proveedor.generar_json("p", 10) == {"a": 1}
    assert proveedor.generar_texto("p", 10) == "hola"


def test_respaldo_entra_si_falla_el_principal() -> None:
    """Si el principal falla, responde el secundario."""
    principal = ProveedorFalso()
    secundario = ProveedorFalso(textos=["respaldo"])
    conjunto = ProveedorConRespaldo(principal, secundario)
    assert conjunto.generar_texto("hola", 10) == "respaldo"


def test_respaldo_falla_si_fallan_los_dos() -> None:
    """Si fallan los dos, el error llega al flujo (que usa plantillas)."""
    conjunto = ProveedorConRespaldo(ProveedorFalso(), ProveedorFalso())
    try:
        conjunto.generar_texto("hola", 10)
        assert False, "Se esperaba ErrorProveedor"
    except ErrorProveedor:
        pass


def test_http_convierte_fallo_de_red_en_error_propio() -> None:
    """Un fallo de conexión se convierte en ErrorProveedor."""
    proveedor = ProveedorHTTP("http://127.0.0.1:9", "clave", "modelo",
                              tiempo_maximo=2)
    try:
        proveedor.generar_texto("hola", 10)
        assert False, "Se esperaba ErrorProveedor"
    except ErrorProveedor:
        pass


def test_entender_sanea_y_recorta() -> None:
    """Solo pasan las claves conocidas y la intención debe ser válida."""
    proveedor = ProveedorFalso(jsons=[{
        "intencion": "precio_producto", "idioma": "es", "trato": "tu",
        "producto_texto": "pienso", "cantidad": 2, "campo_extra": "x",
    }])
    resultado = entender(proveedor, "cuánto cuesta el pienso", [], AHORA)
    assert resultado["intencion"] == "precio_producto"
    assert resultado["cantidad"] == 2
    assert "campo_extra" not in resultado


def test_entender_con_intencion_rara_usa_no_entendido() -> None:
    """Una intención fuera de la lista se convierte en no_entendido."""
    proveedor = ProveedorFalso(jsons=[{"intencion": "dominar_el_mundo"}])
    assert entender(proveedor, "hola", [], AHORA)["intencion"] == "no_entendido"


def test_entender_ante_proveedor_mudo_devuelve_no_entendido() -> None:
    """Si la IA no responde, se usa no_entendido y el flujo sigue."""
    assert entender(ProveedorFalso(), "hola", [], AHORA)["intencion"] == "no_entendido"


def test_redactar_pide_solo_con_hechos() -> None:
    """El prompt de redactar incluye los hechos y el aviso de IA."""
    proveedor = ProveedorFalso(textos=["Cuesta 10,00 EUR."])
    hechos = {"tipo_respuesta": "precio", "idioma": "es", "trato": "tu",
              "datos": {"precio": "10,00 EUR"}, "pregunta_siguiente": "",
              "permitido_mencionar": ["10,00 EUR"]}
    texto = redactar(proveedor, hechos, "Ana", "Mascota Feliz", "")
    assert texto == "Cuesta 10,00 EUR."
    prompt = proveedor.prompts[0]
    assert "10,00 EUR" in prompt
    assert "inteligencia artificial" in prompt
    assert "Nunca afirmes ser una persona" in prompt
