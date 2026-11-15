"""Pruebas de las reglas de negocio (fase 2).

Cada prueba usa una base nueva: el bot nunca inventa datos y todo sale
de la sesión.
"""

from datetime import date, datetime
from zoneinfo import ZoneInfo

from core.esquema import iniciar_bd
from core.estado import crear_estado
from core.reglas import buscar_productos, formatear_precio, nombre_dia, resolver

ZONA = ZoneInfo("Europe/Madrid")
LUNES = date(2026, 11, 16)
AHORA = datetime(2026, 11, 16, 8, 0, tzinfo=ZONA)


def _entendido(intencion: str, **campos: object) -> dict:
    """Arma un entendido mínimo para las pruebas."""
    base: dict = {
        "intencion": intencion, "idioma": "es", "trato": "tu",
        "producto_texto": "", "servicio_texto": "", "veterinario_texto": "",
        "fecha": "", "hora": "", "franja": "", "cantidad": 0, "referencia": "ninguna",
    }
    base.update(campos)
    return base


def test_precio_pienso_15kg() -> None:
    """El pienso de 15 kg cuesta 49,90 EUR con IVA incluido."""
    conn = iniciar_bd(LUNES)
    hechos = resolver(conn, crear_estado(), _entendido("precio_producto",
                      producto_texto="pienso perro adulto 15 kg"), AHORA)
    assert hechos["tipo_respuesta"] == "precio"
    assert hechos["datos"]["precio"] == "49,90 EUR"
    assert "49,90 EUR" in hechos["permitido_mencionar"]


def test_tolera_faltas_de_escritura() -> None:
    """'cepilo' encuentra el cepillo suave."""
    conn = iniciar_bd(LUNES)
    assert buscar_productos(conn, "cepilo", "es")[0]["sku"] == "P013"


def test_pide_aclaracion_con_dos_piensos() -> None:
    """Dos candidatos guardan la lista para "el grande"."""
    conn = iniciar_bd(LUNES)
    estado = crear_estado()
    hechos = resolver(conn, estado, _entendido("precio_producto",
                      producto_texto="pienso perro adulto"), AHORA)
    assert hechos["tipo_respuesta"] == "aclaracion_producto"
    skus = {c for c in estado.candidatos}
    assert len(skus) >= 2
    hechos2 = resolver(conn, estado, _entendido("precio_producto",
                       referencia="el_grande"), AHORA)
    assert hechos2["datos"]["precio"] == "49,90 EUR"


def test_cambio_de_precio_en_caliente() -> None:
    """Si el panel cambia el precio, el mensaje siguiente trae el nuevo."""
    conn = iniciar_bd(LUNES)
    conn.execute("UPDATE productos SET precio_centimos = 4490 WHERE sku = 'P002'")
    hechos = resolver(conn, crear_estado(), _entendido("precio_producto",
                      producto_texto="pienso perro adulto 15 kg"), AHORA)
    assert hechos["datos"]["precio"] == "44,90 EUR"


def test_producto_nuevo_en_caliente() -> None:
    """Un producto agregado en el panel se encuentra enseguida."""
    conn = iniciar_bd(LUNES)
    conn.execute(
        "INSERT INTO productos (sku, nombre_es, nombre_en, descripcion_es,"
        " descripcion_en, categoria, marca, precio_centimos, stock)"
        " VALUES ('P021', 'Snack dental para gatos', 'Dental snack for cats',"
        " 'Snack para gatos.', 'Cat snack.', 'snacks', 'DentiPet', 620, 30)")
    encontrados = buscar_productos(conn, "snack dental gato", "es")
    assert encontrados[0]["sku"] == "P021"


