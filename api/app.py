"""
Sistema de Gestión de Prácticas Preprofesionales
API Flask - Servidor Principal

Versión Profesional: Agentes en archivos separados
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import json
import tempfile

# Importar agentes
from agentes.matching_engine import MatchingEngine
from agentes.nlp_analyzer import NLPAnalyzer
from agentes.learning_system import LearningSystem
from agentes.anomaly_detector import AnomalyDetector
from agentes.monitor_agent import MonitorAgent

app = Flask(__name__)
CORS(app)  # Permitir peticiones desde n8n y frontend

# Configuración de base de datos
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://admin:admin123@postgres:5432/practicas_db')

# Instanciar agentes
matching_engine = MatchingEngine()
nlp_analyzer = NLPAnalyzer()
learning_system = LearningSystem()
anomaly_detector = AnomalyDetector()
monitor_agent = MonitorAgent()

def get_db_connection():
    """Obtiene conexión a PostgreSQL"""
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return conn
    except Exception as e:
        print(f"❌ Error conectando a BD: {e}")
        return None

# ============================================
# ENDPOINT DE SALUD
# ============================================

@app.route('/health', methods=['GET'])
def health():
    """Verifica que la API esté funcionando"""
    try:
        conn = get_db_connection()
        if conn:
            conn.close()
            return jsonify({
                'status': 'ok',
                'message': 'API funcionando correctamente',
                'database': 'conectado'
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'No se pudo conectar a la base de datos'
            }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# ============================================
# ENDPOINTS BÁSICOS (versión simple)
# ============================================

@app.route('/api/estudiantes', methods=['GET'])
def listar_estudiantes():
    """Lista todos los estudiantes"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM estudiantes ORDER BY fecha_registro DESC LIMIT 10")
        estudiantes = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'total': len(estudiantes),
            'estudiantes': estudiantes
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/empresas', methods=['GET'])
def listar_empresas():
    """Lista todas las empresas activas"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM empresas WHERE activa = TRUE")
        empresas = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'total': len(empresas),
            'empresas': empresas
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/registrar-estudiante', methods=['POST'])
def registrar_estudiante():
    """Registra un nuevo estudiante (versión básica)"""
    try:
        data = request.json
        
        # Validaciones básicas
        if not data.get('nombre') or not data.get('email'):
            return jsonify({
                'success': False,
                'error': 'Nombre y email son requeridos'
            }), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Insertar estudiante
        cursor.execute("""
            INSERT INTO estudiantes (nombre, email, carrera, universidad, habilidades)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (
            data.get('nombre'),
            data.get('email'),
            data.get('carrera', 'No especificado'),
            data.get('universidad', 'No especificado'),
            data.get('habilidades', [])
        ))
        
        estudiante_id = cursor.fetchone()['id']
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Estudiante registrado correctamente',
            'estudiante_id': estudiante_id
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================
# ENDPOINT: Agente NLP - Subir PDF
# ============================================

