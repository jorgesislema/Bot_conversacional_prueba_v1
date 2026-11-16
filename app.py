"""Entrada de la demo en Streamlit.

Qué hace: dibuja la cabecera de marca, el chat dentro de un teléfono a
la izquierda y el panel "Prueba el motor" a la derecha, con aviso de IA
fijo, banner de demo y pie legal. Recibe: nada (Streamlit gestiona la
sesión). Devuelve: nada, dibuja la página. Qué NO hace: no guarda datos
entre sesiones; cada visita tiene su propia base en memoria que se
destruye al cerrar.
"""

from __future__ import annotations

import html
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
from ui.acciones import (
    CATEGORIAS,
    DIAS_EN,
    DIAS_ES,
    Cambio,
    anadir_producto,
    cambiar_direccion,
    cambiar_horario,
    cambiar_precio,
    datos_ubicacion,
    horario_de,
    precio_actual,
    productos_para_selector,
    ultimos_cambios,
)
from ui.chat import html_barra, html_conversacion
from ui.estilo import hoja_css
from ui.legal import texto_pie, texto_privacidad
from ui.panel import cargar_tabla, guardar_tabla, resumen_ventas

ZONA = ZoneInfo("Europe/Madrid")

# URLs base conocidas; si el secreto trae una URL completa, se usa tal cual.
URLS = {
    "mistral": "https://api.mistral.ai/v1",
    "openai": "https://api.openai.com/v1",
    "openrouter": "https://openrouter.ai/api/v1",
    "deepseek": "https://api.deepseek.com/v1",
}

# Columnas técnicas que no aportan al visitante en "Datos completos".
COLUMNAS_OCULTAS = ("id", "sku", "veterinario_id", "precio_centimos", "iva_incluido")


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


def _hora() -> str:
    """Hora actual de Madrid en formato HH:MM para las burbujas."""
    return datetime.now(ZONA).strftime("%H:%M")


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
    st.session_state["ultimo_cambio"] = None
    st.session_state["pendiente"] = ""


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


def _enviar(conn: Any, estado: Any, textos: dict[str, Any], pregunta: str,
            proveedor: ProveedorIA | None, limite_sesion: int,
            limite_diario: int) -> None:
    """Pasa la pregunta por el motor y guarda ambos mensajes en la sesión.

    Lo usan la caja de texto, las sugerencias y el botón
    "Pregúntale ahora a Ana", para que los tres sigan el mismo camino.
    """
    contador = obtener_contador(limite_diario)
    cupo = contador.hay_cupo()
    if cupo:
        contador.registrar()
    resultado = responder(conn, estado, textos, pregunta, datetime.now(ZONA),
                          proveedor, cupo_diario=cupo, limite_sesion=limite_sesion)
    st.session_state["mensajes"].append(
        {"rol": "usuario", "texto": pregunta, "hora": _hora()})
    st.session_state["mensajes"].append(
        {"rol": "asistente", "texto": resultado.texto, "hora": _hora()})


def _cabecera(negocio: Any, textos: dict[str, Any]) -> None:
    """Franja de marca con nombre, subtítulo, etiqueta IA y selector de idioma."""
    izquierda, derecha = st.columns([4, 1], vertical_alignment="center")
    with izquierda:
        st.markdown(
            '<div class="mf-cabecera"><div>'
            f'<h1>{negocio["nombre"]}</h1>'
            f'<p>{textos["subtitulo_negocio"]}</p></div>'
            f'<span class="mf-pastilla">{textos["etiqueta_ia"]}</span></div>',
            unsafe_allow_html=True,
        )
    with derecha:
        idioma = st.segmented_control(
            "Idioma / Language", ["ES", "EN"],
            default="ES" if st.session_state["idioma"] == "es" else "EN",
            label_visibility="collapsed", key="selector_idioma",
        )
        nuevo = "en" if idioma == "EN" else "es"
        if idioma and nuevo != st.session_state["idioma"]:
            st.session_state["idioma"] = nuevo
            estado = st.session_state["estado"]
            estado.idioma = nuevo
            # Si el cliente aún no escribió, el aviso de IA se vuelve a
            # mostrar en el idioma elegido; si ya hay conversación, se respeta.
            if not any(m["rol"] == "usuario" for m in st.session_state["mensajes"]):
                st.session_state["mensajes"] = []
                estado.aviso_ia_mostrado = False
            st.rerun()


