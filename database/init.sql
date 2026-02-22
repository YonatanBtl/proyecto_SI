-- ============================================================
-- Script de inicialización de base de datos
-- Sistema de Gestión de Prácticas Preprofesionales
-- ============================================================

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- TABLA: estudiantes
-- ============================================================
CREATE TABLE estudiantes (
    id                SERIAL PRIMARY KEY,
    nombre            VARCHAR(100) NOT NULL,
    email             VARCHAR(100) UNIQUE NOT NULL,
    telefono          VARCHAR(15),
    carrera           VARCHAR(100),
    universidad       VARCHAR(100),
    promedio          DECIMAL(4,2),
    semestre          INTEGER,
    cv_url            TEXT,
    cv_texto          TEXT,
    habilidades       TEXT[],
    meses_experiencia INTEGER DEFAULT 0,
    nivel_ingles      VARCHAR(50),
    proyectos         TEXT[],
    ubicacion         VARCHAR(100),
    lat               DECIMAL(10,8),
    lng               DECIMAL(11,8),
    horas_disponibles INTEGER,
    calidad_cv        INTEGER,
    completitud       INTEGER,
    fecha_registro    TIMESTAMP DEFAULT NOW(),
    activo            BOOLEAN DEFAULT TRUE
);

-- ============================================================
-- TABLA: empresas
-- ============================================================
CREATE TABLE empresas (
    id                  SERIAL PRIMARY KEY,
    nombre              VARCHAR(100) NOT NULL,
    area                VARCHAR(100),
    descripcion         TEXT,
    requisitos          TEXT[],
    carreras_aceptadas  TEXT[],
    experiencia_minima  INTEGER,
    horas_requeridas    INTEGER,
    salario             DECIMAL(10,2),
    ubicacion           VARCHAR(100),
    lat                 DECIMAL(10,8),
    lng                 DECIMAL(11,8),
    modalidad           VARCHAR(50),
    tipo                VARCHAR(50) DEFAULT 'practica',
    fecha_limite        DATE,
    activa              BOOLEAN DEFAULT TRUE,
    fecha_creacion      TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- TABLA: matches
-- ============================================================
CREATE TABLE matches (
    id                  SERIAL PRIMARY KEY,
    estudiante_id       INTEGER REFERENCES estudiantes(id) ON DELETE CASCADE,
    empresa_id          INTEGER REFERENCES empresas(id) ON DELETE CASCADE,
    score_requisitos    DECIMAL(5,2),
    score_atractivo     DECIMAL(5,2),
    score_final         DECIMAL(5,2),
    probabilidad_exito  DECIMAL(5,2),
    desglose            JSONB,
    estado              VARCHAR(50) DEFAULT 'generado',
    fecha_match         TIMESTAMP DEFAULT NOW(),
    fecha_actualizacion TIMESTAMP DEFAULT NOW(),
    UNIQUE(estudiante_id, empresa_id)
);

-- ============================================================
-- TABLA: postulaciones
-- ============================================================
CREATE TABLE postulaciones (
    id                SERIAL PRIMARY KEY,
    match_id          INTEGER REFERENCES matches(id),
    estudiante_id     INTEGER REFERENCES estudiantes(id) ON DELETE CASCADE,
    empresa_id        INTEGER REFERENCES empresas(id) ON DELETE CASCADE,
    estado            VARCHAR(50) DEFAULT 'postulado',
    prioridad         VARCHAR(20),
    fecha_postulacion TIMESTAMP DEFAULT NOW(),
    fecha_respuesta   TIMESTAMP,
    notas             TEXT
);

-- ============================================================
-- TABLA: historial_aprendizaje  ← requerida por LearningSystem
-- ============================================================
CREATE TABLE historial_aprendizaje (
    id            SERIAL PRIMARY KEY,
    match_id      INTEGER REFERENCES matches(id) ON DELETE SET NULL,
    estudiante_id INTEGER REFERENCES estudiantes(id) ON DELETE CASCADE,
    empresa_id    INTEGER REFERENCES empresas(id) ON DELETE CASCADE,
    resultado     VARCHAR(50) NOT NULL,  -- contratado | rechazado | entrevista | sin_respuesta
    caracteristicas JSONB,               -- carrera, universidad, habilidades, score_match
    fecha_registro TIMESTAMP DEFAULT NOW(),
    UNIQUE(match_id)                     -- un resultado por match
);

-- ============================================================
-- TABLA: notificaciones
-- ============================================================
CREATE TABLE notificaciones (
    id          SERIAL PRIMARY KEY,
    estudiante_id INTEGER REFERENCES estudiantes(id),
    tipo        VARCHAR(50),
    asunto      VARCHAR(200),
    mensaje     TEXT,
    estado      VARCHAR(50) DEFAULT 'enviado',
    fecha_envio TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- TABLA: anomalias
-- ============================================================
CREATE TABLE anomalias (
    id              SERIAL PRIMARY KEY,
    tipo            VARCHAR(50),
    entidad_tipo    VARCHAR(50),
    entidad_id      INTEGER,
    descripcion     TEXT,
    severidad       VARCHAR(20),
    fecha_deteccion TIMESTAMP DEFAULT NOW(),
    resuelta        BOOLEAN DEFAULT FALSE
);

-- ============================================================
-- TABLA: metricas
-- ============================================================
CREATE TABLE metricas (
    id                        SERIAL PRIMARY KEY,
    fecha                     DATE DEFAULT CURRENT_DATE,
    total_estudiantes         INTEGER,
    estudiantes_activos       INTEGER,
    total_empresas            INTEGER,
    total_matches             INTEGER,
    matches_exitosos          INTEGER,
    tasa_exito                DECIMAL(5,2),
    tiempo_respuesta_promedio DECIMAL(5,2),
    kpis                      JSONB,
    fecha_calculo             TIMESTAMP DEFAULT NOW()
);

-- ============================================================
-- ÍNDICES
-- ============================================================
CREATE INDEX idx_matches_estudiante      ON matches(estudiante_id);
CREATE INDEX idx_matches_empresa         ON matches(empresa_id);
CREATE INDEX idx_matches_score           ON matches(score_final DESC);
CREATE INDEX idx_postulaciones_estado    ON postulaciones(estado);
CREATE INDEX idx_postulaciones_fecha     ON postulaciones(fecha_postulacion);
CREATE INDEX idx_estudiantes_activo      ON estudiantes(activo);
CREATE INDEX idx_empresas_activa         ON empresas(activa);
CREATE INDEX idx_historial_estudiante    ON historial_aprendizaje(estudiante_id);
CREATE INDEX idx_historial_resultado     ON historial_aprendizaje(resultado);
CREATE INDEX idx_anomalias_resuelta      ON anomalias(resuelta);

-- ============================================================
-- TRIGGER: actualizar fecha_actualizacion en matches
-- ============================================================
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.fecha_actualizacion = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_matches_modtime
BEFORE UPDATE ON matches
FOR EACH ROW
EXECUTE FUNCTION update_modified_column();

-- ============================================================
-- DATOS INICIALES DE EJEMPLO
-- ============================================================
INSERT INTO empresas (
    nombre, area, descripcion, requisitos, carreras_aceptadas,
    experiencia_minima, horas_requeridas, salario,
    ubicacion, lat, lng, modalidad, fecha_limite
) VALUES
(
    'Pragma Tech Peru', 'Desarrollo Software',
    'Consultora tecnológica líder en transformación digital',
    ARRAY['python', 'react', 'sql', 'git'],
    ARRAY['Ing. Sistemas', 'Ing. Software'],
    6, 30, 1500,
    'San Isidro', -12.0931, -77.0465, 'hibrido', '2026-06-30'
),
(
    'Circus Grey Lima', 'Marketing',
    'Agencia de publicidad y marketing integrado',
    ARRAY['social media', 'google ads', 'seo', 'canva'],
    ARRAY['Marketing', 'Comunicaciones'],
    3, 25, 1000,
    'Miraflores', -12.1190, -77.0349, 'remoto', '2026-05-31'
),
(
    'Credicorp Capital', 'Finanzas',
    'Gestión de inversiones y banca de inversión',
    ARRAY['excel', 'sql', 'power bi'],
    ARRAY['Economía', 'Administración', 'Ing. Industrial'],
    0, 35, 1800,
    'San Isidro', -12.0931, -77.0465, 'presencial', '2026-04-30'
);

-- ============================================================
-- MENSAJE DE ÉXITO
-- ============================================================
DO $$
BEGIN
    RAISE NOTICE '✅ Base de datos inicializada correctamente';
    RAISE NOTICE '📋 Tablas: estudiantes, empresas, matches, postulaciones,';
    RAISE NOTICE '          historial_aprendizaje, notificaciones, anomalias, metricas';
    RAISE NOTICE '🏢 3 empresas de ejemplo insertadas';
END $$;