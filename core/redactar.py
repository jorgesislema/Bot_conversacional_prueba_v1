"""Redacta la respuesta con la IA a partir de los hechos.

Qué hace: arma el prompt de estilo de docs/05, sección 5, con solo los
datos de los hechos, y pide el texto al proveedor. Recibe: proveedor,
hechos, textos y nombres del negocio. Devuelve: el texto candidato.
Qué NO hace: no valida el texto (eso es validador.py) ni elige el
respaldo (eso lo hace el flujo que llama).
"""

from __future__ import annotations

from typing import Any

from core.proveedor_ia import ProveedorIA

PLANTILLA_REDACTAR = (
    "Escribes la respuesta de {nombre_bot}, asistente virtual con"
    " inteligencia artificial de {negocio}.\n"
    "Idioma: {idioma}. Trato: {trato}.\n"
    "Estilo: cálido, claro y breve. Máximo 3 frases."
    " Una sola pregunta como máximo.\n"
    "No uses emojis ni iconos. No uses signos de exclamación seguidos.\n"
    "No empieces con la misma fórmula que tu respuesta anterior:"
    " {arranque_anterior}\n"
    "Usa SOLO los datos de la sección HECHOS. Si un dato no está ahí,"
    " no lo menciones.\n"
    "Nunca afirmes ser una persona. Nunca des diagnósticos, dosis ni"
    " consejos médicos.\n"
    "Precios con la moneda y con IVA incluido cuando se mencione un precio.\n"
    "HECHOS: {hechos}\n"
    "Responde solo con el texto para el cliente."
)


def redactar(
    proveedor: ProveedorIA, hechos: dict[str, Any], nombre_bot: str,
    negocio: str, arranque_anterior: str, correccion: str = "",
) -> str:
    """Pide a la IA el texto para los hechos dados.

    Parámetros:
        proveedor: principal o conjunto con respaldo.
        hechos: diccionario de docs/05, sección 3.
        nombre_bot: nombre del asistente (Ana en la demo).
        negocio: nombre del negocio.
        arranque_anterior: respuesta anterior para no repetir el inicio.
        correccion: motivos del validador para el reintento.
    Devuelve: texto candidato para el cliente.
    Ejemplo:
        >>> from core.proveedor_ia import ProveedorFalso
        >>> h = {"tipo_respuesta": "saludo", "idioma": "es", "trato": "tu",
        ...     "datos": {}, "pregunta_siguiente": "",
        ...     "permitido_mencionar": []}
        >>> redactar(ProveedorFalso(textos=["Hola."]), h, "Ana", "M", "")
        'Hola.'
    """
    prompt = PLANTILLA_REDACTAR.format(
        nombre_bot=nombre_bot, negocio=negocio,
        idioma=hechos.get("idioma", "es"), trato=hechos.get("trato", "tu"),
        arranque_anterior=arranque_anterior or "ninguna",
        hechos=hechos,
    )
    if correccion:
        prompt += f"\nCorrige: {correccion}. Responde solo con el texto corregido."
    return proveedor.generar_texto(prompt, 300, 0.6)