def _telefono(conn: Any, estado: Any, negocio: Any, textos: dict[str, Any],
              proveedor: ProveedorIA | None, limite_sesion: int,
              limite_diario: int) -> None:
    """Chat dentro de un marco de teléfono, con sugerencias y caja de texto."""
    with st.container(key="telefono"):
        st.markdown(
            html_barra(str(negocio["nombre_bot"]), textos["estado_en_linea"],
                       textos["etiqueta_ia"])
            + html_conversacion(st.session_state["mensajes"], textos["etiqueta_hoy"]),
            unsafe_allow_html=True,
        )
        # Las sugerencias se muestran al inicio para que el visitante sepa
        # qué probar; se ocultan tras tres mensajes para no estorbar.
        n_cliente = sum(1 for m in st.session_state["mensajes"] if m["rol"] == "usuario")
        if n_cliente < 3:
            with st.container(key="sugerencias", horizontal=True):
                for i, sugerencia in enumerate(textos["sugerencias"]):
                    if st.button(sugerencia, key=f"sug_{i}"):
                        st.session_state["pendiente"] = sugerencia
        pregunta = st.chat_input(textos["placeholder_chat"])
        if pregunta:
            st.session_state["pendiente"] = pregunta
        st.markdown(
            f'<div class="mf-pie-tel">{textos["banner_demo"]} · '
            f'{textos["mensajes_restantes"].format(n=restantes(estado, limite_sesion))}'
            + (f' · {textos["modo_sin_ia"]}' if proveedor is None else "")
            + "</div>",
            unsafe_allow_html=True,
        )
    persona, reset = st.columns(2)
    with persona:
        if st.button(textos["boton_persona"], use_container_width=True):
            st.session_state["mensajes"].append(
                {"rol": "asistente", "hora": _hora(),
                 "texto": _derivar_directo(conn, textos, st.session_state["idioma"])})
            st.rerun()
    with reset:
        if st.button(textos["boton_reset"], use_container_width=True):
            for clave in ("conn", "estado", "mensajes", "idioma", "ultimo_cambio",
                          "pendiente"):
                st.session_state.pop(clave, None)
            st.rerun()


def _aplicar(textos: dict[str, Any], accion: Any) -> None:
    """Ejecuta una acción del panel y muestra el error traducido si falla."""
    try:
        cambio: Cambio = accion()
    except ValueError as error:
        st.error(textos.get(str(error), str(error)))
        return
    st.session_state["ultimo_cambio"] = cambio
    st.rerun()


