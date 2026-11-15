"""Detecta datos personales en el texto del usuario antes de usar la IA.

Qué hace: busca teléfonos, correos, DNI/NIE, IBAN y tarjetas, y los
oculta para que esa parte nunca llegue al proveedor de IA. Recibe: el
texto del usuario. Devuelve: si hay datos y el texto ocultado. Qué NO
hace: no valida identidades ni guarda nada, solo detecta y oculta.

Por qué pecar de exceso: mejor pedir que no se compartan datos que
dejar escapar un teléfono al proveedor (ver 01, sección 5.5).
"""

from __future__ import annotations

import re

_LETRAS_DNI = "TRWAGMYFPDXBNJZSQVHLCKE"
_MASCARA = "[dato oculto]"

_PATRONES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("correo", re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")),
    ("telefono_internacional", re.compile(r"\+\d(?:[\s.\-]?\d){8,14}")),
    ("telefono_es", re.compile(r"\b[6789]\d{2}[\s.\-]?\d{3}[\s.\-]?\d{3}\b")),
    ("telefono_largo", re.compile(r"\b\d{9,}\b")),
    ("nie", re.compile(r"\b[XYZ]\d{7}[A-HJ-NP-TV-Z]\b")),
    ("dni", re.compile(r"\b\d{8}[A-HJ-NP-TV-Z]\b")),
    ("iban", re.compile(r"\bES\d{2}(?:\s?\d{4}){5}\b")),
    ("tarjeta", re.compile(r"\b(?:\d[\s.\-]?){13,19}\b")),
)


def _letra_valida_dni(numero: int) -> str:
    """Devuelve la letra de control de un DNI o NIE."""
    return _LETRAS_DNI[numero % 23]


def _documento_valido(texto: str) -> bool:
    """Comprueba la letra de control de un DNI o NIE.

    Por qué validar la letra: un código de 8 dígitos más letra al azar
    no es un documento real y no debería bloquear el mensaje.
    """
    limpio = texto.replace(" ", "").replace(".", "").replace("-", "")
    if limpio[0] in "XYZ":
        numero = int(str("XYZ".index(limpio[0])) + limpio[1:8])
    else:
        numero = int(limpio[:8])
    return limpio[-1] == _letra_valida_dni(numero)


def _luhn_valido(texto: str) -> bool:
    """Comprueba una tarjeta con el algoritmo de Luhn.

    Por qué Luhn: una ristra de 16 dígitos cualquiera no es una tarjeta;
    solo se oculta si pasa el dígito de control.
    """
    digitos = [int(c) for c in texto if c.isdigit()]
    if len(digitos) not in (13, 14, 15, 16, 17, 18, 19):
        return False
    total = 0
    for i, d in enumerate(reversed(digitos)):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def contiene_datos_personales(texto: str) -> bool:
    """Indica si el texto contiene algún dato personal detectable.

    Parámetros:
        texto: mensaje del usuario.
    Devuelve: verdadero si hay teléfono, correo, DNI/NIE, IBAN o tarjeta.
    Ejemplo:
        >>> contiene_datos_personales("llámame al 612345678")
        True
        >>> contiene_datos_personales("cuánto cuesta el pienso")
        False
    """
    return ocultar_datos_personales(texto)[1]


def ocultar_datos_personales(texto: str) -> tuple[str, bool]:
    """Oculta los datos personales del texto con una máscara.

    Parámetros:
        texto: mensaje del usuario.
    Devuelve: tupla con el texto ocultado y si se encontró algo.
    Ejemplo:
        >>> ocultar_datos_personales("soy ana@test.es")[1]
        True
    """
    encontrado = False

    def _reemplazar(match: re.Match[str], validador: str) -> str:
        nonlocal encontrado
        valor = match.group(0)
        if validador == "documento" and not _documento_valido(valor):
            return valor
        if validador == "tarjeta" and not _luhn_valido(valor):
            return valor
        encontrado = True
        return _MASCARA

    resultado = texto
    for nombre, patron in _PATRONES:
        if nombre in ("dni", "nie"):
            resultado = patron.sub(lambda m: _reemplazar(m, "documento"), resultado)
        elif nombre == "tarjeta":
            resultado = patron.sub(lambda m: _reemplazar(m, "tarjeta"), resultado)
        else:
            resultado = patron.sub(lambda m: _reemplazar(m, "siempre"), resultado)
    return resultado, encontrado
