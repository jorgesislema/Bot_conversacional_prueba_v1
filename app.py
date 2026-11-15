"""Entrada de la demo en Streamlit.

Qué hace: monta el chat a la izquierda y el panel editable a la
derecha, con aviso de IA, banner de demo y pie legal. Recibe: nada
(Streamlit gestiona la sesión). Devuelve: nada, dibuja la página.
Qué NO hace: no guarda datos entre sesiones; cada visita tiene su
propia base en memoria que se destruye al cerrar.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

import streamlit as st

from core.esquema import iniciar_bd
from core.estado import crear_estado
from core.flujo import responder, restantes
from core.limites import LIMITE_DIARIO_POR_DEFECTO, LIMITE_SESION_POR_DEFECTO, ContadorDiario
from core.plantillas import aviso_inicial, cargar_textos, respaldo
from core.proveedor_ia import ProveedorConRespaldo, ProveedorHTTP, ProveedorIA
from core.reglas import resolver
from ui.chat import mostrar_historial
from ui.legal import texto_pie, texto_privacidad
from ui.panel import cargar_tabla, guardar_tabla, resumen_ventas

ZONA = ZoneInfo("Europe/Madrid")

# URLs base conocidas; si el secreto trae una URL completa, se usa tal cual.
URLS = {
    "mistral": "https://api.mistral.ai/v1",
    "openai": "https://api.openai.com/v1",
}


def _secreto(nombre: str, defecto: str = "") -> str:
    """Lee un secreto sin romper si no existe."""
    try:
        valor = st.secrets.get(nombre, defecto)
    except Exception:
        return defecto
    return str(valor) if valor is not None else defecto


def _entero_secreto(nombre: str, defecto: int) -> int:
    """Lee un secreto numérico con valor por defecto."""
    try:
        return int(_secreto(nombre, str(defecto)))
    except ValueError:
        return defecto


def _base_url(nombre: str, directa: str) -> str:
    """Resuelve la URL base del proveedor."""
    if directa.startswith("http"):
        return directa
    return URLS.get(nombre.strip().lower(), directa or URLS["mistral"])


def construir_proveedor() -> ProveedorIA | None:
    """Crea el proveedor con las claves de st.secrets o None sin claves.

    Sin clave principal la app arranca en modo sin IA (ver 06.2).
    """
    nombre = _secreto("PROVEEDOR_PRINCIPAL")
    clave = _secreto("CLAVE_PRINCIPAL")
    if not clave:
        return None
    modelo = _secreto("MODELO_PRINCIPAL") or "mistral-small-latest"
    principal = ProveedorHTTP(_base_url(nombre, _secreto("URL_PRINCIPAL")),
                              clave, modelo)
    nombre_b = _secreto("PROVEEDOR_RESPALDO")
    clave_b = _secreto("CLAVE_RESPALDO")
    if not clave_b:
        return principal
    modelo_b = _secreto("MODELO_RESPALDO") or modelo
    respaldo_prov = ProveedorHTTP(_base_url(nombre_b, _secreto("URL_RESPALDO")),
                                  clave_b, modelo_b)
    return ProveedorConRespaldo(principal, respaldo_prov)


@st.cache_resource
def obtener_contador(limite: int) -> ContadorDiario:
    """Contador diario compartido entre sesiones (ver 05.10)."""
    return ContadorDiario(limite)


def _iniciar_sesion() -> None:
    """Crea la base y el estado propios de esta visita."""
    conn = iniciar_bd()
    negocio = conn.execute("SELECT * FROM negocio").fetchone()
    st.session_state["conn"] = conn
    st.session_state["estado"] = crear_estado(
        idioma=str(negocio["idioma_por_defecto"]),
        trato=str(negocio["trato_por_defecto"]),
    )
    st.session_state["idioma"] = str(negocio["idioma_por_defecto"])
    st.session_state["mensajes"] = []
    st.session_state["aviso_cambio"] = False


def _derivar_directo(conn: Any, textos: dict[str, Any], idioma: str) -> str:
    """Respuesta fija de derivación sin pasar por la IA (ver 05.11)."""
    from core.estado import Estado

    estado = st.session_state["estado"]
    if not isinstance(estado, Estado):
        estado = crear_estado(idioma=idioma)
    hechos = resolver(conn, estado, {"intencion": "hablar_con_persona",
                                     "idioma": idioma, "trato": estado.trato},
                      datetime.now(ZONA))
    texto, _ = respaldo(hechos, textos)
    return texto


def main() -> None:
    """Dibuja la demo completa: chat, panel, aviso legal y pie."""
    st.set_page_config(page_title="Mascota Feliz - demo", layout="wide")
    if "conn" not in st.session_state:
        _iniciar_sesion()
    conn = st.session_state["conn"]
    estado = st.session_state["estado"]
    negocio = conn.execute("SELECT * FROM negocio").fetchone()

    cabecera, lengua = st.columns([3, 1])
    with cabecera:
        st.title(str(negocio["nombre"]))
        st.caption(cargar_textos(st.session_state["idioma"])["etiqueta_ia"])
    with lengua:
        idioma = st.selectbox(
            "Idioma / Language", ["es", "en"],
            index=0 if st.session_state["idioma"] == "es" else 1,
        )
        if idioma != st.session_state["idioma"]:
            st.session_state["idioma"] = idioma
            estado.idioma = idioma
    textos = cargar_textos(st.session_state["idioma"])
    st.caption(textos["banner_demo"])

    limite_sesion = _entero_secreto("LIMITE_SESION", LIMITE_SESION_POR_DEFECTO)
    limite_diario = _entero_secreto("LIMITE_DIARIO", LIMITE_DIARIO_POR_DEFECTO)
    proveedor = construir_proveedor()
    if proveedor is None:
        st.caption(textos["modo_sin_ia"])

    if st.session_state.pop("aviso_cambio", False):
        st.success(textos["cambio_aplicado"])

    if not estado.aviso_ia_mostrado:
        primer = aviso_inicial(textos, estado.idioma, estado.trato,
                               str(negocio["nombre"]),
                               str(negocio["nombre_bot"]),
                               datetime.now(ZONA))
        st.session_state["mensajes"].append({"rol": "asistente", "texto": primer})
        estado.aviso_ia_mostrado = True

    chat_col, panel_col = st.columns([3, 2])
    with chat_col:
        mostrar_historial(st.session_state["mensajes"])
        botones = st.columns(2)
        with botones[0]:
            if st.button(textos["boton_persona"]):
                texto = _derivar_directo(conn, textos, st.session_state["idioma"])
                st.session_state["mensajes"].append(
                    {"rol": "asistente", "texto": texto})
                st.rerun()
        with botones[1]:
            if st.button(textos["boton_reset"]):
                for clave in ("conn", "estado", "mensajes", "idioma"):
                    st.session_state.pop(clave, None)
                st.rerun()
        st.caption(textos["mensajes_restantes"].format(
            n=restantes(estado, limite_sesion)))
        pregunta = st.chat_input(textos["placeholder_chat"])
        if pregunta:
            contador = obtener_contador(limite_diario)
            cupo = contador.hay_cupo()
            if cupo:
                contador.registrar()
            resultado = responder(conn, estado, textos, pregunta,
                                  datetime.now(ZONA), proveedor,
                                  cupo_diario=cupo, limite_sesion=limite_sesion)
            st.session_state["mensajes"].append(
                {"rol": "usuario", "texto": pregunta})
            st.session_state["mensajes"].append(
                {"rol": "asistente", "texto": resultado.texto})
            st.rerun()

    with panel_col:
        pestanas = st.tabs([textos["pestana_catalogo"], textos["pestana_horarios"],
                            textos["pestana_veterinarios"],
                            textos["pestana_ventas"]])
        with pestanas[0]:
            _editor(conn, textos, "productos",
                    ("nombre_es", "nombre_en", "descripcion_es",
                     "descripcion_en", "precio_eur", "stock", "activo"))
            _editor(conn, textos, "servicios",
                    ("nombre_es", "nombre_en", "duracion_min", "precio_eur",
                     "activo"))
        with pestanas[1]:
            _editor(conn, textos, "horarios_negocio",
                    ("hora_apertura", "hora_cierre"))
            st.dataframe(cargar_tabla(conn, "dias_especiales"))
        with pestanas[2]:
            _editor(conn, textos, "veterinarios",
                    ("nombre", "especialidad", "activo"))
            _editor(conn, textos, "turnos", ("hora_inicio", "hora_fin"))
        with pestanas[3]:
            ventas, citas = resumen_ventas(conn)
            st.dataframe(ventas)
            st.dataframe(citas)

    titular = _secreto("TITULAR") or "Titular pendiente de definir"
    correo_titular = _secreto("TITULAR_CORREO") or "pendiente@example.es"
    st.caption(texto_pie(textos, titular, correo_titular))
    with st.expander(textos["pie_privacidad"]):
        st.write(texto_privacidad(textos))


def _editor(conn: Any, textos: dict[str, Any], tabla: str,
            editables: tuple[str, ...]) -> None:
    """Muestra un editor con botón de guardado y validación.

    Al guardar se escribe en SQLite y el mensaje siguiente del bot ya
    usa el dato nuevo (cambio en caliente, ver 03.5).
    """
    original = cargar_tabla(conn, tabla)
    ocultas = [c for c in ("precio_centimos", "iva_incluido") if c in original.columns]
    vista = original.drop(columns=ocultas)
    bloqueadas = [c for c in vista.columns if c not in editables]
    editado = st.data_editor(vista, num_rows="fixed", disabled=bloqueadas,
                             key=f"editor_{tabla}")
    if st.button(textos["guardar"], key=f"guardar_{tabla}"):
        try:
            guardar_tabla(conn, tabla, original, editado, editables)
        except ValueError as error:
            codigo = str(error)
            st.error(textos.get(codigo, codigo))
        else:
            st.session_state["aviso_cambio"] = True
            st.rerun()


if __name__ == "__main__":
    main()
