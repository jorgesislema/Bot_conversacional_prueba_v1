"""Pruebas del esquema y la semilla (fase 1).

Comprueban los conteos de docs/04_DATOS_FICTICIOS.md y que el dinero
va en céntimos enteros.
"""

from datetime import date

from core.esquema import crear_conexion, crear_esquema, cargar_semilla, iniciar_bd


def test_carga_20_productos_6_servicios_3_veterinarios() -> None:
    """La semilla trae 20 productos, 6 servicios y 3 veterinarios."""
    conn = iniciar_bd(date(2026, 11, 16))
    assert conn.execute("SELECT COUNT(*) FROM productos").fetchone()[0] == 20
    assert conn.execute("SELECT COUNT(*) FROM servicios").fetchone()[0] == 6
    assert conn.execute("SELECT COUNT(*) FROM veterinarios").fetchone()[0] == 3


def test_negocio_con_valores_ficticios() -> None:
    """El negocio es Mascota Feliz y el bot se llama Ana."""
    conn = iniciar_bd(date(2026, 11, 16))
    fila = conn.execute("SELECT * FROM negocio").fetchone()
    assert fila["nombre"] == "Mascota Feliz"
    assert fila["nombre_bot"] == "Ana"
    assert fila["telefono"] == "900 000 000"


def test_ningun_veterinario_se_llama_ana() -> None:
    """Ningún veterinario se llama Ana, para no confundir con el bot."""
    conn = iniciar_bd(date(2026, 11, 16))
    filas = conn.execute("SELECT nombre FROM veterinarios").fetchall()
    assert all("ana" not in str(f["nombre"]).lower() for f in filas)


def test_precios_en_centimos_enteros() -> None:
    """Todos los precios son enteros mayor o igual a cero."""
    conn = iniciar_bd(date(2026, 11, 16))
    for tabla in ("productos", "servicios"):
        filas = conn.execute(f"SELECT precio_centimos FROM {tabla}").fetchall()
        assert filas
        for fila in filas:
            assert isinstance(fila["precio_centimos"], int)
            assert fila["precio_centimos"] >= 0


def test_caso_pienso_15kg_4990_y_stock_12() -> None:
    """El pienso de 15 kg cuesta 49,90 EUR y tiene 12 de stock."""
    conn = iniciar_bd(date(2026, 11, 16))
    fila = conn.execute("SELECT * FROM productos WHERE sku = 'P002'").fetchone()
    assert fila["precio_centimos"] == 4990
    assert fila["stock"] == 12


def test_producto_sin_stock_previsto() -> None:
    """El antiparasitario de perro grande (P010) empieza sin stock."""
    conn = iniciar_bd(date(2026, 11, 16))
    fila = conn.execute("SELECT stock FROM productos WHERE sku = 'P010'").fetchone()
    assert fila["stock"] == 0


def test_seis_citas_ejemplo_reproducibles() -> None:
    """Cada sesión empieza con las mismas 6 citas de ejemplo."""
    conn1 = iniciar_bd(date(2026, 11, 16))
    conn2 = iniciar_bd(date(2026, 11, 16))
    citas1 = conn1.execute("SELECT inicio, veterinario_id FROM citas ORDER BY inicio").fetchall()
    citas2 = conn2.execute("SELECT inicio, veterinario_id FROM citas ORDER BY inicio").fetchall()
    assert len(citas1) == 6
    assert [tuple(c) for c in citas1] == [tuple(c) for c in citas2]
    vets = {c["veterinario_id"] for c in citas1}
    assert vets == {1, 2, 3}


def test_ventas_empieza_vacia() -> None:
    """La tabla de ventas empieza vacía y se llena durante la demo."""
    conn = iniciar_bd(date(2026, 11, 16))
    assert conn.execute("SELECT COUNT(*) FROM ventas").fetchone()[0] == 0


def test_cargar_semilla_dos_veces_falla() -> None:
    """La semilla no se puede cargar dos veces en la misma conexión."""
    conn = crear_conexion()
    crear_esquema(conn)
    cargar_semilla(conn, date(2026, 11, 16))
    try:
        cargar_semilla(conn, date(2026, 11, 16))
        assert False, "Se esperaba un error de integridad"
    except Exception:
        pass