def test_sin_stock_ofrece_alternativa() -> None:
    """Sin stock dice que no hay y ofrece otro de la misma categoría."""
    conn = iniciar_bd(LUNES)
    hechos = resolver(conn, crear_estado(), _entendido("disponibilidad",
                      producto_texto="antiparasitario perro grande"), AHORA)
    assert hechos["tipo_respuesta"] == "stock"
    assert hechos["datos"]["stock"] == 0
    assert "alternativa" in hechos["datos"]


def test_stock_bajo_avisa() -> None:
    """Con 3 unidades devuelve el número exacto."""
    conn = iniciar_bd(LUNES)
    hechos = resolver(conn, crear_estado(), _entendido("disponibilidad",
                      producto_texto="collar talla L"), AHORA)
    assert hechos["datos"]["stock"] == 3


def test_precio_en_ingles_con_punto() -> None:
    """En inglés el precio usa punto decimal."""
    conn = iniciar_bd(LUNES)
    estado = crear_estado(idioma="en")
    hechos = resolver(conn, estado, _entendido("precio_producto",
                      producto_texto="adult dog food 15 kg", idioma="en"), AHORA)
    assert hechos["datos"]["precio"] == "49.90 EUR"


def test_horario_del_sabado() -> None:
    """El sábado abre de 10:00 a 14:00."""
    conn = iniciar_bd(LUNES)
    hechos = resolver(conn, crear_estado(), _entendido("horario_negocio",
                      fecha="2026-11-21"), AHORA)
    assert hechos["tipo_respuesta"] == "horario"
    assert hechos["datos"]["apertura"] == "10:00"
    assert hechos["datos"]["cierre"] == "14:00"


def test_domingo_cerrado_propone_siguiente() -> None:
    """El domingo dice que está cerrado y propone otro día."""
    conn = iniciar_bd(LUNES)
    hechos = resolver(conn, crear_estado(), _entendido("horario_negocio",
                      fecha="2026-11-22"), AHORA)
    assert hechos["tipo_respuesta"] == "cerrado"
    assert "lunes" in hechos["datos"]["dia"]


def test_horario_de_marta() -> None:
    """Marta atiende de lunes a viernes de 09:00 a 14:00."""
    conn = iniciar_bd(LUNES)
    hechos = resolver(conn, crear_estado(), _entendido("horario_veterinario",
                      veterinario_texto="doctora Marta"), AHORA)
    assert hechos["tipo_respuesta"] == "horario"
    assert hechos["datos"]["apertura"] == "09:00"


def test_cita_sabado_11_con_pablo() -> None:
    """El sábado a las 11:00 hay hueco con Pablo."""
    conn = iniciar_bd(LUNES)
    conn.execute("DELETE FROM citas")
    hechos = resolver(conn, crear_estado(), _entendido(
        "pedir_cita", servicio_texto="consulta general",
        fecha="2026-11-21", hora="11:00"), AHORA)
    assert hechos["tipo_respuesta"] == "oferta_cita"
    assert hechos["datos"]["hora"] == "11:00"
    assert hechos["datos"]["veterinario"] == "Pablo Soler"


def test_fecha_pasada_busca_desde_hoy() -> None:
    """Una fecha pasada nunca se ofrece: propone desde hoy."""
    conn = iniciar_bd(LUNES)
    hechos = resolver(conn, crear_estado(), _entendido(
        "pedir_cita", servicio_texto="consulta", fecha="2026-11-01"), AHORA)
    assert hechos["tipo_respuesta"] in ("oferta_cita", "sin_hueco")


def test_confirmar_cita_la_guarda() -> None:
    """Tras el sí, la cita queda en la tabla."""
    conn = iniciar_bd(LUNES)
    estado = crear_estado()
    resolver(conn, estado, _entendido(
        "pedir_cita", servicio_texto="consulta",
        fecha="2026-11-17", hora="09:00"), AHORA)
    antes = conn.execute("SELECT COUNT(*) FROM citas").fetchone()[0]
    hechos = resolver(conn, estado, _entendido("confirmar"), AHORA)
    assert hechos["tipo_respuesta"] == "cita_confirmada"
    assert conn.execute("SELECT COUNT(*) FROM citas").fetchone()[0] == antes + 1


