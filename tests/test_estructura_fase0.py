"""Prueba de estructura de la fase 0.

Qué hace: comprueba que existen las carpetas y archivos mínimos que
pide docs/03_ARQUITECTURA_Y_PLAN.md y docs/06_DESPLIEGUE_STREAMLIT.md.
Recibe: nada. Devuelve: nada, falla si falta algún archivo clave.
Qué NO hace: no prueba lógica de negocio (llega en las fases 1 a 3).
"""

from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


def test_existen_carpetas_obligatorias() -> None:
    """Comprueba que existen las carpetas del proyecto.

    Ejemplo:
        >>> test_existen_carpetas_obligatorias()
        Pasa si core/, data/, i18n/, ui/, tests/ y evals/ existen.
    """
    for carpeta in ("core", "data", "i18n", "ui", "tests", "evals"):
        assert (RAIZ / carpeta).is_dir(), f"Falta la carpeta {carpeta}/"


def test_existen_archivos_de_despliegue() -> None:
    """Comprueba los archivos que necesita Streamlit Cloud.

    Ejemplo:
        >>> test_existen_archivos_de_despliegue()
        Pasa si app.py, requirements y la config de Streamlit existen.
    """
    for archivo in (
        "app.py",
        "requirements.txt",
        ".streamlit/config.toml",
        ".streamlit/secrets.toml.example",
        ".gitignore",
    ):
        assert (RAIZ / archivo).is_file(), f"Falta el archivo {archivo}"


def test_requirements_incluye_dependencias_minimas() -> None:
    """Comprueba que requirements.txt fija streamlit, pandas y rapidfuzz.

    Ejemplo:
        >>> test_requirements_incluye_dependencias_minimas()
        Pasa si las tres dependencias aparecen con versión fija.
    """
    contenido = (RAIZ / "requirements.txt").read_text(encoding="utf-8").lower()
    for dependencia in ("streamlit==", "pandas==", "rapidfuzz=="):
        assert dependencia in contenido, f"Falta {dependencia} en requirements.txt"


def test_config_sin_estadisticas_de_uso() -> None:
    """Comprueba que la config desactiva las estadísticas de uso.

    Por qué: la demo no usa cookies de seguimiento (marco legal 01).

    Ejemplo:
        >>> test_config_sin_estadisticas_de_uso()
        Pasa si gatherUsageStats es false.
    """
    contenido = (RAIZ / ".streamlit" / "config.toml").read_text(encoding="utf-8")
    assert "gatherUsageStats = false" in contenido


def test_ejemplo_de_secretos_sin_valores_reales() -> None:
    """Comprueba que la plantilla de secretos trae las claves esperadas.

    Ejemplo:
        >>> test_ejemplo_de_secretos_sin_valores_reales()
        Pasa si aparecen las claves de docs/06 sin valores reales.
    """
    contenido = (RAIZ / ".streamlit" / "secrets.toml.example").read_text(encoding="utf-8")
    for clave in ("PROVEEDOR_PRINCIPAL", "CLAVE_PRINCIPAL", "LIMITE_DIARIO", "LIMITE_SESION"):
        assert clave in contenido, f"Falta la clave {clave} en secrets.toml.example"
