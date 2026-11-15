"""Punto de entrada de la demo en Streamlit.

Qué hace: arranca la interfaz mínima de la fase 0 y confirma que el
entorno carga. Recibe: nada (Streamlit gestiona la sesión). Devuelve:
nada, dibuja un texto en la página. Qué NO hace: no abre chat, no lee
la base de datos ni llama a ningún proveedor de IA (fases 3 y 4).
"""

import streamlit as st


def main() -> None:
    """Dibuja la página provisional de la fase 0.

    Ejemplo:
        >>> main()  # doctest: +SKIP
        Dibuja el título provisional en la app.
    """
    # Texto provisional: el chat y el panel llegan en la fase 4.
    st.title("Mascota Feliz - demo (fase 0)")
    st.write("Estructura del repositorio lista. El chat llega en fases posteriores.")


if __name__ == "__main__":
    main()
