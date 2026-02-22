# API Endpoints - Sistema de Prácticas Preprofesionales

## 📚 Documentación Completa de Endpoints

### Base URL
```
http://localhost:5000
```

---

## 🏥 HEALTH CHECK

### GET /health
Verifica que la API esté funcionando y conectada a la BD.

**Request:**
```bash
curl http://localhost:5000/health
```

**Response:**
```json
{
  "status": "ok",
  "message": "API funcionando correctamente",
  "database": "conectado"
}
```

---

## 👥 ESTUDIANTES

### GET /api/estudiantes
Lista todos los estudiantes (últimos 10).

**Request:**
```bash
curl http://localhost:5000/api/estudiantes
```

**Response:**
```json
{
  "success": true,
  "total": 10,
  "estudiantes": [
    {
      "id": 1,
      "nombre": "Juan Pérez",
      "email": "juan@email.com",
      "carrera": "Ing. Sistemas",
      "universidad": "PUCP",
      "habilidades": ["python", "react", "sql"],
      "completitud": 85
    }
  ]
}
```

### POST /api/registrar-estudiante
Registra un nuevo estudiante.

**Request:**
```bash
curl -X POST http://localhost:5000/api/registrar-estudiante \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "María García",
    "email": "maria@email.com",
    "carrera": "Ing. Sistemas",
    "universidad": "UNI",
    "habilidades": ["python", "java", "sql"]
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Estudiante registrado correctamente",
  "estudiante_id": 5
}
```

---

## 🏢 EMPRESAS

### GET /api/empresas
Lista todas las empresas activas.

**Request:**
```bash
curl http://localhost:5000/api/empresas
```

**Response:**
```json
{
  "success": true,
  "total": 3,
  "empresas": [
    {
      "id": 1,
      "nombre": "TechStartup SAC",
      "area": "Desarrollo Software",
      "requisitos": ["python", "react", "sql"],
      "salario": 1200,
      "modalidad": "hibrido"
    }
  ]
}
```

---

## 🎯 AGENTE 1: MATCHING ENGINE

### POST /api/calcular-matches
Calcula matches para un estudiante con todas las empresas activas.

**Request:**
```bash
curl -X POST http://localhost:5000/api/calcular-matches \
  -H "Content-Type: application/json" \
  -d '{"estudiante_id": 1}'
```

**Response:**
```json
{
  "success": true,
  "num_matches": 3,
  "matches": [
    {
      "empresa_id": 1,
      "empresa_nombre": "TechStartup SAC",
      "empresa_area": "Desarrollo Software",
      "score_final": 85.5,
      "score_estudiante_empresa": 88.0,
      "score_empresa_estudiante": 82.0,
      "desglose": {
        "habilidades": 90.0,
        "experiencia": 75.0,
        "carrera": 100.0,
        "ubicacion": 50.0,
        "disponibilidad": 100.0
      },
      "insight": "¡Excelente match! Cumples perfectamente los requisitos...",
      "recomendacion": "ALTA - Postula inmediatamente"
    }
  ]
}
```

---

## 📄 AGENTE 2: NLP ANALYZER

### POST /api/analizar-cv
Analiza un CV y extrae información estructurada.

**Request:**
```bash
curl -X POST http://localhost:5000/api/analizar-cv \
  -H "Content-Type: application/json" \
  -d '{
    "texto_cv": "Juan Pérez. Estudiante de Ing. Sistemas PUCP. Experiencia: 2020-2023 en Python y React. Email: juan@email.com. Tel: 987654321"
  }'
```

**Response:**
```json
{
  "success": true,
  "resultado": {
    "habilidades": ["python", "react"],
    "email": "juan@email.com",
    "telefono": "987654321",
    "meses_experiencia": 36,
    "nivel_ingles": "No especificado",
    "universidad": "PUCP",
    "calidad_cv": 75,
    "completitud": 80,
    "recomendaciones": [
      "✅ Tu perfil está completo"
    ]
  }
}
```

---

## 🧠 AGENTE 3: LEARNING SYSTEM

### POST /api/predecir-exito
Predice la probabilidad de éxito de un match.

**Request:**
```bash
curl -X POST http://localhost:5000/api/predecir-exito \
  -H "Content-Type: application/json" \
  -d '{
    "estudiante": {
      "carrera": "Ing. Sistemas",
      "universidad": "PUCP",
      "habilidades": ["python", "react"],
      "meses_experiencia": 12
    },
    "empresa": {
      "area": "Desarrollo Software"
    }
  }'
```

**Response:**
```json
{
  "success": true,
  "probabilidad_exito": 75.5,
  "mensaje": "Probabilidad de éxito: 75.5%"
}
```

### POST /api/registrar-resultado
Registra el resultado de un match para que el sistema aprenda.

