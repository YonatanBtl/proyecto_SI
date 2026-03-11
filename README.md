# PractiMatch — Sistema Inteligente de Matching Bidireccional

Sistema multi-agente inteligente para matching automático y **bidireccional** entre estudiantes universitarios y empresas que ofrecen prácticas preprofesionales. Desarrollado como proyecto final del curso de Sistemas Inteligentes 2026.

## ✅ Estado del Proyecto — Versión Final

| Componente | Estado |
|---|---|
| Agente 1 — MatchingEngine (TF-IDF bidireccional, 5 dimensiones) | ✅ Implementado |
| Agente 2 — NLPAnalyzer (spaCy + regex + base de 100+ skills) | ✅ Implementado |
| Agente 3 — LearningSystem (pesos adaptativos por área, PostgreSQL) | ✅ Implementado |
| Agente 4 — AnomalyDetector (Z-score estadístico, 4 tipos) | ✅ Implementado |
| Agente 5 — MonitorAgent (KPIs + alertas anti-duplicados 24h) | ✅ Implementado |
| API Flask REST (20+ endpoints) | ✅ Implementado |
| Frontend HTML (5 interfaces conectadas a datos reales) | ✅ Implementado |
| Workflow 1 n8n — Monitor KPIs (schedule automático) | ✅ Implementado |
| Workflow 2 n8n — Detección anomalías (schedule 1 hora) | ✅ Implementado |
| Workflow 3 n8n — Pipeline nuevo estudiante (webhook) | ✅ Implementado |
| Dataset sintético cargado en PostgreSQL | ✅ 101 est. · 50 emp. · 779 matches |
| Fix alertas duplicadas (1 alerta por tipo cada 24h) | ✅ Implementado |
| pgAdmin 4 | ✅ Implementado |

---

## 🚀 Inicio Rápido

### Prerrequisitos

- Docker Desktop instalado y en ejecución
- 8 GB RAM mínimo recomendado
- Windows 11 / Linux / macOS

### Instalación

```bash
# 1. Clonar el proyecto
git clone [url-repositorio]
cd proyecto-practicas

# 2. Levantar los 4 contenedores
docker-compose up -d

# Esto levanta:
#   API Flask      → localhost:5000
#   PostgreSQL     → localhost:5432 (interno)
#   n8n            → localhost:5678
#   pgAdmin 4      → localhost:5050

# 3. Esperar ~30 segundos y verificar que todo corre
docker-compose ps

# 4. Generar el dataset sintético (101 estudiantes, 50 empresas contextualizados para Lima)
python data/generar_dataset.py

# 5. Cargar el dataset a PostgreSQL y calcular los 779 matches
python data/cargar_dataset.py

# 5. Acceder al sistema
#   Web:     http://localhost:5000
#   n8n:     http://localhost:5678  (admin / admin123)
#   pgAdmin: http://localhost:5050  (admin@admin.com / admin)
```

### Verificar que funciona

```bash
# Health check de la API
curl http://localhost:5000/health
# → {"status": "ok", "database": "conectado"}

# KPIs del sistema
curl http://localhost:5000/api/kpis
```

---

## 📁 Estructura del Proyecto

```
proyecto-practicas/
├── docker-compose.yml              # 4 contenedores: API, PostgreSQL, n8n, pgAdmin
├── api/
│   ├── app.py                      # API Flask — 20+ endpoints REST
│   ├── Dockerfile
│   ├── requirements.txt
│   └── agentes/
│       ├── matching_engine.py      # Agente 1: TF-IDF + scoring bidireccional (5 dimensiones)
│       ├── nlp_analyzer.py         # Agente 2: spaCy NER + regex + base de conocimiento
│       ├── learning_system.py      # Agente 3: Pesos adaptativos por área, persiste en BD
│       ├── anomaly_detector.py     # Agente 4: Z-score estadístico, 4 tipos de anomalía
│       └── monitor_agent.py        # Agente 5: KPIs + alertas con anti-duplicados 24h
├── frontend/
│   ├── index.html                  # Landing page
│   ├── dashboard.html              # KPIs en tiempo real + alertas activas
│   ├── matches.html                # Motor de matching interactivo con desglose
│   ├── analisis-cv.html            # Análisis NLP de CVs con drag & drop
│   └── anomalias.html              # Detección y visualización de anomalías
├── database/
│   └── init.sql                    # 9 tablas PostgreSQL con índices y relaciones FK
├── n8n/
│   └── workflows/
│       ├── monitor_kpis.json       # Workflow 1: Schedule automático → /api/kpis → alertas
│       ├── detectar_anomalias.json # Workflow 2: Schedule 1 hora → /api/detectar-anomalias
│       └── pipeline_estudiante.json# Workflow 3: Webhook → /api/calcular-matches
└── data/
    ├── generar_dataset.py          # Genera dataset sintético contextualizado Lima
    └── cargar_dataset.py           # Carga datos a PostgreSQL y calcula todos los matches
```

