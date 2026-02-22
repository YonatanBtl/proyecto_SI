# Dataset Ficticio - Sistema de Prácticas

Este directorio contiene scripts para generar y cargar datos ficticios al sistema.

## 📁 Archivos

- `generar_dataset.py` - Genera 50 estudiantes y 30 empresas ficticias
- `cargar_dataset.py` - Carga los datos a PostgreSQL
- `estudiantes.csv` - 50 estudiantes (generado)
- `empresas.csv` - 30 empresas (generado)

## 🚀 Uso Rápido

### 1. Generar los CSV

```bash
cd data
python generar_dataset.py
```

Esto crea:
- ✅ `estudiantes.csv` con 50 estudiantes
- ✅ `empresas.csv` con 30 empresas

### 2. Cargar a PostgreSQL

```bash
python cargar_dataset.py
```

El script preguntará si deseas limpiar las tablas primero.

## 📊 Datos Generados

### Estudiantes (50)

**Campos:**
- Nombre completo (ficticio)
- Email único
- Teléfono
- Carrera (12 opciones)
- Universidad (10 opciones)
- Promedio (12-18)
- Semestre (5-10)
- Habilidades (3-8 por estudiante)
- Experiencia (0-36 meses)
- Nivel de inglés
- Proyectos
- Ubicación en Lima
- Horas disponibles
- Calidad CV
- Completitud

**Distribución aproximada:**
- 40% Ing. Sistemas/Software
- 20% Marketing/Comunicaciones
- 15% Administración/Economía
- 10% Diseño
- 15% Otras carreras

### Empresas (30)

**Áreas cubiertas:**
- Desarrollo Software (7)
- Data Science (3)
- Marketing (5)
- Diseño (3)
- Finanzas (3)
- Consultoría (2)
- Recursos Humanos (2)
- Retail/E-commerce (2)
- Logística (2)
- EdTech/HealthTech (3)

**Campos:**
- Nombre de empresa
- Área
- Descripción
- Requisitos (2-5 habilidades)
- Carreras aceptadas
- Experiencia mínima (0-18 meses)
- Horas requeridas (20-35 hrs/semana)
- Salario (S/800-2000)
- Ubicación en Lima
- Modalidad (presencial/remoto/híbrido)
- Fecha límite

## 🎲 Datos Realistas

Los datos son completamente ficticios pero realistas:

- ✅ Nombres y apellidos comunes en Perú
- ✅ Emails únicos generados automáticamente
- ✅ Distribución de habilidades según carrera
- ✅ Salarios ajustados por área
- ✅ Ubicaciones reales en Lima con coordenadas
- ✅ Requisitos coherentes por tipo de empresa

## 🔧 Configuración

Por defecto se conecta a:
```
postgresql://admin:admin123@localhost:5432/practicas_db
```

Para cambiar, define la variable de entorno:
```bash
export DATABASE_URL="postgresql://user:pass@host:port/dbname"
```

## ⚠️ Importante

- Los datos son **100% ficticios**
- No usar en producción
- Perfecto para demos y desarrollo
- Se pueden regenerar cuantas veces quieras

## 🧪 Verificación

Después de cargar, verifica:

```bash
# Ver empresas
curl http://localhost:5000/api/empresas

# Ver estudiantes
curl http://localhost:5000/api/estudiantes

# Ver KPIs
curl http://localhost:5000/api/kpis
```

## 📝 Personalización

Para cambiar la cantidad:

```python
# En generar_dataset.py
NUM_ESTUDIANTES = 100  # Cambiar a lo que necesites
NUM_EMPRESAS = 50
```

Luego regenera:
```bash
python generar_dataset.py
python cargar_dataset.py
```
