"""Historial del chat en Streamlit.

Qué hace: dibuja los mensajes guardados en la sesión. Recibe: la lista
de mensajes con rol y contenido. Devuelve: nada, dibuja en pantalla.
Qué NO hace: no llama al motor (eso lo hace app.py con core/flujo.py).
"""

from __future__ import annotations

from typing import Any

import streamlit as st


def mostrar_historial(mensajes: list[dict[str, Any]]) -> None:
    """Dibuja cada mensaje con el rol que le toca.

    Parámetros:
        mensajes: lista de {"rol": "usuario"|"asistente", "texto": ...}.
    Ejemplo:
        >>> mostrar_historial([])  # doctest: +SKIP
        No dibuja nada sin mensajes.
    """
    for mensaje in mensajes:
        with st.chat_message(mensaje["rol"]):
            st.write(mensaje["texto"])