**Request:**
```bash
curl -X POST http://localhost:5000/api/registrar-resultado \
  -H "Content-Type: application/json" \
  -d '{
    "match_id": 15,
    "resultado": "contratado"
  }'
```

**Valores válidos para resultado:**
- `contratado` - El estudiante fue contratado
- `rechazado` - El estudiante fue rechazado
- `entrevista` - Llegó a entrevista pero no fue contratado
- `sin_respuesta` - La empresa no respondió

**Response:**
```json
{
  "success": true,
  "mensaje": "Resultado 'contratado' registrado exitosamente para el aprendizaje del sistema"
}
```

### GET /api/insights-area/{area}
Obtiene insights de aprendizaje para un área específica.

**Request:**
```bash
curl "http://localhost:5000/api/insights-area/Desarrollo%20Software"
```

**Response:**
```json
{
  "success": true,
  "insights": {
    "disponible": true,
    "area": "Desarrollo Software",
    "n_casos_exitosos": 12,
    "experiencia_promedio_meses": 14.5,
    "universidades_top": ["PUCP", "UNI", "ULIMA"],
    "promedio_academico_esperado": 15.8,
    "habilidades_mas_valoradas": {
      "python": 10,
      "react": 8,
      "sql": 7
    },
    "recomendacion": "Esta área valora la experiencia (promedio 15 meses) | Habilidad más valorada: python"
  }
}
```

### GET /api/recomendaciones/{estudiante_id}?area={area}
Obtiene recomendaciones para mejorar el perfil de un estudiante.

**Request:**
```bash
curl "http://localhost:5000/api/recomendaciones/1?area=Desarrollo%20Software"
```

**Response:**
```json
{
  "success": true,
  "estudiante_id": 1,
  "area_objetivo": "Desarrollo Software",
  "recomendaciones": [
    "💼 Adquiere 6 meses más de experiencia (promedio exitoso: 15 meses)",
    "🎯 Aprende estas habilidades valoradas: docker, kubernetes, aws"
  ]
}
```

### GET /api/aprendizaje/estadisticas
Obtiene estadísticas generales del sistema de aprendizaje.

**Request:**
```bash
curl http://localhost:5000/api/aprendizaje/estadisticas
```

**Response:**
```json
{
  "success": true,
  "estadisticas": {
    "total_registros": 45,
    "contratados": 12,
    "tasa_exito_global": 26.67,
    "areas_con_aprendizaje": 3,
    "total_patrones_exitosos": 12,
    "distribucion_resultados": {
      "contratado": 12,
      "rechazado": 20,
      "entrevista": 8,
      "sin_respuesta": 5
    }
  }
}
```

---

## 🚨 AGENTE 4: ANOMALY DETECTOR

### POST /api/detectar-anomalias
Ejecuta detección de anomalías en todo el sistema.

**Request:**
```bash
curl -X POST http://localhost:5000/api/detectar-anomalias
```

**Response:**
```json
{
  "success": true,
  "total_anomalias": 5,
  "por_severidad": {
    "criticas": 0,
    "altas": 1,
    "medias": 2,
    "bajas": 2
  },
  "anomalias": [
    {
      "tipo": "empresa_inactiva",
      "entidad_tipo": "empresa",
      "entidad_id": 5,
      "severidad": "alta",
      "descripcion": "Empresa 'Marketing Digital Corp' tiene 15 postulaciones pero solo 6.7% de tasa de respuesta",
      "recomendacion": "Contactar a la empresa o desactivarla temporalmente"
    }
  ],
  "mensaje": "Se detectaron 5 anomalías en el sistema"
}
```

### GET /api/anomalias/resumen?dias={dias}
Obtiene resumen de anomalías de los últimos N días.

**Request:**
```bash
curl "http://localhost:5000/api/anomalias/resumen?dias=7"
```

**Response:**
```json
{
  "success": true,
  "dias": 7,
  "resumen": [
    {
      "tipo": "empresa_inactiva",
      "severidad": "alta",
      "total": 2,
      "ultima_deteccion": "2026-02-19T10:30:00"
    }
  ]
}
```

### POST /api/anomalias/{anomalia_id}/resolver
Marca una anomalía como resuelta.

**Request:**
```bash
curl -X POST http://localhost:5000/api/anomalias/3/resolver
```

**Response:**
```json
{
  "success": true,
  "mensaje": "Anomalía 3 marcada como resuelta"
}
```

---

## 📊 AGENTE 5: MONITOR AGENT

### GET /api/kpis
Obtiene todos los KPIs del sistema.

**Request:**
```bash
curl http://localhost:5000/api/kpis
```

