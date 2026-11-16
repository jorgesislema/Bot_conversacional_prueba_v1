"""Pruebas legales y de coherencia entre plantillas y validador (fase 2)."""

from datetime import date, datetime
from zoneinfo import ZoneInfo

from core.esquema import iniciar_bd
from core.estado import crear_estado
from core.plantillas import aviso_inicial, cargar_textos, respaldo, saludo_segun_hora
from core.privacidad import contiene_datos_personales
from core.reglas import resolver
from core.validador import validar

ZONA = ZoneInfo("Europe/Madrid")
LUNES = date(2026, 11, 16)
AHORA = datetime(2026, 11, 16, 8, 0, tzinfo=ZONA)


def test_aviso_inicial_menciona_ia_en_es() -> None:
    """El primer mensaje en ES dice inteligencia artificial."""
    textos = cargar_textos("es")
    texto = aviso_inicial(textos, "es", "tu", "Mascota Feliz", "Ana", AHORA)
    assert "inteligencia artificial" in texto
    assert "Mascota Feliz" in texto
    assert "Ana" in texto


def test_aviso_inicial_menciona_ia_en_en() -> None:
    """El primer mensaje en EN dice artificial intelligence."""
    textos = cargar_textos("en")
    texto = aviso_inicial(textos, "en", "tu", "Mascota Feliz", "Ana", AHORA)
    assert "artificial intelligence" in texto


def test_saludo_cambia_segun_hora() -> None:
    """El saludo depende de la hora de Madrid."""
    textos = cargar_textos("es")
    manana = datetime(2026, 11, 16, 9, 0, tzinfo=ZONA)
    tarde = datetime(2026, 11, 16, 16, 0, tzinfo=ZONA)
    noche = datetime(2026, 11, 16, 22, 0, tzinfo=ZONA)
    assert saludo_segun_hora(manana, textos) == "Buenos días"
    assert saludo_segun_hora(tarde, textos) == "Buenas tardes"
    assert saludo_segun_hora(noche, textos) == "Buenas noches"


def test_eres_humano_responde_con_la_verdad() -> None:
    """El bot nunca finge ser persona."""
    conn = iniciar_bd(LUNES)
    hechos = resolver(conn, crear_estado(), {"intencion": "es_ia", "idioma": "es",
                       "trato": "tu"}, AHORA)
    texto, _ = respaldo(hechos, cargar_textos("es"))
    assert "inteligencia artificial" in texto
    assert "persona del equipo" in texto or "persona, te indico" in texto


def test_derivar_muestra_contacto_y_aviso_demo() -> None:
    """Derivar muestra teléfono, correo y el aviso de demo."""
    conn = iniciar_bd(LUNES)
    hechos = resolver(conn, crear_estado(), {"intencion": "hablar_con_persona",
                       "idioma": "es", "trato": "tu"}, AHORA)
    texto, _ = respaldo(hechos, cargar_textos("es"))
    assert "900 000 000" in texto
    assert "contacto@mascotafeliz.example" in texto


def test_datos_personales_no_llegan_a_la_ia() -> None:
    """Un teléfono o correo se detecta antes de llamar a la IA."""
    assert contiene_datos_personales("mi teléfono es 612345678")
    assert contiene_datos_personales("escribe a ana@test.es")