def _panel(conn: Any, textos: dict[str, Any]) -> None:
    """Panel "Prueba el motor": acciones guiadas y datos completos."""
    idioma = st.session_state["idioma"]
    dias = DIAS_EN if idioma == "en" else DIAS_ES
    with st.container(key="panel"):
        st.markdown(
            f'<p class="mf-panel-titulo">{textos["panel_titulo"]}</p>'
            f'<p class="mf-panel-sub">{textos["panel_sub"]}</p>',
            unsafe_allow_html=True,
        )
        cambio = st.session_state.get("ultimo_cambio")
        if isinstance(cambio, Cambio):
            st.success(f'{textos["cambio_aplicado"]} {cambio.resumen}')
            with st.container(key="preguntar"):
                if st.button(textos["boton_preguntar"], key="boton_preguntar"):
                    st.session_state["pendiente"] = cambio.pregunta(idioma)
                    st.session_state["ultimo_cambio"] = None

        precio, producto, horario, ubicacion, datos = st.tabs([
            textos["pestana_precio"], textos["pestana_producto"],
            textos["pestana_horario"], textos["pestana_ubicacion"],
            textos["pestana_datos"]])

        with ubicacion:
            direccion_actual, enlace_actual = datos_ubicacion(conn)
            with st.form("form_ubicacion", border=False):
                direccion = st.text_input(textos["campo_direccion"], value=direccion_actual)
                enlace = st.text_input(textos["campo_enlace_mapa"], value=enlace_actual,
                                       help=textos["ayuda_enlace_mapa"])
                if st.form_submit_button(textos["boton_guardar_direccion"], type="primary"):
                    _aplicar(textos, lambda: cambiar_direccion(conn, direccion, enlace))

        with precio:
            opciones = productos_para_selector(conn, idioma)
            # El selector va fuera del formulario para que, al cambiar de
            # producto, el campo de precio se rellene con su precio actual.
            # Antes el campo salía vacío con un ejemplo gris y parecía lleno.
            # Las opciones son ids y la etiqueta se calcula aparte: si la
            # etiqueta (que lleva el precio) fuera la opción, al cambiar el
            # precio Streamlit volvería al primer producto.
            etiquetas = dict(opciones)
            elegido = st.selectbox(textos["campo_producto"], list(etiquetas),
                                   format_func=lambda i: etiquetas.get(i, ""),
                                   key=f"sel_precio_{idioma}")
            if elegido is not None:
                actual = precio_actual(conn, elegido, idioma)
                with st.form(f"form_precio_{elegido}", border=False):
                    nuevo = st.text_input(textos["campo_precio_nuevo"], value=actual,
                                          help=textos["ayuda_decimales"])
                    if st.form_submit_button(textos["boton_aplicar"], type="primary"):
                        _aplicar(textos, lambda: cambiar_precio(conn, elegido, nuevo))

        with producto:
            with st.form("form_producto", border=False, clear_on_submit=True):
                nombre = st.text_input(textos["campo_nombre"],
                                       placeholder=textos["ejemplo_nombre"])
                columnas = st.columns(3)
                categoria = columnas[0].selectbox(textos["campo_categoria"], CATEGORIAS)
                euros = columnas[1].text_input(textos["campo_precio"],
                                               placeholder=textos["ejemplo_precio"],
                                               help=textos["ayuda_decimales"])
                stock = columnas[2].number_input(textos["campo_stock"], min_value=0,
                                                 value=20, step=1)
                descripcion = st.text_input(textos["campo_descripcion"])
                if st.form_submit_button(textos["boton_anadir"], type="primary"):
                    _aplicar(textos, lambda: anadir_producto(
                        conn, nombre, categoria, euros, int(stock), descripcion))

        with horario:
            dia = st.selectbox(textos["campo_dia"], range(7),
                               format_func=lambda d: dias[d].capitalize())
            actual = horario_de(conn, dia)
            with st.form(f"form_horario_{dia}", border=False):
                columnas = st.columns(2)
                apertura = columnas[0].text_input(
                    textos["campo_apertura"], value=actual[0] if actual else "10:00")
                cierre = columnas[1].text_input(
                    textos["campo_cierre"], value=actual[1] if actual else "14:00")
                cerrado = st.checkbox(textos["campo_cerrado"], value=actual is None)
                if st.form_submit_button(textos["boton_aplicar"], type="primary"):
                    _aplicar(textos, lambda: cambiar_horario(
                        conn, dia, apertura.strip(), cierre.strip(), cerrado))

        with datos:
            st.caption(textos["ayuda_datos"])
            _editor(conn, textos, "productos",
                    ("nombre_es", "nombre_en", "descripcion_es",
                     "descripcion_en", "precio_eur", "stock", "activo"))
            _editor(conn, textos, "servicios",
                    ("nombre_es", "nombre_en", "duracion_min", "precio_eur", "activo"))
            _editor(conn, textos, "veterinarios", ("nombre", "especialidad", "activo"))
            st.caption(textos["titulo_ventas"])
            ventas, citas = resumen_ventas(conn)
            st.dataframe(ventas, hide_index=True)
            st.dataframe(citas, hide_index=True)

        st.markdown(f'**{textos["ultimos_cambios"]}**')
        cambios = ultimos_cambios(conn)
        if cambios:
            # Se escapa: el detalle puede incluir un nombre escrito por el visitante.
            st.markdown("".join(f'<div class="mf-cambio">{html.escape(c)}</div>'
                                for c in cambios),
                        unsafe_allow_html=True)
        else:
            st.caption(textos["sin_cambios"])


