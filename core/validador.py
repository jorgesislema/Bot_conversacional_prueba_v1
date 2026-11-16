"""Comprueba que la respuesta solo contiene datos de los hechos.

Qué hace: aplica las 7 reglas de docs/05, sección 6, y devuelve los
motivos de rechazo. Recibe: texto, hechos, arranque anterior y frases
prohibidas. Devuelve: lista de motivos (vacía si es válida). Qué NO
hace: no corrige ni reintenta; el flujo que llama decide el respaldo.
"""

from __future__ import annotations

import re
from typing import Any

_PATRON_NUMERO = re.compile(r"\d+[,.]\d+|\d{1,2}:\d{2}|\b\d+\b")
_PATRON_PRECIO = re.compile(r"\d+[,.]\d{2}")
_PATRON_HORA = re.compile(r"\d{1,2}:\d{2}")
_PATRON_CORREO = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
_PATRON_ENLACE = re.compile(r"https?://\S+")
# El salto de línea también separa frases: en una lista cada línea empieza
# con mayúscula sin que eso sea un nombre propio.
_PATRON_FRASE = re.compile(r"[.!?\n]+")
_PATRON_PALABRA = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+")

# Mayúsculas de cortesía o inicio de pregunta que no son nombres propios.
_EXCEPCIONES = {
    "cuál", "cuáles", "qué", "cómo", "dónde", "cuándo", "cuánto",
    "ese", "esa", "esos", "esas", "este", "esta", "estos", "estas",
    "dra", "dr", "sr", "sra",
    "what", "which", "this", "that", "these", "those", "how",
}


def _normalizar_numero(token: str) -> str:
    """Unifica el separador decimal para comparar ES y EN."""
    return token.replace(",", ".")


def validar(
    texto: str,
    hechos: dict[str, Any],
    arranque_anterior: str,
    frases_prohibidas: list[str],
) -> list[str]:
    """Valida una respuesta redactada contra los hechos.

    Parámetros:
        texto: respuesta candidata.
        hechos: diccionario con tipo_respuesta, datos y permitido_mencionar.
        arranque_anterior: respuesta anterior del bot.
        frases_prohibidas: lista i18n de frases que fingen ser persona.
    Devuelve: lista de motivos; vacía cuando la respuesta es válida.
    Ejemplo:
        >>> hechos = {"tipo_respuesta": "precio", "datos": {},
        ...     "permitido_mencionar": ["Pienso", "10,00 EUR"]}
        >>> validar("Pienso: 10,00 EUR, IVA incluido.", hechos, "Hola.", [])
        []
    """
    motivos: list[str] = []
    permitido = " | ".join(str(p) for p in hechos.get("permitido_mencionar", []))
    permitido_norm = _normalizar_numero(permitido.lower())
    datos = hechos.get("datos", {})
    # Un enlace solo vale si está tal cual en los hechos; luego se quita del
    # texto para que sus números y puntos no cuenten como datos o frases.
    for enlace in _PATRON_ENLACE.findall(texto):
        if enlace.rstrip(".,)") not in permitido:
            motivos.append("enlace_no_permitido")
    texto = _PATRON_ENLACE.sub("enlace", texto)

    for match in _PATRON_NUMERO.finditer(texto):
        token = _normalizar_numero(match.group(0))
        if token.lower() not in permitido_norm and token not in str(datos):
            motivos.append(f"numero_no_permitido: {match.group(0)}")

    for frase in _PATRON_FRASE.split(texto):
        limpia = frase.lstrip()
        for match in _PATRON_PALABRA.finditer(limpia):
            palabra = match.group(0)
            inicio = match.start()
            if inicio == 0:
                continue  # El inicio de frase no es nombre propio.
            # Tras dos puntos empieza una cita de un dato ("Sobre X: Alimento...").
            anterior = limpia[:inicio].rstrip()
            if anterior.endswith(":"):
                continue
            bajo = palabra.lower()
            if len(palabra) < 3 or palabra.isupper() or bajo in _EXCEPCIONES:
                continue
            if palabra[0].isupper() and bajo not in permitido.lower():
                motivos.append(f"nombre_no_permitido: {palabra}")
                break
        if motivos and motivos[-1].startswith("nombre_no_permitido"):
            break

    sin_numeros = _PATRON_HORA.sub("", _PATRON_PRECIO.sub("", texto))
    # El punto del correo no separa frases.
    sin_numeros = _PATRON_CORREO.sub("correo", sin_numeros)
    frases = [f for f in _PATRON_FRASE.split(sin_numeros) if f.strip()]
    if "lista" not in datos and len(frases) > 3:
        motivos.append("demasiadas_frases")
    if len(texto) > 450:
        motivos.append("demasiado_larga")

    for letra in texto:
        codigo = ord(letra)
        if 0x1F300 <= codigo <= 0x1FAFF or 0x2600 <= codigo <= 0x27BF:
            motivos.append("contiene_emoji")
            break

    texto_bajo = texto.lower()
    for frase in frases_prohibidas:
        if frase.lower() in texto_bajo:
            motivos.append(f"finge_persona: {frase}")
            break

    if "!!" in texto:
        motivos.append("exclamacion_doble")

    actual = _PATRON_PALABRA.findall(texto)
    anterior = _PATRON_PALABRA.findall(arranque_anterior)
    if actual and anterior and actual[0].lower() == anterior[0].lower():
        motivos.append("mismo_arranque")
    return motivos