def test_confirmar_compra_descuenta_stock() -> None:
    """Tras el sí, la venta se registra y el stock baja."""
    conn = iniciar_bd(LUNES)
    estado = crear_estado()
    resolver(conn, estado, _entendido("precio_producto",
              producto_texto="pienso perro adulto 15 kg", cantidad=2), AHORA)
    hechos = resolver(conn, estado, _entendido("confirmar"), AHORA)
    assert hechos["tipo_respuesta"] == "compra_confirmada"
    assert hechos["datos"]["total"] == "99,80 EUR"
    fila = conn.execute("SELECT stock FROM productos WHERE sku = 'P002'").fetchone()
    assert fila["stock"] == 10
    assert conn.execute("SELECT COUNT(*) FROM ventas").fetchone()[0] == 1


def test_sin_stock_no_vende() -> None:
    """Sin existencias no se registra ninguna venta."""
    conn = iniciar_bd(LUNES)
    estado = crear_estado()
    resolver(conn, estado, _entendido("precio_producto",
              producto_texto="antiparasitario perro grande"), AHORA)
    resolver(conn, estado, _entendido("confirmar"), AHORA)
    assert conn.execute("SELECT COUNT(*) FROM ventas").fetchone()[0] == 0


def test_rechazar_anula_la_propuesta() -> None:
    """Un no cancela la propuesta pendiente."""
    conn = iniciar_bd(LUNES)
    estado = crear_estado()
    resolver(conn, estado, _entendido("precio_producto",
              producto_texto="pienso perro adulto 15 kg"), AHORA)
    assert estado.propuesta_pendiente is not None
    hechos = resolver(conn, estado, _entendido("rechazar"), AHORA)
    assert hechos["tipo_respuesta"] == "anulado"
    assert estado.propuesta_pendiente is None


def test_es_ia_responde_con_la_verdad() -> None:
    """A "eres una persona" responde que es una IA."""
    conn = iniciar_bd(LUNES)
    hechos = resolver(conn, crear_estado(), _entendido("es_ia"), AHORA)
    assert hechos["tipo_respuesta"] == "aviso_ia"


def test_derivar_trae_contacto() -> None:
    """Derivar incluye el teléfono y el correo del negocio."""
    conn = iniciar_bd(LUNES)
    hechos = resolver(conn, crear_estado(), _entendido("hablar_con_persona"), AHORA)
    assert hechos["tipo_respuesta"] == "derivar"
    assert "900 000 000" in hechos["permitido_mencionar"]


def test_urgencia_trae_telefono() -> None:
    """La urgencia incluye el teléfono de la clínica."""
    conn = iniciar_bd(LUNES)
    hechos = resolver(conn, crear_estado(), _entendido("urgencia_clinica"), AHORA)
    assert hechos["tipo_respuesta"] == "urgencia"
    assert hechos["datos"]["telefono"] == "900 000 000"


def test_fuera_de_alcance_se_rechaza() -> None:
    """El fútbol no es asunto del bot."""
    conn = iniciar_bd(LUNES)
    hechos = resolver(conn, crear_estado(), _entendido("fuera_de_alcance"), AHORA)
    assert hechos["tipo_respuesta"] == "rechazo_alcance"


def test_formato_de_precios() -> None:
    """Coma decimal en ES y punto en EN."""
    assert formatear_precio(4990, "es") == "49,90 EUR"
    assert formatear_precio(4990, "en") == "49.90 EUR"


def test_nombre_de_dia_en_dos_idiomas() -> None:
    """El mismo día se nombra bien en ES y EN."""
    dia = date(2026, 11, 19)
    assert nombre_dia(dia, "es") == "jueves 19 de noviembre"
    assert nombre_dia(dia, "en") == "Thursday 19 November"