@app.route('/api/subir-cv', methods=['POST'])
def subir_cv():
    """
    Recibe un archivo PDF o DOCX, extrae el texto con el Agente NLP
    y opcionalmente registra al estudiante en la BD.

    Form-data:
        archivo  : archivo PDF o DOCX (requerido)
        registrar: 'true' para guardar en BD (opcional)
    """
    try:
        # Verificar que se envió un archivo
        if 'archivo' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No se envió ningún archivo. Usa el campo "archivo" en form-data.'
            }), 400

        archivo = request.files['archivo']

        if archivo.filename == '':
            return jsonify({'success': False, 'error': 'El archivo no tiene nombre'}), 400

        # Validar extensión
        extension = archivo.filename.rsplit('.', 1)[-1].lower()
        if extension not in ['pdf', 'docx']:
            return jsonify({
                'success': False,
                'error': 'Solo se aceptan archivos PDF o DOCX'
            }), 400

        # Guardar temporalmente y analizar
        with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{extension}') as tmp:
            archivo.save(tmp.name)
            resultado = nlp_analyzer.analizar_cv_desde_archivo(tmp.name)
            os.unlink(tmp.name)  # Borrar archivo temporal

        if 'error' in resultado:
            return jsonify({'success': False, 'error': resultado['error']}), 422

        # Si se pide registrar, guardar en BD automáticamente
        registrar = request.form.get('registrar', 'false').lower() == 'true'
        estudiante_id = None

        if registrar:
            conn = get_db_connection()
            if conn:
                cursor = conn.cursor()
                try:
                    cursor.execute("""
                        INSERT INTO estudiantes (nombre, email, carrera, universidad, habilidades)
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (email) DO NOTHING
                        RETURNING id
                    """, (
                        resultado.get('nombre', 'No detectado'),
                        resultado.get('email', ''),
                        'No especificado',
                        resultado.get('universidad', 'Otra'),
                        resultado.get('habilidades', [])
                    ))
                    row = cursor.fetchone()
                    estudiante_id = row['id'] if row else None
                    conn.commit()
                except Exception as db_err:
                    print(f"⚠️ Error guardando estudiante: {db_err}")
                finally:
                    cursor.close()
                    conn.close()

        return jsonify({
            'success': True,
            'archivo': archivo.filename,
            'resultado': resultado,
            'estudiante_registrado': registrar,
            'estudiante_id': estudiante_id
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================
# ENDPOINT: Agente NLP - Texto plano
# ============================================

@app.route('/api/analizar-cv', methods=['POST'])
def analizar_cv():
    """
    Analiza un CV en texto plano usando el Agente NLP.
    Útil para pruebas rápidas sin subir archivo.
    """
    try:
        data = request.json
        texto_cv = data.get('texto_cv', '')

        if not texto_cv:
            return jsonify({
                'success': False,
                'error': 'texto_cv es requerido'
            }), 400

        # Delegar al Agente 2: NLP Analyzer
        resultado = nlp_analyzer.analizar_cv_completo(texto_cv)

        return jsonify({
            'success': True,
            'resultado': resultado
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================
# ENDPOINT: Agente Matching (versión SIMPLE)
# ============================================

@app.route('/api/calcular-matches', methods=['POST'])
def calcular_matches():
    """
    Calcula matches para un estudiante usando el Agente de Matching
    """
    try:
        data = request.json
        estudiante_id = data.get('estudiante_id')
        
        if not estudiante_id:
            return jsonify({
                'success': False,
                'error': 'estudiante_id es requerido'
            }), 400
        
        conn = get_db_connection()
        
        # Delegar al Agente 1: Matching Engine
        matches = matching_engine.calcular_matches_para_estudiante(estudiante_id, conn)
        
        # Guardar matches en BD
        cursor = conn.cursor()
        for match in matches:
            cursor.execute("""
                INSERT INTO matches (
                    estudiante_id, empresa_id, score_final, 
                    score_requisitos, score_atractivo, desglose
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (estudiante_id, empresa_id) 
                DO UPDATE SET 
                    score_final = EXCLUDED.score_final,
                    score_requisitos = EXCLUDED.score_requisitos,
                    score_atractivo = EXCLUDED.score_atractivo,
                    desglose = EXCLUDED.desglose,
                    fecha_actualizacion = NOW()
            """, (
                estudiante_id,
                match['empresa_id'],
                match['score_final'],
                match['score_estudiante_empresa'],
                match['score_empresa_estudiante'],
                json.dumps(match['desglose'])
            ))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'num_matches': len(matches),
            'matches': matches[:5]  # Top 5
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================
# ENDPOINT: KPIs Básicos
# ============================================

@app.route('/api/kpis', methods=['GET'])
def obtener_kpis():
    """Obtiene KPIs completos usando el Agente Monitor"""
    try:
        conn = get_db_connection()
        
        # Delegar al Agente 5: Monitor Agent
        kpis = monitor_agent.calcular_kpis_completos(conn)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'kpis': kpis
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================
# ENDPOINT: Predecir Éxito (Agente Learning)
# ============================================

@app.route('/api/predecir-exito', methods=['POST'])
def predecir_exito():
    """
    Predice la probabilidad de éxito de un match usando el Agente Learning
    """
    try:
        data = request.json
        estudiante = data.get('estudiante')
        empresa = data.get('empresa')
        
        if not estudiante or not empresa:
            return jsonify({
                'success': False,
                'error': 'estudiante y empresa son requeridos'
            }), 400
        
        # Delegar al Agente 3: Learning System
        probabilidad = learning_system.predecir_probabilidad_exito(estudiante, empresa)
        
        return jsonify({
            'success': True,
            'probabilidad_exito': probabilidad,
            'mensaje': f"Probabilidad de éxito: {probabilidad}%"
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/registrar-resultado', methods=['POST'])
def registrar_resultado():
    """
    Registra el resultado de un match para que el Agente Learning aprenda
    """
    try:
        data = request.json
        match_id = data.get('match_id')
        resultado = data.get('resultado')  # 'contratado', 'rechazado', 'entrevista', 'sin_respuesta'
        
        if not match_id or not resultado:
            return jsonify({
                'success': False,
                'error': 'match_id y resultado son requeridos'
            }), 400
        
        # Obtener datos del match desde BD
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT m.*, 
                   e.id as est_id, e.carrera, e.universidad, e.habilidades, 
                   e.meses_experiencia, e.promedio, e.proyectos,
                   emp.id as emp_id, emp.area, emp.nombre as empresa_nombre
            FROM matches m
            JOIN estudiantes e ON m.estudiante_id = e.id
            JOIN empresas emp ON m.empresa_id = emp.id
            WHERE m.id = %s
        """, (match_id,))
        
        match_data = cursor.fetchone()
        
        if not match_data:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Match no encontrado'
            }), 404
        
        # Preparar datos para el agente
        match_info = {
            'match_id': match_id,
            'score_final': match_data['score_final'],
            'estudiante': {
                'id': match_data['est_id'],
                'carrera': match_data['carrera'],
                'universidad': match_data['universidad'],
                'habilidades': match_data['habilidades'],
                'meses_experiencia': match_data['meses_experiencia'],
                'promedio': match_data['promedio'],
                'proyectos': match_data['proyectos']
            },
            'empresa': {
                'id': match_data['emp_id'],
                'area': match_data['area'],
                'nombre': match_data['empresa_nombre']
            }
        }
        
        # Delegar al Agente 3: Learning System
        learning_system.registrar_resultado(match_info, resultado)
        
        # Guardar en BD
        learning_system.guardar_historial_db(conn)
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'mensaje': f"Resultado '{resultado}' registrado exitosamente para el aprendizaje del sistema"
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/insights-area/<area>', methods=['GET'])
def obtener_insights_area(area):
    """
    Obtiene insights de aprendizaje para un área específica
    """
    try:
        # Delegar al Agente 3: Learning System
        insights = learning_system.obtener_insights_area(area)
        
        return jsonify({
            'success': True,
            'insights': insights
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================
# ENDPOINT: Detectar Anomalías (Agente Anomaly)
# ============================================

@app.route('/api/detectar-anomalias', methods=['POST'])
def detectar_anomalias():
    """
    Ejecuta detección de anomalías en todo el sistema usando el Agente Anomaly
    """
    try:
        conn = get_db_connection()
        
        # Delegar al Agente 4: Anomaly Detector
        anomalias = anomaly_detector.detectar_todas_anomalias(conn)
        
        conn.close()
        
        # Separar por severidad
        criticas = [a for a in anomalias if a['severidad'] == 'critica']
        altas = [a for a in anomalias if a['severidad'] == 'alta']
        medias = [a for a in anomalias if a['severidad'] == 'media']
        bajas = [a for a in anomalias if a['severidad'] == 'baja']
        
        return jsonify({
            'success': True,
            'total_anomalias': len(anomalias),
            'por_severidad': {
                'criticas': len(criticas),
                'altas': len(altas),
                'medias': len(medias),
                'bajas': len(bajas)
            },
            'anomalias': anomalias,
            'mensaje': f"Se detectaron {len(anomalias)} anomalías en el sistema"
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/anomalias/resumen', methods=['GET'])
def resumen_anomalias():
    """
    Obtiene resumen de anomalías de los últimos 7 días
    """
    try:
        dias = request.args.get('dias', 7, type=int)
        
        conn = get_db_connection()
        
        # Delegar al Agente 4: Anomaly Detector
        resumen = anomaly_detector.obtener_resumen_anomalias(conn, dias)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'dias': dias,
            'resumen': resumen
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/anomalias/<int:anomalia_id>/resolver', methods=['POST'])
def resolver_anomalia(anomalia_id):
    """
    Marca una anomalía como resuelta
    """
    try:
        conn = get_db_connection()
        
        # Delegar al Agente 4: Anomaly Detector
        anomaly_detector.marcar_anomalia_resuelta(anomalia_id, conn)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'mensaje': f"Anomalía {anomalia_id} marcada como resuelta"
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================
# ENDPOINT: Alertas y Monitoreo Avanzado
# ============================================

@app.route('/api/alertas', methods=['GET'])
def obtener_alertas():
    """
    Genera alertas basadas en los KPIs actuales
    """
    try:
        conn = get_db_connection()
        
        # Obtener KPIs actuales
        kpis = monitor_agent.calcular_kpis_completos(conn)
        
        # Generar alertas basadas en KPIs
        alertas = monitor_agent.generar_alertas_rendimiento(kpis)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'total_alertas': len(alertas),
            'alertas': alertas
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/metricas/historico', methods=['GET'])
def obtener_historico_metricas():
    """
    Obtiene histórico de métricas para gráficos
    """
    try:
        dias = request.args.get('dias', 30, type=int)
        
        conn = get_db_connection()
        
        # Delegar al Agente 5: Monitor Agent
        historico = monitor_agent.obtener_historico_metricas(conn, dias)
        
        conn.close()
        
        return jsonify({
            'success': True,
            'dias': dias,
            'historico': historico
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================
# ENDPOINT: Recomendaciones para Estudiantes
# ============================================

@app.route('/api/recomendaciones/<int:estudiante_id>', methods=['GET'])
def obtener_recomendaciones_estudiante(estudiante_id):
    """
    Obtiene recomendaciones para mejorar el perfil de un estudiante
    """
    try:
        area_objetivo = request.args.get('area', type=str)
        
        if not area_objetivo:
            return jsonify({
                'success': False,
                'error': 'Parámetro "area" es requerido (ej: ?area=Desarrollo Software)'
            }), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Obtener estudiante
        cursor.execute("SELECT * FROM estudiantes WHERE id = %s", (estudiante_id,))
        estudiante = cursor.fetchone()
        
        if not estudiante:
            cursor.close()
            conn.close()
            return jsonify({
                'success': False,
                'error': 'Estudiante no encontrado'
            }), 404
        
        # Delegar al Agente 3: Learning System
        recomendaciones = learning_system.recomendar_mejoras_estudiante(
            dict(estudiante), 
            area_objetivo
        )
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'estudiante_id': estudiante_id,
            'area_objetivo': area_objetivo,
            'recomendaciones': recomendaciones
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================
# ENDPOINT: Estadísticas del Sistema de Aprendizaje
# ============================================

@app.route('/api/aprendizaje/estadisticas', methods=['GET'])
def estadisticas_aprendizaje():
    """
    Obtiene estadísticas generales del sistema de aprendizaje
    """
    try:
        # Delegar al Agente 3: Learning System
        stats = learning_system.obtener_estadisticas_generales()
        
        return jsonify({
            'success': True,
            'estadisticas': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================
# INICIAR SERVIDOR
# ============================================

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 API de Sistema de Prácticas Preprofesionales")
    print("=" * 60)
    print("📡 Servidor corriendo en: http://localhost:5000")
    print("🏥 Health check: http://localhost:5000/health")
    print("=" * 60)
    
    app.run(host='0.0.0.0', port=5000, debug=True)