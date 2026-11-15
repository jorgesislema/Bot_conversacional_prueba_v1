"""Pruebas del validador, una por cada regla de docs/05, sección 6."""

from core.validador import validar

HECHOS = {
    "tipo_respuesta": "precio",
    "datos": {"producto": "Pienso", "precio": "10,00 EUR"},
    "permitido_mencionar": ["Pienso", "10,00 EUR"],
}


def test_acepta_respuesta_correcta() -> None:
    """Una respuesta con solo datos permitidos pasa."""
    assert validar("Pienso: 10,00 EUR, IVA incluido.", HECHOS, "Hola.", []) == []


def test_rechaza_numero_inventado() -> None:
    """Un precio que no está en los hechos se rechaza."""
    motivos = validar("Pienso: 99,00 EUR, IVA incluido.", HECHOS, "Hola.", [])
    assert any(m.startswith("numero_no_permitido") for m in motivos)


def test_rechaza_nombre_inventado() -> None:
    """Un veterinario que no está en los hechos se rechaza."""
    motivos = validar("Te atiende Laura a las 10:00.", HECHOS, "Hola.", [])
    assert any(m.startswith("nombre_no_permitido") for m in motivos)


def test_rechaza_mas_de_tres_frases() -> None:
    """Cuatro frases seguidas se rechazan."""
    texto = "Pienso: 10,00 EUR. Hay stock. Ven cuando quieras. Gracias por todo."
    assert "demasiadas_frases" in validar(texto, HECHOS, "Hola.", [])


def test_rechaza_texto_demasiado_largo() -> None:
    """Más de 450 caracteres se rechaza."""
    assert "demasiado_larga" in validar("Pienso " * 100, HECHOS, "Hola.", [])


def test_rechaza_emoji() -> None:
    """Los emojis están prohibidos en las respuestas."""
    # Se construye con chr para no meter un emoji literal en el código.
    assert "contiene_emoji" in validar("Pienso a 10,00 EUR " + chr(0x1F600), HECHOS, "H.", [])


def test_rechaza_frase_que_finge_persona() -> None:
    """Fingir ser persona se rechaza."""
    motivos = validar("Como persona, te recomiendo el pienso.", HECHOS, "Hola.",
                      ["como persona"])
    assert any(m.startswith("finge_persona") for m in motivos)


def test_rechaza_doble_exclamacion() -> None:
    """Los signos de exclamación seguidos se rechazan."""
    assert "exclamacion_doble" in validar("Pienso genial!! Ven ya.", HECHOS, "H.", [])


def test_rechaza_mismo_arranque() -> None:
    """Repetir la primera palabra de la respuesta anterior se rechaza."""
    motivos = validar("Tengo el pienso a 10,00 EUR.", HECHOS, "Tengo novedades.", [])
    assert "mismo_arranque" in motivos


def test_lista_pedida_puede_pasar_de_tres_frases() -> None:
    """Una aclaración con lista no tiene tope de frases."""
    hechos = dict(HECHOS, datos={"lista": "A, B, C, D"})
    texto = "Tengo esto. A. B. C. D."
    assert "demasiadas_frases" not in validar(texto, hechos, "Hola.", [])
