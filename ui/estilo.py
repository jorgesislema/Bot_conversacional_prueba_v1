"""Estilo visual de la demo: colores de marca y hoja CSS.

Qué hace: define los colores de Mascota Feliz y la hoja CSS que da a la
página aspecto comercial (cabecera de marca, chat dentro de un teléfono
con burbujas tipo mensajería, panel en tarjetas). Recibe: nada.
Devuelve: la hoja CSS como texto. Qué NO hace: no inserta HTML que venga
del usuario; el CSS es fijo y propio (evita inyección).

Nota legal y de marca: las burbujas recuerdan a una app de mensajería,
pero no se usa el logo, el nombre ni el verde de WhatsApp, que son
marca registrada.
"""

from __future__ import annotations

# Colores de marca. Se repiten en .streamlit/config.toml para el tema base.
MARCA = "#1F7A6D"
MARCA_OSCURA = "#165C52"
MARCA_SUAVE = "#DDF1EC"
FONDO = "#F6F8F7"
TEXTO = "#1C2B28"
GRIS = "#6B7A77"
FONDO_CHAT = "#EAF0EE"

CSS = f"""
<style>
/* Sin fuentes de Google: cargarlas envía la IP del visitante a un tercero
   (problema de RGPD). Se usa Inter si está instalada y si no la del sistema. */
html, body, .stApp {{ font-family: 'Inter', 'Segoe UI', system-ui, -apple-system, sans-serif; }}
.stApp {{ background: {FONDO}; }}
#MainMenu, footer, [data-testid="stDecoration"] {{ visibility: hidden; height: 0; }}
.block-container {{ padding-top: 1.2rem; max-width: 1200px; }}

/* Cabecera de marca */
.mf-cabecera {{
  background: linear-gradient(120deg, {MARCA} 0%, {MARCA_OSCURA} 100%);
  color: #FFFFFF; border-radius: 16px; padding: 18px 24px;
  display: flex; justify-content: space-between; align-items: center;
  box-shadow: 0 6px 20px rgba(31,122,109,.18); margin-bottom: 6px;
}}
.mf-cabecera h1 {{ color: #FFFFFF; font-size: 1.6rem; margin: 0; padding: 0; font-weight: 700; }}
.mf-cabecera p {{ color: #E6F4F1; margin: 2px 0 0 0; font-size: .92rem; }}
.mf-pastilla {{
  display: inline-block; border: 1px solid rgba(255,255,255,.7); color: #FFFFFF;
  border-radius: 999px; padding: 4px 12px; font-size: .8rem; font-weight: 500;
}}
.mf-guia {{
  background: #FFFFFF; border: 1px solid #DCE5E2; border-left: 4px solid {MARCA};
  border-radius: 10px; padding: 10px 14px; color: {TEXTO}; font-size: .9rem; margin: 8px 0 4px 0;
}}

/* Teléfono */
.st-key-telefono {{
  background: #FFFFFF; border: 10px solid #1E2422; border-radius: 34px;
  padding: 0 !important; box-shadow: 0 18px 40px rgba(0,0,0,.18);
  max-width: 430px; margin: 0 auto; overflow: hidden; gap: 0 !important;
}}
.mf-tel-barra {{
  background: {MARCA}; color: #FFFFFF; padding: 12px 14px;
  display: flex; align-items: center; gap: 10px;
}}
.mf-avatar {{
  width: 38px; height: 38px; border-radius: 50%; background: #FFFFFF; color: {MARCA};
  display: flex; align-items: center; justify-content: center; font-weight: 700;
}}
.mf-tel-nombre {{ font-weight: 600; line-height: 1.1; }}
.mf-tel-estado {{ font-size: .75rem; color: #D4EEE8; }}
.mf-tel-ia {{
  margin-left: auto; font-size: .68rem; border: 1px solid rgba(255,255,255,.7);
  border-radius: 999px; padding: 2px 8px;
}}
.mf-tel-chat {{
  background: {FONDO_CHAT}; height: 430px; overflow-y: auto; padding: 12px 10px;
  display: flex; flex-direction: column-reverse;
}}
.mf-tel-lista {{ display: flex; flex-direction: column; gap: 6px; }}
.mf-burbuja {{
  max-width: 82%; padding: 8px 11px 5px 11px; border-radius: 12px;
  font-size: .9rem; line-height: 1.35; color: {TEXTO};
  box-shadow: 0 1px 1px rgba(0,0,0,.08); word-wrap: break-word;
}}
.mf-bot {{ background: #FFFFFF; align-self: flex-start; border-top-left-radius: 3px; }}
.mf-cliente {{ background: {MARCA_SUAVE}; align-self: flex-end; border-top-right-radius: 3px; }}
.mf-hora {{ display: block; text-align: right; font-size: .68rem; color: {GRIS}; margin-top: 2px; }}
.mf-fecha {{
  align-self: center; background: #FFFFFF; color: {GRIS}; font-size: .72rem;
  border-radius: 8px; padding: 3px 10px; margin-bottom: 4px;
}}
.mf-pie-tel {{
  font-size: .7rem; line-height: 1.35; color: {GRIS}; text-align: center;
  padding: 2px 16px 18px 16px; background: #FFFFFF;
}}
.st-key-telefono [data-testid="stChatInput"] {{ margin: 6px 10px 0 10px; }}
.st-key-sugerencias {{ padding: 6px 10px 0 10px; background: #FFFFFF; }}
.st-key-sugerencias button {{
  border-radius: 999px !important; border: 1px solid {MARCA} !important;
  color: {MARCA} !important; background: #FFFFFF !important;
  font-size: .78rem !important; padding: 2px 10px !important; min-height: 0 !important;
}}

/* Panel */
.st-key-panel {{
  background: #FFFFFF; border: 1px solid #DCE5E2; border-radius: 16px;
  padding: 16px 18px; box-shadow: 0 4px 14px rgba(0,0,0,.05);
}}
.mf-panel-titulo {{ font-size: 1.15rem; font-weight: 700; color: {TEXTO}; margin: 0; }}
.mf-panel-sub {{ color: {GRIS}; font-size: .88rem; margin: 2px 0 8px 0; }}
.mf-cambio {{ font-size: .82rem; color: {TEXTO}; border-bottom: 1px dashed #DCE5E2; padding: 4px 0; }}
.st-key-panel .stButton > button[kind="primary"],
.st-key-panel [data-testid="stFormSubmitButton"] > button {{
  background: {MARCA}; border-color: {MARCA}; color: #FFFFFF;
}}
.st-key-preguntar button {{
  background: #FFFFFF !important; border: 2px solid {MARCA} !important;
  color: {MARCA} !important; font-weight: 600 !important; width: 100%;
}}
.mf-pie {{ color: {GRIS}; font-size: .78rem; text-align: center; margin-top: 18px; }}

@media (max-width: 760px) {{
  .st-key-telefono {{ border-width: 6px; border-radius: 22px; }}
  .mf-tel-chat {{ height: 360px; }}
  .mf-cabecera {{ flex-direction: column; align-items: flex-start; gap: 8px; }}
}}
</style>
"""


def hoja_css() -> str:
    """Devuelve la hoja CSS fija de la demo.

    Ejemplo:
        >>> "<style>" in hoja_css()
        True
    """
    return CSS
