"""Chat en forma de teléfono con burbujas tipo mensajería.

Qué hace: convierte el historial de la sesión en HTML seguro (todo texto
se escapa) con burbujas del bot a la izquierda y del cliente a la
derecha, más la barra superior con el nombre del asistente y la etiqueta
de IA. Recibe: la lista de mensajes y los textos de la cabecera.
Devuelve: HTML como texto (funciones puras, fáciles de probar).
Qué NO hace: no llama al motor (eso lo hace app.py con core/flujo.py) y
nunca inserta HTML escrito por el usuario sin escapar.
"""

from __future__ import annotations

import html
import re
from typing import Any

# Enlaces https ya escapados. Se excluyen comillas y "<" para que el
# enlace no pueda salirse del atributo href.
_PATRON_ENLACE = re.compile(r"https://[^\s<>\"']+")


def _enlazar(texto_escapado: str) -> str:
    """Convierte en enlace pulsable cada https:// de un texto ya escapado.

    Solo se usa con mensajes del bot, que salen de la base de datos.
    El texto del cliente nunca se convierte en enlace.

    Ejemplo:
        >>> 'target="_blank"' in _enlazar("Mapa: https://www.google.com/maps")
        True
    """
    def reemplazo(coincidencia: re.Match[str]) -> str:
        enlace = coincidencia.group(0).rstrip(".,)")
        resto = coincidencia.group(0)[len(enlace):]
        return (f'<a href="{enlace}" target="_blank" rel="noopener noreferrer">'
                f"{enlace}</a>{resto}")

    return _PATRON_ENLACE.sub(reemplazo, texto_escapado)


def _texto_seguro(texto: str) -> str:
    """Escapa el texto y conserva los saltos de línea como <br>.

    Por qué escapar: el mensaje del cliente se pinta con HTML; sin
    escapar, alguien podría inyectar etiquetas o scripts.

    Ejemplo:
        >>> _texto_seguro("<b>hola</b>\\nadios")
        '&lt;b&gt;hola&lt;/b&gt;<br>adios'
    """
    return html.escape(texto).replace("\n", "<br>")


def html_barra(nombre_bot: str, estado: str, etiqueta_ia: str) -> str:
    """Barra superior del teléfono: avatar, nombre, estado y etiqueta IA.

    La etiqueta de IA es fija y visible siempre (Ley de IA, art. 50).

    Ejemplo:
        >>> "Asistente con IA" in html_barra("Ana", "en línea", "Asistente con IA")
        True
    """
    inicial = html.escape(nombre_bot[:1].upper() or "A")
    return (
        '<div class="mf-tel-barra">'
        f'<div class="mf-avatar">{inicial}</div>'
        f'<div><div class="mf-tel-nombre">{html.escape(nombre_bot)}</div>'
        f'<div class="mf-tel-estado">{html.escape(estado)}</div></div>'
        f'<div class="mf-tel-ia">{html.escape(etiqueta_ia)}</div>'
        "</div>"
    )


def html_conversacion(mensajes: list[dict[str, Any]], etiqueta_fecha: str) -> str:
    """Zona de mensajes con burbujas y hora.

    Parámetros:
        mensajes: lista de {"rol": "usuario"|"asistente", "texto", "hora"?}.
        etiqueta_fecha: texto de la pastilla superior ("Hoy").
    Devuelve: HTML de la conversación.
    Ejemplo:
        >>> "mf-cliente" in html_conversacion([{"rol": "usuario", "texto": "hola"}], "Hoy")
        True
    """
    # Contenedor externo en columna invertida: así la barra de desplazamiento
    # arranca abajo y el último mensaje siempre queda a la vista.
    partes = ['<div class="mf-tel-chat"><div class="mf-tel-lista">',
              f'<div class="mf-fecha">{html.escape(etiqueta_fecha)}</div>']
    for mensaje in mensajes:
        es_cliente = mensaje.get("rol") == "usuario"
        clase = "mf-cliente" if es_cliente else "mf-bot"
        hora = html.escape(str(mensaje.get("hora", "")))
        pie = f'<span class="mf-hora">{hora}</span>' if hora else ""
        cuerpo = _texto_seguro(str(mensaje.get("texto", "")))
        if not es_cliente:
            cuerpo = _enlazar(cuerpo)
        partes.append(f'<div class="mf-burbuja {clase}">{cuerpo}{pie}</div>')
    partes.append("</div></div>")
    return "".join(partes)