**Response:**
```json
{
  "success": true,
  "kpis": {
    "estudiantes": {
      "total": 50,
      "activos_7d": 23,
      "tasa_actividad": 46.0,
      "completitud_promedio": 78.5,
      "top_carreras": [
        {"carrera": "Ing. Sistemas", "total": 20},
        {"carrera": "Marketing", "total": 12}
      ]
    },
    "empresas": {
      "total_activas": 30,
      "por_area": [
        {"area": "Desarrollo Software", "total": 10},
        {"area": "Marketing", "total": 8}
      ]
    },
    "matches": {
      "total": 1500,
      "ultimos_7d": 230,
      "score_promedio": 68.5,
      "distribucion_scores": [
        {"rango": "Excelente (80-100)", "total": 450},
        {"rango": "Bueno (60-79)", "total": 680}
      ]
    },
    "postulaciones": {
      "total": 425,
      "tasa_respuesta": 65.2,
      "tiempo_respuesta_dias": 7.3,
      "contratados": 45,
      "tasa_exito": 10.6
    },
    "tendencias": {
      "postulaciones": {
        "ultimos_7d": 85,
        "anteriores_7d": 72,
        "cambio_porcentual": 18.06,
        "tendencia": "subida"
      }
    },
    "fecha_calculo": "2026-02-19T15:30:00"
  }
}
```

### GET /api/alertas
Genera alertas basadas en los KPIs actuales.

**Request:**
```bash
curl http://localhost:5000/api/alertas
```

**Response:**
```json
{
  "success": true,
  "total_alertas": 2,
  "alertas": [
    {
      "nivel": "critico",
      "tipo": "tasa_exito_baja",
      "mensaje": "Tasa de éxito muy baja: 8.5%",
      "recomendacion": "Revisar algoritmo de matching o estrategia de recomendaciones"
    },
    {
      "nivel": "warning",
      "tipo": "respuesta_lenta",
      "mensaje": "Empresas tardan 15.2 días en responder",
      "recomendacion": "Enviar recordatorios automáticos a empresas"
    }
  ]
}
```

### GET /api/metricas/historico?dias={dias}
Obtiene histórico de métricas para gráficos.

**Request:**
```bash
curl "http://localhost:5000/api/metricas/historico?dias=30"
```

**Response:**
```json
{
  "success": true,
  "dias": 30,
  "historico": [
    {
      "fecha": "2026-01-20",
      "total_estudiantes": 45,
      "estudiantes_activos": 20,
      "total_matches": 1200,
      "tasa_exito": 9.5
    }
  ]
}
```

---

## 📋 RESUMEN DE ENDPOINTS

### Total: 19 Endpoints

**Health & Básicos (4):**
- ✅ GET  /health
- ✅ GET  /api/estudiantes
- ✅ POST /api/registrar-estudiante
- ✅ GET  /api/empresas

**Agente 1 - Matching (1):**
- ✅ POST /api/calcular-matches

**Agente 2 - NLP (1):**
- ✅ POST /api/analizar-cv

**Agente 3 - Learning (5):**
- ✅ POST /api/predecir-exito
- ✅ POST /api/registrar-resultado
- ✅ GET  /api/insights-area/{area}
- ✅ GET  /api/recomendaciones/{estudiante_id}
- ✅ GET  /api/aprendizaje/estadisticas

**Agente 4 - Anomaly (3):**
- ✅ POST /api/detectar-anomalias
- ✅ GET  /api/anomalias/resumen
- ✅ POST /api/anomalias/{anomalia_id}/resolver

**Agente 5 - Monitor (3):**
- ✅ GET  /api/kpis
- ✅ GET  /api/alertas
- ✅ GET  /api/metricas/historico

---

## 🧪 PRUEBAS RÁPIDAS

### Test básico (verificar que funciona):
```bash
curl http://localhost:5000/health
curl http://localhost:5000/api/empresas
curl http://localhost:5000/api/kpis
```

### Test completo de un flujo:
```bash
# 1. Registrar estudiante
curl -X POST http://localhost:5000/api/registrar-estudiante \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Test User",
    "email": "test@email.com",
    "carrera": "Ing. Sistemas",
    "universidad": "PUCP",
    "habilidades": ["python", "react"]
  }'

# 2. Calcular matches (usar el ID retornado)
curl -X POST http://localhost:5000/api/calcular-matches \
  -H "Content-Type: application/json" \
  -d '{"estudiante_id": 1}'

# 3. Ver KPIs
curl http://localhost:5000/api/kpis
```

---

## 🐛 CÓDIGOS DE ERROR

- **200** - Éxito
- **400** - Bad Request (parámetros faltantes o inválidos)
- **404** - Not Found (recurso no encontrado)
- **500** - Internal Server Error (error del servidor)

Todos los errores retornan:
```json
{
  "success": false,
  "error": "Descripción del error"
}
```
