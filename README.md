# 🎯 PractiMatch

### Sistema Inteligente de Matching Bidireccional para Prácticas Preprofesionales

> Conecta automáticamente a estudiantes universitarios con empresas compatibles usando 5 agentes de inteligencia artificial, análisis NLP de CVs y flujos de automatización autónomos.

---

## ⚡ Inicio Rápido

```bash
# 1. Levantar los 4 contenedores
docker-compose up -d

# 2. Generar y cargar el dataset
python data/generar_dataset.py
python data/cargar_dataset.py

# 3. Abrir el sistema
#   🌐 Web      →  http://localhost:5000
#   ⚙️  n8n      →  http://localhost:5678   (admin / admin123)
#   🗄️  pgAdmin  →  http://localhost:5050   (admin@admin.com / admin)
```

**Requisito único:** Docker Desktop instalado y en ejecución.

---

## 🖥️ Interfaces del Sistema

| Página | URL | Descripción |
|---|---|---|
| 🏠 Landing | `localhost:5000` | Presentación del sistema |
| 📊 Dashboard | `localhost:5000/dashboard.html` | KPIs en tiempo real y alertas activas |
| 🔗 Matches | `localhost:5000/matches.html` | Motor de matching interactivo |
| 📄 Análisis CV | `localhost:5000/analisis-cv.html` | Extracción automática de CVs (drag & drop) |
| ⚠️ Anomalías | `localhost:5000/anomalias.html` | Detección y visualización de anomalías |

---

## 🤖 Los 5 Agentes IA

| # | Agente | Tecnología | Función |
|---|---|---|---|
| 1 | **MatchingEngine** | TF-IDF + similitud coseno | Calcula compatibilidad bidireccional en 5 dimensiones |
| 2 | **NLPAnalyzer** | spaCy + regex | Extrae datos de CVs en PDF y DOCX automáticamente |
| 3 | **LearningSystem** | Pesos adaptativos | Ajusta el algoritmo según resultados reales por área |
| 4 | **AnomalyDetector** | Z-score estadístico | Detecta comportamientos anómalos en estudiantes y empresas |
| 5 | **MonitorAgent** | KPIs + alertas | Supervisa el sistema y genera alertas automáticas 24/7 |

El **MatchingEngine** evalúa compatibilidad en dos direcciones: ¿el estudiante cumple a la empresa? y ¿la empresa es adecuada para el estudiante? El score final combina ambas perspectivas (60% / 40%).

---

## 🔄 Automatización con n8n

Tres workflows corren de forma autónoma sin intervención humana:

- **Monitor de KPIs** — revisa indicadores del sistema y persiste alertas en PostgreSQL si algún KPI baja de umbral crítico
- **Detección de Anomalías** — ejecuta el AnomalyDetector y clasifica anomalías por severidad (ALTA / MEDIA / BAJA)
- **Pipeline Nuevo Estudiante** — se activa vía webhook al registrar un estudiante y calcula sus matches automáticamente

> Los workflows se conectan a la API usando el nombre de servicio interno Docker (`practicas_api:5000`), no `localhost`.

---

## 📁 Estructura del Proyecto

```
proyecto-practicas/
├── docker-compose.yml
├── api/
│   ├── app.py                      # API Flask — 20+ endpoints
│   ├── Dockerfile
│   ├── requirements.txt
│   └── agentes/
│       ├── matching_engine.py
│       ├── nlp_analyzer.py
│       ├── learning_system.py
│       ├── anomaly_detector.py
│       └── monitor_agent.py
├── frontend/
│   ├── index.html
│   ├── dashboard.html
│   ├── matches.html
│   ├── analisis-cv.html
│   └── anomalias.html
├── database/
│   └── init.sql                    # 9 tablas PostgreSQL
├── n8n/
│   └── workflows/                  # 3 workflows exportados en JSON
└── data/
    ├── generar_dataset.py          # Genera el dataset sintético
    └── cargar_dataset.py           # Carga datos y calcula matches
```

---

## 📊 Métricas del Dataset

| Indicador | Valor |
|---|---|
| 👨‍🎓 Estudiantes | 101 |
| 🏢 Empresas | 50 |
| 🔗 Matches calculados | 779 |
| 📈 Score promedio | 54.41% |
| ⚠️ Anomalías detectadas | 73 |
| 🔔 Alertas activas en BD | 2 |
| ⚙️ Workflows n8n activos | 3 |

---

## 🛠️ Comandos Útiles

```bash
docker-compose ps                        # Ver estado de los contenedores
docker-compose logs -f api               # Ver logs de la API en tiempo real
docker-compose restart api               # Reiniciar la API tras cambios en app.py
docker-compose down                      # Detener (conserva la base de datos)
docker-compose down -v                   # Detener y borrar todos los datos
docker-compose build --no-cache api      # Reconstruir la imagen de la API
```

---

## 🐛 Problemas Frecuentes

**No conecta a la base de datos**
```bash
docker-compose restart postgres
docker-compose logs postgres
```

**Puerto en uso**
```bash
netstat -ano | findstr :5000   # Windows
lsof -i :5000                  # Linux / Mac
```

**Reconstruir desde cero**
```bash
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
python data/generar_dataset.py
python data/cargar_dataset.py
```

---

## 🧰 Tecnologías

`Python 3.10` · `Flask` · `spaCy` · `scikit-learn` · `PostgreSQL 15` · `n8n` · `Docker Compose` · `pgAdmin 4` · `PyPDF2` · `python-docx`

---

## 👥 Equipo

Proyecto Final — Sistemas Inteligentes 2026

- [Integrante 1]
- [Integrante 2]
- [Integrante 3]
- [Integrante 4]
- [Integrante 5]