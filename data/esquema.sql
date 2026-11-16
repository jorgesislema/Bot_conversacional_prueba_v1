-- Esquema SQLite de la demo (docs/03_ARQUITECTURA_Y_PLAN.md, sección 3).
-- Dinero en céntimos enteros, nunca flotantes. Fechas en ISO 8601, zona Europe/Madrid.
-- Días de semana: 0 = lunes, 6 = domingo.

CREATE TABLE IF NOT EXISTS negocio (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    nombre TEXT NOT NULL,
    nombre_bot TEXT NOT NULL,
    telefono TEXT NOT NULL,
    correo TEXT NOT NULL,
    trato_por_defecto TEXT NOT NULL CHECK (trato_por_defecto IN ('tu', 'usted')),
    idioma_por_defecto TEXT NOT NULL CHECK (idioma_por_defecto IN ('es', 'en')),
    -- Dirección para "dónde están". Si enlace_mapa está vacío, el enlace de
    -- Google Maps se arma con la dirección. Solo se aceptan enlaces https.
    direccion TEXT NOT NULL DEFAULT '',
    enlace_mapa TEXT NOT NULL DEFAULT '' CHECK (enlace_mapa = '' OR enlace_mapa LIKE 'https://%')
);

CREATE TABLE IF NOT EXISTS productos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku TEXT NOT NULL UNIQUE,
    nombre_es TEXT NOT NULL,
    nombre_en TEXT NOT NULL,
    descripcion_es TEXT NOT NULL,
    descripcion_en TEXT NOT NULL,
    categoria TEXT NOT NULL,
    marca TEXT NOT NULL,
    precio_centimos INTEGER NOT NULL CHECK (precio_centimos >= 0),
    iva_incluido INTEGER NOT NULL DEFAULT 1 CHECK (iva_incluido IN (0, 1)),
    stock INTEGER NOT NULL CHECK (stock >= 0),
    activo INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1))
);

CREATE TABLE IF NOT EXISTS servicios (
    id INTEGER PRIMARY KEY,
    nombre_es TEXT NOT NULL,
    nombre_en TEXT NOT NULL,
    duracion_min INTEGER NOT NULL CHECK (duracion_min > 0),
    precio_centimos INTEGER NOT NULL CHECK (precio_centimos >= 0),
    activo INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1))
);

CREATE TABLE IF NOT EXISTS veterinarios (
    id INTEGER PRIMARY KEY,
    nombre TEXT NOT NULL,
    especialidad TEXT NOT NULL,
    activo INTEGER NOT NULL DEFAULT 1 CHECK (activo IN (0, 1))
);

CREATE TABLE IF NOT EXISTS turnos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    veterinario_id INTEGER NOT NULL REFERENCES veterinarios (id),
    dia_semana INTEGER NOT NULL CHECK (dia_semana BETWEEN 0 AND 6),
    hora_inicio TEXT NOT NULL,
    hora_fin TEXT NOT NULL,
    CHECK (hora_fin > hora_inicio)
);

CREATE TABLE IF NOT EXISTS horarios_negocio (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    dia_semana INTEGER NOT NULL UNIQUE CHECK (dia_semana BETWEEN 0 AND 6),
    hora_apertura TEXT NOT NULL,
    hora_cierre TEXT NOT NULL,
    CHECK (hora_cierre > hora_apertura)
);

CREATE TABLE IF NOT EXISTS dias_especiales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL UNIQUE,
    cerrado INTEGER NOT NULL CHECK (cerrado IN (0, 1)),
    hora_apertura TEXT,
    hora_cierre TEXT,
    nota TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS citas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    veterinario_id INTEGER REFERENCES veterinarios (id),
    servicio_id INTEGER NOT NULL REFERENCES servicios (id),
    inicio TEXT NOT NULL,
    fin TEXT NOT NULL,
    alias_cliente TEXT NOT NULL DEFAULT '',
    CHECK (fin > inicio)
);

CREATE TABLE IF NOT EXISTS ventas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    producto_id INTEGER NOT NULL REFERENCES productos (id),
    cantidad INTEGER NOT NULL CHECK (cantidad > 0),
    total_centimos INTEGER NOT NULL CHECK (total_centimos >= 0),
    creado TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS registro_eventos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT NOT NULL,
    detalle TEXT NOT NULL,
    creado TEXT NOT NULL
);
