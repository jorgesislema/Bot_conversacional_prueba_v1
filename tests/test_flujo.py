"""Pruebas del flujo completo sin interfaz (fase 4)."""

from datetime import date, datetime
from zoneinfo import ZoneInfo

from core.entender import entender
from core.esquema import iniciar_bd
from core.estado import Estado, crear_estado
from core.flujo import responder
from core.plantillas import cargar_textos
from core.proveedor_ia import ProveedorFalso

ZONA = ZoneInfo("Europe/Madrid")
LUNES = date(2026, 11, 16)
AHORA = datetime(2026, 11, 16, 8, 0, tzinfo=ZONA)

ENTENDIDO_PRECIO = {
    "intencion": "precio_producto", "idioma": "es", "trato": "tu",
    "producto_texto": "pienso perro adulto 15 kg", "servicio_texto": "",
    "veterinario_texto": "", "fecha": "", "hora": "", "franja": "",
    "cantidad": 0, "referencia": "ninguna",
}


def _entender_falso(entendido: dict):
    """Crea un entender que devuelve siempre el mismo JSON."""
    def _falso(proveedor, mensaje, historial, ahora):
        return entender(ProveedorFalso(jsons=[entendido]), mensaje,
                         historial, ahora)
    return _falso


def test_flujo_con_ia_valida() -> None:
    """Con texto válido de la IA, la respuesta sale con IA."""
    import core.flujo as flujo
    real = flujo.entender
    flujo.entender = _entender_falso(ENTENDIDO_PRECIO)
    try:
        proveedor = ProveedorFalso(
            textos=["El de 15 kg: 49,90 EUR, IVA incluido. Hay 12 en stock."])
        resultado = responder(iniciar_bd(LUNES), crear_estado(),
                              cargar_textos("es"), "cuánto cuesta",
                              AHORA, proveedor)
    finally:
        flujo.entender = real
    assert resultado.con_ia
    assert "49,90 EUR" in resultado.texto


def test_flujo_con_ia_mala_usa_respaldo() -> None:
    """Con texto inventado dos veces, cae al respaldo sin IA."""
    import core.flujo as flujo
    real = flujo.entender
    flujo.entender = _entender_falso(ENTENDIDO_PRECIO)
    try:
        proveedor = ProveedorFalso(textos=["Cuesta 10,00 EUR.", "Cuesta 10,00 EUR."])
        resultado = responder(iniciar_bd(LUNES), crear_estado(),
                              cargar_textos("es"), "cuánto cuesta",
                              AHORA, proveedor)
    finally:
        flujo.entender = real
    assert not resultado.con_ia
    assert "49,90 EUR" in resultado.texto


def test_flujo_sin_ia_usa_plantillas() -> None:
    """Sin proveedor, el bot responde con plantillas."""
    resultado = responder(iniciar_bd(LUNES), crear_estado(),
                          cargar_textos("es"), "hola", AHORA, None)
    assert not resultado.con_ia
    assert resultado.texto


def test_flujo_datos_personales_no_usan_ia() -> None:
    """Un teléfono recibe respuesta fija y no llega a la IA."""
    proveedor = ProveedorFalso(textos=["nunca debería usarse"])
    resultado = responder(iniciar_bd(LUNES), crear_estado(),
                          cargar_textos("es"), "llámame al 612345678",
                          AHORA, proveedor)
    assert resultado.tipo == "datos_personales"
    assert not resultado.con_ia
    assert proveedor.prompts == []


def test_flujo_respuestas_fijas_sin_ia() -> None:
    """Hablar con persona no pasa por la IA aunque haya proveedor."""
    import core.flujo as flujo
    real = flujo.entender
    flujo.entender = _entender_falso({**ENTENDIDO_PRECIO,
                                      "intencion": "hablar_con_persona"})
    try:
        proveedor = ProveedorFalso(textos=["nunca debería usarse"])
        resultado = responder(iniciar_bd(LUNES), crear_estado(),
                              cargar_textos("es"), "quiero hablar con alguien",
                              AHORA, proveedor)
    finally:
        flujo.entender = real
    assert resultado.tipo == "derivar"
    assert "900 000 000" in resultado.texto
    assert proveedor.prompts == []


def test_flujo_tope_bloquea() -> None:
    """Al llegar al tope, el chat se bloquea con mensaje fijo."""
    estado = crear_estado()
    estado.n_mensajes = 40
    resultado = responder(iniciar_bd(LUNES), estado, cargar_textos("es"),
                          "hola", AHORA, None)
    assert resultado.tope
    assert estado.n_mensajes == 40


def test_flujo_recorta_mensaje_largo() -> None:
    """Un mensaje de 600 caracteres se recorta y se avisa."""
    resultado = responder(iniciar_bd(LUNES), crear_estado(),
                          cargar_textos("es"), "x" * 600, AHORA, None)
    assert resultado.recortado


def test_flujo_sin_cupo_usa_plantillas() -> None:
    """Sin cupo diario, el modo degradado responde sin IA."""
    proveedor = ProveedorFalso(textos=["nunca debería usarse"])
    resultado = responder(iniciar_bd(LUNES), crear_estado(),
                          cargar_textos("es"), "cuánto cuesta",
                          AHORA, proveedor, cupo_diario=False)
    assert not resultado.con_ia
    assert resultado.tipo == "no_se"
    assert proveedor.prompts == []
