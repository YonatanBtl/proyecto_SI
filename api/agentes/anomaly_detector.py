"""
Agente 4: Anomaly Detector
Detecta comportamientos anómalos y sospechosos en el sistema
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta


class AnomalyDetector:
    """
    Agente de detección de anomalías.
    Identifica patrones sospechosos y comportamientos anormales.
    """

    def __init__(self):
        self.umbral_zscore      = 2.5
        self.empresas_alertadas  = set()
        self.estudiantes_alertados = set()

    # =========================================================
    # MÉTODO PRINCIPAL
    # =========================================================

    def detectar_todas_anomalias(self, db_conn):
        """Ejecuta todos los detectores y retorna lista de anomalías."""
        anomalias = []

        try:
            anomalias.extend(self._detectar_empresas_inactivas(db_conn))
        except Exception as e:
            print(f"⚠️ Error en empresas_inactivas: {e}")

        try:
            anomalias.extend(self._detectar_requisitos_imposibles(db_conn))
        except Exception as e:
            print(f"⚠️ Error en requisitos_imposibles: {e}")

        try:
            anomalias.extend(self._detectar_estudiantes_spam(db_conn))
        except Exception as e:
            print(f"⚠️ Error en estudiantes_spam: {e}")

        try:
            anomalias.extend(self._detectar_picos_anomalos(db_conn))
        except Exception as e:
            print(f"⚠️ Error en picos_anomalos: {e}")

        try:
            anomalias.extend(self._detectar_scores_anomalos(db_conn))
        except Exception as e:
            print(f"⚠️ Error en scores_anomalos: {e}")

        # Guardar en base de datos
        for anomalia in anomalias:
            self._guardar_anomalia_db(anomalia, db_conn)

        return anomalias

    # =========================================================
    # DETECTOR 1: Empresas inactivas
    # =========================================================

    def _detectar_empresas_inactivas(self, db_conn):
        """Detecta empresas que nunca responden a postulaciones."""
        query = """
        SELECT
            e.id,
            e.nombre,
            COUNT(p.id)::float AS total_postulaciones,
            SUM(CASE WHEN p.estado != 'postulado' THEN 1 ELSE 0 END)::float AS respuestas
        FROM empresas e
        JOIN postulaciones p ON e.id = p.empresa_id
        WHERE e.activa = TRUE
        GROUP BY e.id, e.nombre
        HAVING COUNT(p.id) >= 5
        """
        df = pd.read_sql(query, db_conn)
        if df.empty:
            return []

        df['tasa_respuesta'] = df['respuestas'] / df['total_postulaciones']
        empresas_inactivas   = df[df['tasa_respuesta'] < 0.10]

        anomalias = []
        for _, row in empresas_inactivas.iterrows():
            if row['id'] not in self.empresas_alertadas:
                anomalias.append({
                    'tipo':         'empresa_inactiva',
                    'entidad_tipo': 'empresa',
                    'entidad_id':   int(row['id']),
                    'severidad':    'alta',
                    'descripcion':  (
                        f"Empresa '{row['nombre']}' tiene {int(row['total_postulaciones'])} "
                        f"postulaciones pero solo {row['tasa_respuesta']*100:.1f}% de tasa de respuesta"
                    ),
                    'recomendacion': "Contactar a la empresa o desactivarla temporalmente",
                })
                self.empresas_alertadas.add(row['id'])

        return anomalias

    # =========================================================
    # DETECTOR 2: Requisitos imposibles
    # =========================================================

    def _detectar_requisitos_imposibles(self, db_conn):
        """Detecta empresas con requisitos contradictorios o imposibles."""
        query = "SELECT * FROM empresas WHERE activa = TRUE"
        df    = pd.read_sql(query, db_conn)
        anomalias = []

        for _, empresa in df.iterrows():
            problemas = []

            exp_min       = float(empresa['experiencia_minima'] or 0)
            horas_req     = float(empresa['horas_requeridas'] or 0)
            salario       = float(empresa['salario'] or 0)
            num_requisitos = len(empresa['requisitos']) if empresa['requisitos'] is not None else 0

            if empresa.get('tipo') == 'practica' and exp_min > 24:
                problemas.append(f"Práctica requiere {int(exp_min)} meses de experiencia (>2 años)")

            if num_requisitos > 10:
                problemas.append(f"Requiere {num_requisitos} habilidades (muy alto para práctica)")

            if num_requisitos >= 8 and salario < 500:
                problemas.append(f"Requiere {num_requisitos} habilidades pero ofrece solo S/{salario:.0f}")

            if empresa.get('tipo') == 'practica' and horas_req > 40:
                problemas.append(f"Requiere {int(horas_req)} horas/semana (excesivo para práctica)")

            if problemas:
                anomalias.append({
                    'tipo':         'requisitos_imposibles',
                    'entidad_tipo': 'empresa',
                    'entidad_id':   int(empresa['id']),
                    'severidad':    'media',
                    'descripcion':  f"Empresa '{empresa['nombre']}' tiene requisitos problemáticos: {'; '.join(problemas)}",
                    'recomendacion': "Revisar y ajustar requisitos de la oferta",
                })

        return anomalias

    # =========================================================
    # DETECTOR 3: Estudiantes spam
    # =========================================================

    def _detectar_estudiantes_spam(self, db_conn):
        """Detecta estudiantes que postulan indiscriminadamente."""
        hace_7_dias = datetime.now() - timedelta(days=7)

        query = """
        SELECT
            e.id,
            e.nombre,
            COUNT(p.id)::int          AS total_postulaciones,
            COUNT(DISTINCT emp.area)::int AS areas_diferentes
        FROM estudiantes e
        JOIN postulaciones p   ON e.id = p.estudiante_id
        JOIN empresas emp      ON p.empresa_id = emp.id
        WHERE p.fecha_postulacion >= %s
        GROUP BY e.id, e.nombre
        """
        df = pd.read_sql(query, db_conn, params=(hace_7_dias,))
        if df.empty:
            return []

        anomalias = []
        for _, row in df.iterrows():
            problemas = []
            if row['total_postulaciones'] > 20:
                problemas.append(f"Postuló {int(row['total_postulaciones'])} veces en 7 días")
            if row['areas_diferentes'] > 5:
                problemas.append(f"Postuló a {int(row['areas_diferentes'])} áreas completamente diferentes")

            if problemas:
                anomalias.append({
                    'tipo':         'estudiante_spam',
                    'entidad_tipo': 'estudiante',
                    'entidad_id':   int(row['id']),
                    'severidad':    'baja',
                    'descripcion':  f"Estudiante '{row['nombre']}': {'; '.join(problemas)}",
                    'recomendacion': "Enviar recomendación de estrategia de búsqueda más enfocada",
                })

        return anomalias

    # =========================================================
    # DETECTOR 4: Picos anómalos de postulaciones
    # =========================================================

    def _detectar_picos_anomalos(self, db_conn):
        """Detecta picos inusuales en el número de postulaciones usando Z-score."""
        query = """
        SELECT
            DATE(fecha_postulacion)  AS fecha,
            COUNT(*)::float          AS num_postulaciones
        FROM postulaciones
        WHERE fecha_postulacion >= CURRENT_DATE - INTERVAL '30 days'
        GROUP BY DATE(fecha_postulacion)
        ORDER BY fecha
        """
        df = pd.read_sql(query, db_conn)

        if len(df) < 7:
            return []

        media = float(df['num_postulaciones'].mean())
        std   = float(df['num_postulaciones'].std())

        if std == 0:
            return []

        df['z_score'] = (df['num_postulaciones'] - media) / std
        dias_anomalos = df[abs(df['z_score']) > self.umbral_zscore]

        anomalias = []
        for _, row in dias_anomalos.iterrows():
            anomalias.append({
                'tipo':         'pico_anomalo_postulaciones',
                'entidad_tipo': 'sistema',
                'entidad_id':   None,
                'severidad':    'media',
                'descripcion':  (
                    f"Pico anómalo el {row['fecha']}: "
                    f"{int(row['num_postulaciones'])} postulaciones (promedio: {media:.1f})"
                ),
                'recomendacion': "Investigar causa del pico (campaña, bot, evento especial)",
            })

        return anomalias

    # =========================================================
    # DETECTOR 5: Scores anómalos
    # =========================================================

    def _detectar_scores_anomalos(self, db_conn):
        """Detecta matches con scores sospechosamente perfectos o postulaciones con score muy bajo."""
        anomalias = []

        # Matches perfectos (score = 100)
        query_perfectos = """
        SELECT m.id, m.score_final::float,
               e.nombre AS estudiante_nombre,
               emp.nombre AS empresa_nombre
        FROM matches m
        JOIN estudiantes e  ON m.estudiante_id = e.id
        JOIN empresas emp    ON m.empresa_id = emp.id
        WHERE m.score_final = 100
          AND m.fecha_match >= CURRENT_DATE - INTERVAL '7 days'
        """
        df_perf = pd.read_sql(query_perfectos, db_conn)
        for _, match in df_perf.iterrows():
            anomalias.append({
                'tipo':         'score_perfecto_sospechoso',
                'entidad_tipo': 'match',
                'entidad_id':   int(match['id']),
                'severidad':    'baja',
                'descripcion':  f"Match perfecto (100%) entre '{match['estudiante_nombre']}' y '{match['empresa_nombre']}'",
                'recomendacion': "Verificar que el algoritmo no tenga sesgos",
            })

        # Postulaciones con score muy bajo (<40)
        query_bajos = """
        SELECT m.id, m.score_final::float,
               e.nombre AS estudiante_nombre,
               emp.nombre AS empresa_nombre
        FROM matches m
        JOIN postulaciones p ON m.id = p.match_id
        JOIN estudiantes e   ON m.estudiante_id = e.id
        JOIN empresas emp    ON m.empresa_id = emp.id
        WHERE m.score_final < 40
        """
        df_bajos = pd.read_sql(query_bajos, db_conn)
        for _, match in df_bajos.iterrows():
            anomalias.append({
                'tipo':         'postulacion_score_bajo',
                'entidad_tipo': 'match',
                'entidad_id':   int(match['id']),
                'severidad':    'baja',
                'descripcion':  (
                    f"Estudiante '{match['estudiante_nombre']}' postuló a "
                    f"'{match['empresa_nombre']}' con match de solo {match['score_final']:.1f}%"
                ),
                'recomendacion': "Puede ser una postulación desesperada o error del estudiante",
            })

        return anomalias

    # =========================================================
    # GUARDAR EN BD
    # =========================================================

    def _guardar_anomalia_db(self, anomalia, db_conn):
        """Guarda anomalía detectada en la base de datos."""
        cursor = db_conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO anomalias (tipo, entidad_tipo, entidad_id, descripcion, severidad)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                anomalia['tipo'],
                anomalia['entidad_tipo'],
                anomalia.get('entidad_id'),
                anomalia['descripcion'],
                anomalia['severidad']
            ))
            db_conn.commit()
        except Exception as e:
            print(f"Error guardando anomalía: {e}")
            db_conn.rollback()
        finally:
            cursor.close()

    # =========================================================
    # CONSULTAS ADICIONALES
    # =========================================================

    def obtener_resumen_anomalias(self, db_conn, dias=7):
        """Obtiene resumen de anomalías de los últimos N días."""
        query = f"""
        SELECT
            tipo, severidad,
            COUNT(*) AS total,
            MAX(fecha_deteccion) AS ultima_deteccion
        FROM anomalias
        WHERE fecha_deteccion >= CURRENT_DATE - INTERVAL '{dias} days'
          AND resuelta = FALSE
        GROUP BY tipo, severidad
        ORDER BY
            CASE severidad
                WHEN 'critica' THEN 1
                WHEN 'alta'    THEN 2
                WHEN 'media'   THEN 3
                ELSE 4
            END, total DESC
        """
        df = pd.read_sql(query, db_conn)
        return df.to_dict('records')

    def marcar_anomalia_resuelta(self, anomalia_id, db_conn):
        """Marca una anomalía como resuelta."""
        cursor = db_conn.cursor()
        cursor.execute("UPDATE anomalias SET resuelta = TRUE WHERE id = %s", (anomalia_id,))
        db_conn.commit()
        cursor.close()

    def generar_alerta_email(self, anomalias, destinatario='admin@sistema.com'):
        """Genera contenido HTML de email para anomalías críticas/altas."""
        criticas = [a for a in anomalias if a['severidad'] in ['critica', 'alta']]
        if not criticas:
            return None

        items = "".join([
            f"<li><strong>[{a['severidad'].upper()}] {a['tipo']}</strong><br>"
            f"{a['descripcion']}<br>"
            f"<em>Recomendación: {a['recomendacion']}</em></li>"
            for a in criticas
        ])

        return {
            'destinatario':   destinatario,
            'asunto':         f"🚨 {len(criticas)} Anomalías Detectadas en el Sistema",
            'contenido_html': f"<h2>🚨 Alertas de Anomalías</h2><ul>{items}</ul>"
        }