> **Nota sobre el frontend**: se optó por HTML5 + JavaScript vanilla en lugar de React.
> Cada página se conecta a la API mediante `fetch()` y muestra datos reales en tiempo real.
> Esta decisión simplificó el deployment y eliminó una capa de dependencias.

---

## 🤖 Los 5 Agentes Inteligentes

### Agente 1 — MatchingEngine

Motor de decisión **bidireccional**: calcula compatibilidad en dos direcciones simultáneas.

- **Score Requisitos (60%)**: ¿El estudiante cumple lo que pide la empresa?
- **Score Atractivo (40%)**: ¿La empresa es adecuada para el perfil del estudiante?
- **Score Final** = (Req × 0.60) + (Atr × 0.40)

**5 dimensiones con pesos configurables:**

| Dimensión | Peso base | Técnica | Casos límite manejados |
|---|---|---|---|
| Habilidades | 35% | TF-IDF + similitud coseno | Lista vacía → score 0, sin error |
| Experiencia | 25% | Ratio de meses | Empresa requiere 0 meses → score 1.0 automático |
| Carrera | 20% | Lookup exacto | Carrera fuera de lista → 0.3 (penaliza, no descarta) |
| Ubicación | 10% | Distancia GPS | > 50 km → score 0 (penalización máxima) |
| Disponibilidad | 10% | Ratio de horas | — |

Los pesos son ajustados automáticamente por el **LearningSystem** según el área de negocio.

---

### Agente 2 — NLPAnalyzer

Extrae información estructurada de CVs en **PDF y DOCX** sin intervención manual, combinando tres técnicas:

| Campo extraído | Técnica principal | Variantes manejadas |
|---|---|---|
| Nombre | spaCy PERSON NER + regex mayúsculas | EDGAR QUISPE → Edgar Quispe |
| Email | Regex RFC 5322 case-insensitive | Cualquier formato |
| Universidad | Base de conocimiento + spaCy ORG | PUCP, UNMSM, UPC, UNI, etc. |
| Habilidades | Base de 100+ tecnologías categorizadas | Python, React, SAP, Power BI, etc. |
| Experiencia | Regex fechas múltiples formatos | MM/YYYY, "Sept 2023", "mes YYYY" |
| Nivel inglés | Patrones texto con lista negra | básico, B1, B2, C1, avanzado |

Maneja CVs con columnas dobles, nombres en mayúsculas y fechas escritas en texto.

> **Limitación conocida**: CVs escaneados como imagen requieren OCR — no soportado en esta versión.

---

### Agente 3 — LearningSystem

Aprendizaje adaptativo que **ajusta los pesos del MatchingEngine por área de negocio**:

1. Cuando un match resulta en `contratado`, guarda las características del perfil exitoso en `historial_aprendizaje`
2. Con 5+ casos acumulados en una misma área, recalcula los pesos óptimos para esa área
3. Los pesos aprendidos se persisten en PostgreSQL — sobreviven reinicios de Docker

> Con el dataset sintético actual, `historial_aprendizaje` tiene 0 filas porque los resultados de contratación son aleatorios. El sistema opera con pesos base hasta recibir datos reales de producción.

---

### Agente 4 — AnomalyDetector

Detección estadística con **Z-score** sobre el comportamiento histórico:

| Tipo | Criterio | Severidad |
|---|---|---|
| `empresa_inactiva` | 5+ postulaciones recibidas y 0% de respuestas en 30 días | ALTA |
| `requisitos_imposibles` | Requisitos que 0% de estudiantes posee | ALTA |
| `estudiante_spam` | 15+ postulaciones a 5+ áreas distintas en 7 días | MEDIA |
| `pico_anomalo` | Volumen con Z-score > 2.5 sobre la media histórica | MEDIA |
| `score_bajo` | score_final < 30% | BAJA |

Resultado con dataset actual: **73 anomalías** — 3 ALTA · 16 MEDIA · 54 BAJA.

---

### Agente 5 — MonitorAgent

Supervisión continua del sistema con **alertas persistidas en PostgreSQL**.

**Fix anti-duplicados 24h**: los workflows de n8n ejecutan `/api/alertas` cada 30 minutos. Sin el fix, la tabla `alertas` acumulaba registros idénticos en cada ejecución. La solución verifica que no exista ya una alerta del mismo `tipo` en las últimas 24 horas antes de insertar:

```python
# Lógica implementada en app.py (endpoint POST /api/alertas)
alerta_reciente = db.query(
    "SELECT id FROM alertas WHERE tipo = %s AND fecha > NOW() - INTERVAL '24 hours'",
    [tipo]
)
if not alerta_reciente:
    db.insert("INSERT INTO alertas (tipo, severidad, mensaje) VALUES (%s, %s, %s)", ...)
```

**KPIs monitoreados:**

| KPI | Umbral de alerta | Estado actual |
|---|---|---|
| Tasa de éxito | < 20% → alerta CRÍTICA | 9.1% ⚠️ alerta activa |
| Usuarios activos | < 30% en 7 días → alerta MEDIA | 18.81% ⚠️ alerta activa |
| Anomalías críticas | ≥ 5 → alerta ALTA | 0 ✅ |
| Score promedio | < 40% → alerta MEDIA | 54.41% ✅ |

---

## 🔄 Workflows n8n

Los 3 workflows corren de forma autónoma. Se comunican con la API usando el nombre de servicio interno Docker (`practicas_api:5000`), **no** `localhost:5000`.

### Workflow 1 — Monitor de KPIs
```
Schedule (30 min) → GET /api/kpis → IF tasa<20% OR anomalías≥5
                                        ├─ TRUE  → POST /api/alertas → BD
                                        └─ FALSE → Log "Sistema OK"
```

### Workflow 2 — Detección de Anomalías
```
Schedule (1 hora) → POST /api/detectar-anomalias → IF críticas > 0
                                                       ├─ TRUE  → Clasificar CRÍTICO/ALTO
                                                       └─ FALSE → Log "Sin críticas"
```

### Workflow 3 — Pipeline Nuevo Estudiante
```
Webhook POST (estudiante_id) → Validar ID → POST /api/calcular-matches
                                           → Extraer top 3 empresas
                                           → Responder JSON con resultados
```

---

## 🗄️ Base de Datos — 9 Tablas PostgreSQL

```sql
estudiantes           -- 101 registros — 10 carreras, 8 universidades limeñas
empresas              -- 50 registros  — 10 áreas de negocio, requisitos reales
matches               -- 779 registros — score promedio 54.41%, rango 20-95%
postulaciones         -- 200+ registros — 6 estados posibles
historial_aprendizaje -- 0 registros   — se puebla con resultados reales de producción
anomalias             -- 73 registros  — 3 ALTA, 16 MEDIA, 54 BAJA
metricas              -- 280 registros — historial de KPIs del MonitorAgent
alertas               -- 2 registros   — con validación anti-duplicados 24h
notificaciones        -- 0 registros   — diseñada para notificaciones futuras por email
```

### Consultas útiles

```sql
-- Distribución de matches por calidad
SELECT
  CASE
    WHEN score_final >= 80 THEN 'Excelente (80-100%)'
    WHEN score_final >= 60 THEN 'Bueno (60-79%)'
    WHEN score_final >= 40 THEN 'Regular (40-59%)'
    ELSE 'Bajo (<40%)'
  END AS calidad,
  COUNT(*) as cantidad
FROM matches GROUP BY calidad ORDER BY MIN(score_final) DESC;

-- Alertas activas
SELECT tipo, severidad, mensaje, fecha FROM alertas WHERE resuelta = false;

-- Anomalías por severidad
SELECT severidad, tipo, COUNT(*) FROM anomalias
GROUP BY severidad, tipo ORDER BY severidad;

-- Tasa de éxito real
SELECT COUNT(*) FILTER (WHERE estado = 'contratado') * 100.0 / COUNT(*) AS tasa_exito
FROM postulaciones;

-- Limpiar alertas duplicadas si las hay
DELETE FROM alertas WHERE id NOT IN (SELECT MIN(id) FROM alertas GROUP BY tipo);
```

---

## 🌐 Endpoints de la API

