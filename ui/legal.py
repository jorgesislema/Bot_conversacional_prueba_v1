"""Aviso legal del pie: titular y privacidad (docs/01, secciones 5 y 6).

Qué hace: compone el pie con el titular y devuelve el aviso de
privacidad corto. Recibe: textos i18n y datos del titular. Devuelve:
cadenas listas para mostrar. Qué NO hace: no dibuja nada (eso es app.py).
"""

from __future__ import annotations

from typing import Any


def texto_pie(textos: dict[str, Any], titular: str, correo: str) -> str:
    """Compone el pie con el titular y su contacto.

    Parámetros:
        textos: diccionario i18n del idioma activo.
        titular: nombre del responsable (lo define el dueño).
        correo: contacto del responsable.
    Devuelve: línea de pie con ambos datos.
    Ejemplo:
        >>> texto_pie({"pie_titular": "Titular: {titular}. Contacto: {correo_titular}."}, "X", "x@y.z")
        'Titular: X. Contacto: x@y.z.'
    """
    return str(textos["pie_titular"]).format(titular=titular,
                                             correo_titular=correo)


def texto_privacidad(textos: dict[str, Any]) -> str:
    """Devuelve el aviso corto de privacidad.

    Ejemplo:
        >>> isinstance(texto_privacidad({"texto_privacidad": "Hola"}), str)
        True
    """
    return str(textos["texto_privacidad"])
