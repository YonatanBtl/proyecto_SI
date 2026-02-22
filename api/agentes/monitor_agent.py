"""
Agente 5: Monitor Agent
Monitorea métricas del sistema en tiempo real y calcula KPIs
"""

import json
from datetime import datetime, timedelta
import pandas as pd


class MonitorAgent:
    """
    Agente de monitoreo
    Calcula KPIs y métricas del sistema
    """
    
    def __init__(self, redis_client=None):
        self.redis_client = redis_client
        self.usar_redis = redis_client is not None
        self.cache_memoria = {}
        self.cache_ttl = 300  # 5 minutos
    
    def calcular_kpis_completos(self, db_conn):
        """
        Calcula todos los KPIs del sistema
        
        Args:
            db_conn: Conexión a PostgreSQL
            
        Returns:
            dict: KPIs completos del sistema
        """
        
        kpis = {}
        
        # 1. Métricas de estudiantes
        kpis['estudiantes'] = self._metricas_estudiantes(db_conn)
        
        # 2. Métricas de empresas
        kpis['empresas'] = self._metricas_empresas(db_conn)
        
        # 3. Métricas de matches
        kpis['matches'] = self._metricas_matches(db_conn)
        
        # 4. Métricas de postulaciones
        kpis['postulaciones'] = self._metricas_postulaciones(db_conn)
        
        # 5. Métricas de rendimiento
        kpis['rendimiento'] = self._metricas_rendimiento(db_conn)
        
        # 6. Tendencias
        kpis['tendencias'] = self._calcular_tendencias(db_conn)
        
        kpis['fecha_calculo'] = datetime.now().isoformat()
        
        # Guardar en caché
        self._guardar_en_cache('kpis_sistema', kpis)
        
        # Guardar en BD para histórico
        self._guardar_kpis_db(kpis, db_conn)
        
        return kpis
    
    def _metricas_estudiantes(self, db_conn):
        """Métricas relacionadas con estudiantes"""
        
        cursor = db_conn.cursor()
        
        # Total de estudiantes
        cursor.execute("SELECT COUNT(*) as total FROM estudiantes")
        total = cursor.fetchone()['total']
        
        # Estudiantes activos (últimos 7 días)
        hace_7_dias = datetime.now() - timedelta(days=7)
        cursor.execute("""
            SELECT COUNT(DISTINCT estudiante_id) as activos
            FROM postulaciones
            WHERE fecha_postulacion >= %s
        """, (hace_7_dias,))
        activos = cursor.fetchone()['activos'] or 0
        
        # Completitud promedio de perfiles
        cursor.execute("SELECT AVG(completitud) as completitud_promedio FROM estudiantes")
        completitud_promedio = cursor.fetchone()['completitud_promedio'] or 0
        
        # Por carrera
        cursor.execute("""
            SELECT carrera, COUNT(*) as total
            FROM estudiantes
            GROUP BY carrera
            ORDER BY total DESC
            LIMIT 5
        """)
        por_carrera = [{'carrera': r['carrera'], 'total': r['total']} for r in cursor.fetchall()]
        
        # Por universidad
        cursor.execute("""
            SELECT universidad, COUNT(*) as total
            FROM estudiantes
            GROUP BY universidad
            ORDER BY total DESC
            LIMIT 5
        """)
        por_universidad = [{'universidad': r['universidad'], 'total': r['total']} for r in cursor.fetchall()]
        
        cursor.close()
        
        return {
            'total': total,
            'activos_7d': activos,
            'tasa_actividad': round((activos / total * 100) if total > 0 else 0, 2),
            'completitud_promedio': round(completitud_promedio, 2),
            'top_carreras': por_carrera,
            'top_universidades': por_universidad
        }
    
    def _metricas_empresas(self, db_conn):
        """Métricas relacionadas con empresas"""
        
        cursor = db_conn.cursor()
        
        # Total empresas activas
        cursor.execute("SELECT COUNT(*) as total FROM empresas WHERE activa = TRUE")
        total = cursor.fetchone()['total']
        
        # Por área
        cursor.execute("""
            SELECT area, COUNT(*) as total
            FROM empresas
            WHERE activa = TRUE
            GROUP BY area
            ORDER BY total DESC
        """)
        por_area = [{'area': r['area'], 'total': r['total']} for r in cursor.fetchall()]
        
        # Con más postulaciones
        cursor.execute("""
            SELECT e.nombre, COUNT(p.id) as total_postulaciones
            FROM empresas e
            LEFT JOIN postulaciones p ON e.id = p.empresa_id
            WHERE e.activa = TRUE
            GROUP BY e.id, e.nombre
            ORDER BY total_postulaciones DESC
            LIMIT 5
        """)
        top_demanda = [{'empresa': r['nombre'], 'postulaciones': r['total_postulaciones']} 
                       for r in cursor.fetchall()]
        
        cursor.close()
        
        return {
            'total_activas': total,
            'por_area': por_area,
            'top_demanda': top_demanda
        }

    def _metricas_matches(self, db_conn):
        """Métricas relacionadas con matches"""
        
        cursor = db_conn.cursor()
        
        # Total matches
        cursor.execute("SELECT COUNT(*) as total FROM matches")
        total = int(cursor.fetchone()['total'])

        # Última semana
        hace_7_dias = datetime.now() - timedelta(days=7)
        cursor.execute("SELECT COUNT(*) as total FROM matches WHERE fecha_match >= %s", (hace_7_dias,))
        ultimos_7d = int(cursor.fetchone()['total'])

        # Score promedio
        cursor.execute("SELECT AVG(score_final)::float as score_promedio FROM matches")
        score_promedio = float(cursor.fetchone()['score_promedio'] or 0)

        # Distribución de scores
        cursor.execute("""
            SELECT rango, COUNT(*) as total
            FROM (
                SELECT 
                    CASE 
                        WHEN score_final >= 80 THEN 'Excelente (80-100)'
                        WHEN score_final >= 60 THEN 'Bueno (60-79)'
                        WHEN score_final >= 40 THEN 'Regular (40-59)'
                        ELSE 'Bajo (<40)'
                    END as rango
                FROM matches
            ) sub
            GROUP BY rango
            ORDER BY 
                CASE rango
                    WHEN 'Excelente (80-100)' THEN 1
                    WHEN 'Bueno (60-79)' THEN 2
                    WHEN 'Regular (40-59)' THEN 3
                    ELSE 4
                END
        """)
        distribucion = [{'rango': r['rango'], 'total': int(r['total'])} for r in cursor.fetchall()]

        cursor.close()

        return {
            'total':               total,
            'ultimos_7d':          ultimos_7d,
            'score_promedio':      round(score_promedio, 2),
            'distribucion_scores': distribucion
        }

    def _metricas_postulaciones(self, db_conn):
        """Métricas relacionadas con postulaciones"""
        
        cursor = db_conn.cursor()
        
        # Total postulaciones
        cursor.execute("SELECT COUNT(*) as total FROM postulaciones")
        total = cursor.fetchone()['total']
        
        # Por estado
        cursor.execute("""
            SELECT estado, COUNT(*) as total
            FROM postulaciones
            GROUP BY estado
            ORDER BY total DESC
        """)
        por_estado = [{'estado': r['estado'], 'total': r['total']} for r in cursor.fetchall()]
        
        # Tasa de respuesta
        cursor.execute("SELECT COUNT(*) as con_respuesta FROM postulaciones WHERE fecha_respuesta IS NOT NULL")
        con_respuesta = cursor.fetchone()['con_respuesta']
        tasa_respuesta = round((con_respuesta / total * 100) if total > 0 else 0, 2)
        
        # Tiempo promedio de respuesta (en días)
        cursor.execute("""
            SELECT AVG(EXTRACT(DAY FROM (fecha_respuesta - fecha_postulacion))) as tiempo_promedio
            FROM postulaciones
            WHERE fecha_respuesta IS NOT NULL
        """)
        tiempo_respuesta = cursor.fetchone()['tiempo_promedio'] or 0
        
        # Tasa de éxito (contratados / total)
        cursor.execute("SELECT COUNT(*) as contratados FROM postulaciones WHERE estado = 'contratado'")
        contratados = cursor.fetchone()['contratados']
        tasa_exito = round((contratados / total * 100) if total > 0 else 0, 2)
        
        cursor.close()
        
        return {
            'total': total,
            'por_estado': por_estado,
            'tasa_respuesta': tasa_respuesta,
            'tiempo_respuesta_dias': round(tiempo_respuesta, 1),
            'contratados': contratados,
            'tasa_exito': tasa_exito
        }
    
    def _metricas_rendimiento(self, db_conn):
        """Métricas de rendimiento del sistema"""
        
        cursor = db_conn.cursor()
        
        # Precisión del matching (cuántos matches >60% terminan en postulación)
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN p.id IS NOT NULL THEN 1 END) as matches_postulados,
                COUNT(*) as total_matches
            FROM matches m
            LEFT JOIN postulaciones p ON m.id = p.match_id
            WHERE m.score_final >= 60
        """)
        resultado = cursor.fetchone()
        matches_postulados = resultado['matches_postulados'] or 0
        total_matches = resultado['total_matches'] or 1
        
        precision = round((matches_postulados / total_matches * 100), 2)
        
        # Recall (cuántas postulaciones vienen de matches sugeridos)
        cursor.execute("SELECT COUNT(*) as total_postulaciones FROM postulaciones")
        total_postulaciones = cursor.fetchone()['total_postulaciones'] or 1
        recall = round((matches_postulados / total_postulaciones * 100), 2)
        
        cursor.close()
        
        return {
            'precision_matching': precision,
            'recall_matching': recall,
            'matches_con_score_alto': total_matches,
            'conversion_a_postulacion': precision
        }
    
    def _calcular_tendencias(self, db_conn):
        """Calcula tendencias (cambios en últimos 7 vs 14 días)"""
        
        cursor = db_conn.cursor()
        
        hace_7d = datetime.now() - timedelta(days=7)
        hace_14d = datetime.now() - timedelta(days=14)
        
        # Postulaciones
        cursor.execute("SELECT COUNT(*) as total FROM postulaciones WHERE fecha_postulacion >= %s", (hace_7d,))
        post_7d = cursor.fetchone()['total']
        
        cursor.execute("""
            SELECT COUNT(*) as total FROM postulaciones 
            WHERE fecha_postulacion >= %s AND fecha_postulacion < %s
        """, (hace_14d, hace_7d))
        post_7_14d = cursor.fetchone()['total']
        
        cambio_postulaciones = self._calcular_cambio_porcentual(post_7d, post_7_14d)
        
        # Nuevos estudiantes
        cursor.execute("SELECT COUNT(*) as total FROM estudiantes WHERE fecha_registro >= %s", (hace_7d,))
        est_7d = cursor.fetchone()['total']
        
        cursor.execute("""
            SELECT COUNT(*) as total FROM estudiantes 
            WHERE fecha_registro >= %s AND fecha_registro < %s
        """, (hace_14d, hace_7d))
        est_7_14d = cursor.fetchone()['total']
        
        cambio_estudiantes = self._calcular_cambio_porcentual(est_7d, est_7_14d)
        
        cursor.close()
        
        return {
            'postulaciones': {
                'ultimos_7d': post_7d,
                'anteriores_7d': post_7_14d,
                'cambio_porcentual': cambio_postulaciones,
                'tendencia': 'subida' if cambio_postulaciones > 0 else 'bajada'
            },
            'nuevos_estudiantes': {
                'ultimos_7d': est_7d,
                'anteriores_7d': est_7_14d,
                'cambio_porcentual': cambio_estudiantes,
                'tendencia': 'subida' if cambio_estudiantes > 0 else 'bajada'
            }
        }
    
    def _calcular_cambio_porcentual(self, actual, anterior):
        """Calcula cambio porcentual entre dos valores"""
        if anterior == 0:
            return 100.0 if actual > 0 else 0.0
        
        cambio = ((actual - anterior) / anterior) * 100
        return round(cambio, 2)
    
    def generar_alertas_rendimiento(self, kpis):
        """Genera alertas basadas en los KPIs"""
        
        alertas = []
        
        # Alerta 1: Tasa de éxito muy baja
        if kpis['postulaciones']['tasa_exito'] < 10:
            alertas.append({
                'nivel': 'critico',
                'tipo': 'tasa_exito_baja',
                'mensaje': f"Tasa de éxito muy baja: {kpis['postulaciones']['tasa_exito']}%",
                'recomendacion': "Revisar algoritmo de matching o estrategia de recomendaciones"
            })
        
        # Alerta 2: Tiempo de respuesta muy alto
        if kpis['postulaciones']['tiempo_respuesta_dias'] > 14:
            alertas.append({
                'nivel': 'warning',
                'tipo': 'respuesta_lenta',
                'mensaje': f"Empresas tardan {kpis['postulaciones']['tiempo_respuesta_dias']:.1f} días en responder",
                'recomendacion': "Enviar recordatorios automáticos a empresas"
            })
        
        # Alerta 3: Poca actividad
        if kpis['estudiantes']['tasa_actividad'] < 20:
            alertas.append({
                'nivel': 'info',
                'tipo': 'baja_actividad',
                'mensaje': f"Solo {kpis['estudiantes']['tasa_actividad']}% de usuarios activos",
                'recomendacion': "Campaña de re-engagement"
            })
        
        # Alerta 4: Tendencia negativa
        if kpis['tendencias']['postulaciones']['cambio_porcentual'] < -20:
            alertas.append({
                'nivel': 'warning',
                'tipo': 'tendencia_negativa',
                'mensaje': f"Postulaciones bajaron {abs(kpis['tendencias']['postulaciones']['cambio_porcentual'])}%",
                'recomendacion': "Investigar causa de la caída"
            })
        
        return alertas
    
    def _guardar_en_cache(self, clave, datos):
        """Guarda datos en caché (Redis o memoria)"""
        
        if self.usar_redis:
            try:
                self.redis_client.setex(
                    clave,
                    self.cache_ttl,
                    json.dumps(datos, default=str)
                )
            except Exception as e:
                print(f"Error guardando en Redis: {e}")
        else:
            self.cache_memoria[clave] = {
                'datos': datos,
                'expira': datetime.now() + timedelta(seconds=self.cache_ttl)
            }
    
    def obtener_desde_cache(self, clave):
        """Obtiene datos desde caché"""
        
        if self.usar_redis:
            try:
                datos = self.redis_client.get(clave)
                if datos:
                    return json.loads(datos)
            except Exception as e:
                print(f"Error leyendo Redis: {e}")
        else:
            if clave in self.cache_memoria:
                entrada = self.cache_memoria[clave]
                if entrada['expira'] > datetime.now():
                    return entrada['datos']
                else:
                    del self.cache_memoria[clave]
        
        return None
    
    def _guardar_kpis_db(self, kpis, db_conn):
        """Guarda KPIs en base de datos para histórico"""
        
        cursor = db_conn.cursor()
        
        try:
            cursor.execute("""
                INSERT INTO metricas (
                    fecha, 
                    total_estudiantes, 
                    estudiantes_activos,
                    total_empresas,
                    total_matches,
                    matches_exitosos,
                    tasa_exito,
                    tiempo_respuesta_promedio,
                    kpis
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                datetime.now().date(),
                kpis['estudiantes']['total'],
                kpis['estudiantes']['activos_7d'],
                kpis['empresas']['total_activas'],
                kpis['matches']['total'],
                kpis['postulaciones']['contratados'],
                kpis['postulaciones']['tasa_exito'],
                kpis['postulaciones']['tiempo_respuesta_dias'],
                json.dumps(kpis, default=str)
            ))
            db_conn.commit()
        except Exception as e:
            print(f"Error guardando KPIs en BD: {e}")
        finally:
            cursor.close()
    
    def obtener_historico_metricas(self, db_conn, dias=30):
        """Obtiene histórico de métricas para gráficos"""
        
        query = f"""
        SELECT *
        FROM metricas
        WHERE fecha >= CURRENT_DATE - INTERVAL '{dias} days'
        ORDER BY fecha
        """
        
        df = pd.read_sql(query, db_conn)
        
        return df.to_dict('records')