# Sistema de Gestión de Prácticas Preprofesionales

Sistema multi-agente inteligente para matching automático entre estudiantes y empresas.

## 🚀 Inicio Rápido

### Prerrequisitos

- Docker Desktop instalado
- 8GB RAM mínimo
- Windows 11 / Linux / macOS

### Instalación

1. **Clonar/Descargar el proyecto**

2. **Levantar los servicios**

```bash
docker-compose up -d
```

Esto levantará:
- PostgreSQL (puerto 5432)
- n8n (puerto 5678)
- API Python (puerto 5000)

3. **Verificar que todo funciona**

```bash
# Verificar servicios corriendo
docker-compose ps

# Ver logs
docker-compose logs -f api
```

4. **Probar la API**

Abrir en navegador: http://localhost:5000/health

Deberías ver:
```json
{
  "status": "ok",
  "message": "API funcionando correctamente",
  "database": "conectado"
}
```

5. **Acceder a n8n**

Abrir: http://localhost:5678
- Usuario: admin
- Contraseña: admin123

## 📊 Estructura del Proyecto

```
proyecto-practicas/
├── docker-compose.yml          # Configuración de servicios
├── api/                        # API Python (Flask)
│   ├── app.py                  # Servidor principal
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── agentes/               # Agentes inteligentes (próximamente)
│   └── utils/                 # Utilidades
├── database/
│   └── init.sql               # Script de inicialización BD
├── n8n/
│   └── workflows/             # Flujos n8n exportados
├── frontend/                  # Dashboard React (próximamente)
└── data/                      # Datasets
```

## 🧪 Probar Endpoints

### Listar empresas
```bash
curl http://localhost:5000/api/empresas
```

### Registrar estudiante
```bash
curl -X POST http://localhost:5000/api/registrar-estudiante \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Juan Pérez",
    "email": "juan@example.com",
    "carrera": "Ing. Sistemas",
    "universidad": "PUCP",
    "habilidades": ["python", "react", "sql"]
  }'
```

### Calcular matches
```bash
curl -X POST http://localhost:5000/api/calcular-matches \
  -H "Content-Type: application/json" \
  -d '{"estudiante_id": 1}'
```

## 🛠️ Comandos Útiles

### Ver logs de un servicio
```bash
docker-compose logs -f api
docker-compose logs -f postgres
docker-compose logs -f n8n
```

### Reiniciar un servicio
```bash
docker-compose restart api
```

### Detener todo
```bash
docker-compose down
```

### Detener y borrar datos (CUIDADO)
```bash
docker-compose down -v
```

### Entrar a un contenedor
```bash
docker exec -it practicas_api bash
docker exec -it practicas_db psql -U admin -d practicas_db
```

### Ver consumo de recursos
```bash
docker stats
```

## 🐛 Solución de Problemas

### Error: "Cannot connect to database"
```bash
# Verificar que PostgreSQL esté corriendo
docker-compose ps postgres

# Reiniciar PostgreSQL
docker-compose restart postgres
```

### Error: "Port already in use"
```bash
# Ver qué está usando el puerto
netstat -ano | findstr :5000  # Windows
lsof -i :5000  # Linux/Mac

# Cambiar puerto en docker-compose.yml si es necesario
```

### Reconstruir contenedores
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## 📝 Próximos Pasos

1. ✅ Sistema base funcionando
2. ⏳ Implementar Agente 1 (Matching avanzado)
3. ⏳ Implementar Agente 2 (NLP)
4. ⏳ Implementar Agente 3 (Learning)
5. ⏳ Implementar Agente 4 (Anomalías)
6. ⏳ Implementar Agente 5 (Monitor)
7. ⏳ Dashboard React
8. ⏳ Workflows n8n completos

## 📚 Documentación

- [Flask](https://flask.palletsprojects.com/)
- [PostgreSQL](https://www.postgresql.org/docs/)
- [n8n](https://docs.n8n.io/)
- [Docker](https://docs.docker.com/)

## 👥 Equipo

Proyecto de Sistemas Inteligentes 2026

## 📄 Licencia

Proyecto académico - Universidad