### Sistema
| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/api/kpis` | KPIs del sistema en tiempo real |
| GET/POST | `/api/alertas` | Consultar/generar alertas (anti-duplicados 24h) |

### Estudiantes y Empresas
| Método | Endpoint | Descripción |
|---|---|---|
| GET | `/api/estudiantes` | Listar estudiantes |
| GET | `/api/empresas` | Listar empresas |
| POST | `/api/registrar-estudiante` | Registrar estudiante con JSON |
| POST | `/api/subir-cv` | Subir CV PDF/DOCX → NLPAnalyzer extrae datos |

### Matching
| Método | Endpoint | Descripción |
|---|---|---|
| POST | `/api/calcular-matches` | Calcular matches para un estudiante |
| GET | `/api/matches/<estudiante_id>` | Ver matches con desglose por dimensión |
| POST | `/api/postular` | Registrar postulación a una empresa |

### Agentes
| Método | Endpoint | Descripción |
|---|---|---|
| POST | `/api/analizar-cv` | Ejecutar NLPAnalyzer sobre un CV |
| POST | `/api/detectar-anomalias` | Ejecutar AnomalyDetector |
| GET | `/api/anomalias` | Listar anomalías detectadas |
| GET | `/api/metricas/historico` | Historial de métricas del MonitorAgent |

---

## 🖥️ Interfaces Web

| URL | Descripción |
|---|---|
| `localhost:5000` | Landing page |
| `localhost:5000/dashboard.html` | KPIs en tiempo real, alertas activas, estadísticas globales |
| `localhost:5000/matches.html` | Motor de matching interactivo con desglose por dimensión |
| `localhost:5000/analisis-cv.html` | Análisis NLP de CVs con drag & drop |
| `localhost:5000/anomalias.html` | Visualización de anomalías por tipo y severidad |

---

## 🛠️ Comandos Útiles

```bash
# Ver estado de todos los contenedores
docker-compose ps

# Logs en tiempo real
docker-compose logs -f api
docker-compose logs -f postgres
docker-compose logs -f n8n

# Reiniciar la API después de cambiar app.py
docker-compose restart api

# Entrar a un contenedor
docker exec -it practicas_api bash
docker exec -it practicas_db psql -U admin -d practicas_db

# Ver consumo de recursos
docker stats

# Detener todo (conserva la base de datos)
docker-compose down

# Detener y BORRAR todos los datos
docker-compose down -v

# Reconstruir imagen tras cambiar requirements.txt o Dockerfile
docker-compose build --no-cache api
docker-compose up -d
```

---

## 🐛 Solución de Problemas

**"Cannot connect to database"**
```bash
docker-compose ps postgres
docker-compose restart postgres
docker-compose logs postgres
```

**"Port already in use"**
```bash
netstat -ano | findstr :5000   # Windows
lsof -i :5000                  # Linux / Mac
```

**Las alertas se duplican en la tabla**

El fix anti-duplicados está en `app.py` endpoint `/api/alertas`. Si ya hay duplicados:
```sql
DELETE FROM alertas WHERE id NOT IN (SELECT MIN(id) FROM alertas GROUP BY tipo);
```

**n8n no puede conectar con la API**

Verificar que la URL en los workflows sea `http://practicas_api:5000` (nombre de servicio interno Docker), **no** `http://localhost:5000`.

**El NLPAnalyzer no detecta habilidades**

El CV debe estar en PDF o DOCX de texto, no una imagen escaneada. CVs escaneados requieren OCR — no soportado en esta versión.

**Reconstruir desde cero**
```bash
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
python data/generar_dataset.py
python data/cargar_dataset.py
```

---

## 📊 Métricas del Sistema (Dataset Actual)

| Métrica | Valor |
|---|---|
| Estudiantes registrados | 101 |
| Empresas activas | 50 |
| Matches calculados | 779 |
| Score promedio | 54.41% |
| Tasa de éxito | 9.1% ⚠️ (esperado con dataset sintético sin retroalimentación real) |
| Anomalías detectadas | 73 (3 alta · 16 media · 54 baja) |
| Alertas persistidas en BD | 2 |
| Registros de métricas históricas | 280 |
| Workflows n8n activos | 3 |

---

## 📚 Stack Tecnológico

| Tecnología | Versión | Uso |
|---|---|---|
| Python | 3.10 | Lenguaje principal — agentes y API |
| Flask | 2.x | Framework API REST |
| spaCy | 3.x | NLP — Named Entity Recognition |
| scikit-learn | 1.x | TF-IDF + similitud coseno |
| psycopg2 | 2.9 | Conector Python → PostgreSQL |
| PyPDF2 | latest | Lectura de CVs en PDF |
| python-docx | latest | Lectura de CVs en DOCX |
| PostgreSQL | 15 | Base de datos relacional — 9 tablas |
| n8n | latest | Orquestador de workflows automáticos |
| Docker Compose | 3.8 | Orquestación de 4 contenedores |
| pgAdmin 4 | latest | Administración visual de PostgreSQL |

---

## 👥 Equipo

Proyecto Final — Sistemas Inteligentes 2026

- [Integrante 1]
- [Integrante 2]
- [Integrante 3]
- [Integrante 4]
- [Integrante 5]

---

## 📄 Licencia

Proyecto académico — Universidad — 2026