def _editor(conn: Any, textos: dict[str, Any], tabla: str,
            editables: tuple[str, ...]) -> None:
    """Tabla editable con botón de guardado y validación.

    Al guardar se escribe en SQLite y el mensaje siguiente del bot ya
    usa el dato nuevo (cambio en caliente, ver 03.5). El id se conserva
    como índice oculto para poder guardar, pero no se muestra.
    """
    original = cargar_tabla(conn, tabla)
    ocultas = [c for c in COLUMNAS_OCULTAS if c in original.columns and c != "id"]
    vista = original.drop(columns=ocultas)
    bloqueadas = [c for c in vista.columns if c not in editables]
    # Precio con dos decimales y paso de 0,01: antes la columna se trataba
    # como número sin formato y costaba escribir céntimos.
    configuracion: dict[str, Any] = {"id": None}
    if "precio_eur" in vista.columns:
        configuracion["precio_eur"] = st.column_config.NumberColumn(
            "EUR", min_value=0.0, step=0.01, format="%.2f")
    editado = st.data_editor(vista, num_rows="fixed", disabled=bloqueadas,
                             key=f"editor_{tabla}", hide_index=True,
                             column_config=configuracion)
    if st.button(textos["guardar"], key=f"guardar_{tabla}"):
        try:
            guardar_tabla(conn, tabla, original, editado, editables)
        except ValueError as error:
            codigo = str(error)
            st.error(textos.get(codigo, codigo))
        else:
            st.session_state["ultimo_cambio"] = None
            st.rerun()


def main() -> None:
    """Dibuja la demo completa: cabecera, teléfono, panel y pie."""
    st.set_page_config(page_title="Mascota Feliz - demo", layout="wide")
    st.markdown(hoja_css(), unsafe_allow_html=True)
    if "conn" not in st.session_state:
        _iniciar_sesion()
    conn = st.session_state["conn"]
    estado = st.session_state["estado"]
    negocio = conn.execute("SELECT * FROM negocio").fetchone()
    textos = cargar_textos(st.session_state["idioma"])

    limite_sesion = _entero_secreto("LIMITE_SESION", LIMITE_SESION_POR_DEFECTO)
    limite_diario = _entero_secreto("LIMITE_DIARIO", LIMITE_DIARIO_POR_DEFECTO)
    proveedor = construir_proveedor()

    # Aviso de IA como primer mensaje, siempre (Ley de IA, art. 50).
    if not estado.aviso_ia_mostrado:
        primer = aviso_inicial(textos, estado.idioma, estado.trato,
                               str(negocio["nombre"]), str(negocio["nombre_bot"]),
                               datetime.now(ZONA))
        st.session_state["mensajes"].append(
            {"rol": "asistente", "texto": primer, "hora": _hora()})
        estado.aviso_ia_mostrado = True

    _cabecera(negocio, textos)
    st.markdown(f'<div class="mf-guia">{textos["guia_inicio"]}</div>',
                unsafe_allow_html=True)

    chat_col, panel_col = st.columns([1, 1], gap="large")
    with panel_col:
        _panel(conn, textos)
    with chat_col:
        _telefono(conn, estado, negocio, textos, proveedor, limite_sesion, limite_diario)

    # La pregunta pendiente (caja, sugerencia o botón del panel) se procesa
    # una sola vez y luego se redibuja la página con la respuesta.
    pendiente = st.session_state.get("pendiente", "")
    if pendiente:
        st.session_state["pendiente"] = ""
        with st.spinner(f'{negocio["nombre_bot"]}...'):
            _enviar(conn, estado, textos, pendiente, proveedor,
                    limite_sesion, limite_diario)
        st.rerun()

    titular = _secreto("TITULAR") or "Titular pendiente de definir"
    correo_titular = _secreto("TITULAR_CORREO") or "pendiente@example.es"
    st.markdown(f'<div class="mf-pie">{texto_pie(textos, titular, correo_titular)}</div>',
                unsafe_allow_html=True)
    with st.expander(textos["pie_privacidad"]):
        st.write(texto_privacidad(textos))


if __name__ == "__main__":
    main()