def _casos() -> list[dict]:
    """Un caso de respaldo por cada tipo de respuesta."""
    return [
        {"tipo_respuesta": "precio", "idioma": "es", "datos":
            {"producto": "Pienso perro adulto 15 kg", "precio": "49,90 EUR"},
         "permitido_mencionar": ["Pienso perro adulto 15 kg", "49,90 EUR"]},
        # Desde la conversación tipo vendedor, descripción y stock llevan
        # también marca y precio.
        {"tipo_respuesta": "descripcion", "idioma": "es", "datos":
            {"producto": "Pienso perro adulto 15 kg",
             "descripcion": "Alimento completo con pollo y arroz.",
             "marca": "Campo Verde", "precio": "49,90 EUR", "stock": 12},
         "permitido_mencionar": ["Pienso perro adulto 15 kg", "Campo Verde",
                                 "49,90 EUR"]},
        {"tipo_respuesta": "stock", "idioma": "es", "datos":
            {"producto": "Collar", "stock": 25, "marca": "Paseo", "precio": "7,90 EUR"},
         "permitido_mencionar": ["Collar", "25", "Paseo", "7,90 EUR"]},
        {"tipo_respuesta": "stock", "idioma": "es", "datos":
            {"producto": "Collar", "stock": 2, "marca": "Paseo", "precio": "8,90 EUR"},
         "permitido_mencionar": ["Collar", "2", "Paseo", "8,90 EUR"]},
        {"tipo_respuesta": "lista_productos", "idioma": "es", "datos":
            {"lista": "- Pienso A, Campo Verde: 14,50 EUR\n- Pienso B, Campo Verde: 49,90 EUR",
             "cantidad": 2, "total": 2},
         "permitido_mencionar": ["Pienso A", "Campo Verde", "14,50 EUR", "Pienso B",
                                 "49,90 EUR"]},
        {"tipo_respuesta": "comparacion", "idioma": "es", "datos":
            {"producto": "A y B", "descripcion": "A: uno (1,00 EUR) ; B: dos (2,00 EUR)"},
         "permitido_mencionar": ["A", "B", "1,00 EUR", "2,00 EUR"]},
        {"tipo_respuesta": "stock", "idioma": "es", "datos":
            {"producto": "Pienso", "stock": 0, "alternativa": "Otro pienso",
             "precio": "10,00 EUR"},
         "permitido_mencionar": ["Pienso", "0", "Otro pienso", "10,00 EUR"]},
        {"tipo_respuesta": "aclaracion_producto", "idioma": "es",
         "datos": {"lista": "A, B"}, "permitido_mencionar": ["A", "B"]},
        {"tipo_respuesta": "horario", "idioma": "es",
         "datos": {"dia": "sábado 21 de noviembre", "apertura": "10:00",
                   "cierre": "14:00"},
         "permitido_mencionar": ["sábado 21 de noviembre", "10:00", "14:00"]},
        {"tipo_respuesta": "cerrado", "idioma": "es",
         "datos": {"dia": "lunes 23 de noviembre"},
         "permitido_mencionar": ["lunes 23 de noviembre"]},
        {"tipo_respuesta": "oferta_cita", "idioma": "es",
         "datos": {"dia": "martes 17 de noviembre", "hora": "11:00",
                   "veterinario": "Pablo Soler", "servicio": "Consulta general"},
         "permitido_mencionar": ["martes 17 de noviembre", "11:00",
                                 "Pablo Soler", "Consulta general"]},
        {"tipo_respuesta": "cita_confirmada", "idioma": "es",
         "datos": {"dia": "martes 17 de noviembre", "hora": "11:00",
                   "veterinario": "Pablo Soler", "servicio": "Consulta general"},
         "permitido_mencionar": ["martes 17 de noviembre", "11:00", "Pablo Soler",
                                 "Consulta general"]},
        {"tipo_respuesta": "sin_hueco", "idioma": "es",
         "datos": {"dia": "martes 17 de noviembre", "hora": "11:00",
                   "veterinario": "Pablo Soler", "servicio": "Consulta general"},
         "permitido_mencionar": ["martes 17 de noviembre", "11:00", "Pablo Soler"]},
        {"tipo_respuesta": "compra_confirmada", "idioma": "es",
         "datos": {"producto": "Pienso", "cantidad": 2, "total": "99,80 EUR"},
         "permitido_mencionar": ["Pienso", "2", "99,80 EUR"]},
        {"tipo_respuesta": "derivar", "idioma": "es",
         "datos": {"telefono": "900 000 000", "correo": "contacto@mascotafeliz.example"},
         "permitido_mencionar": ["900 000 000", "contacto@mascotafeliz.example"]},
        {"tipo_respuesta": "aviso_ia", "idioma": "es",
         "datos": {"negocio": "Mascota Feliz"},
         "permitido_mencionar": ["Mascota Feliz"]},
        {"tipo_respuesta": "urgencia", "idioma": "es",
         "datos": {"telefono": "900 000 000"},
         "permitido_mencionar": ["900 000 000"]},
        {"tipo_respuesta": "rechazo_alcance", "idioma": "es", "datos": {},
         "permitido_mencionar": []},
        {"tipo_respuesta": "no_se", "idioma": "es", "datos": {},
         "permitido_mencionar": []},
        {"tipo_respuesta": "anulado", "idioma": "es", "datos": {},
         "permitido_mencionar": []},
        {"tipo_respuesta": "saludo", "idioma": "es", "datos": {},
         "permitido_mencionar": []},
        {"tipo_respuesta": "despedida", "idioma": "es", "datos": {},
         "permitido_mencionar": []},
        {"tipo_respuesta": "gracias", "idioma": "es", "datos": {},
         "permitido_mencionar": []},
        {"tipo_respuesta": "datos_personales", "idioma": "es", "datos": {},
         "permitido_mencionar": []},
        {"tipo_respuesta": "tope", "idioma": "es", "datos": {},
         "permitido_mencionar": []},
    ]


def test_todos_los_respaldos_pasan_el_validador() -> None:
    """Cada plantilla de respaldo, en ES y EN, pasa el validador."""
    for idioma in ("es", "en"):
        textos = cargar_textos(idioma)
        for hechos in _casos():
            hechos = dict(hechos, idioma=idioma, trato="tu")
            texto, _ = respaldo(hechos, textos, evitar_indice=0)
            motivos = validar(texto, hechos, "Empezamos.", textos["frases_prohibidas"])
            assert motivos == [], f"{hechos['tipo_respuesta']}/{idioma}: {motivos}"
