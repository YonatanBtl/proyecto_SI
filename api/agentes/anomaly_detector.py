"""
Agente 4: Anomaly Detector
Detecta comportamientos anómalos y sospechosos en el sistema
"""

from datetime import datetime, timedelta


class AnomalyDetector:
    """
    Agente de detección de anomalías.
    Usa cursor directo en vez de pd.read_sql para compatibilidad con psycopg2.
    """

    def __init__(self):
        self.umbral_zscore         = 2.5
        self.empresas_alertadas    = set()
        self.estudiantes_alertados = set()

    def detectar_todas_anomalias(self, db_conn):
        anomalias = []
        for metodo in [
            self._detectar_empresas_inactivas,
            self._detectar_requisitos_imposibles,
            self._detectar_estudiantes_spam,
            self._detectar_picos_anomalos,
            self._detectar_scores_anomalos,
        ]:
            try:
                anomalias.extend(metodo(db_conn))
            except Exception as e:
                print(f" Error en {metodo.__name__}: {e}")

        for anomalia in anomalias:
            self._guardar_anomalia_db(anomalia, db_conn)

        return anomalias

    def _detectar_empresas_inactivas(self, db_conn):
        cursor = db_conn.cursor()
        cursor.execute("""
            SELECT e.id, e.nombre,
                   COUNT(p.id) AS total_postulaciones,
                   SUM(CASE WHEN p.estado != 'postulado' THEN 1 ELSE 0 END) AS respuestas
            FROM empresas e
            JOIN postulaciones p ON e.id = p.empresa_id
            WHERE e.activa = TRUE
            GROUP BY e.id, e.nombre
            HAVING COUNT(p.id) >= 5
        """)
        rows = cursor.fetchall()
        cursor.close()

        anomalias = []
        for row in rows:
            total     = int(row['total_postulaciones'])
            respuestas = int(row['respuestas'])
            tasa      = respuestas / total if total > 0 else 0

            if tasa < 0.20 and row['id'] not in self.empresas_alertadas:
                anomalias.append({
                    'tipo': 'empresa_inactiva', 'entidad_tipo': 'empresa',
                    'entidad_id': int(row['id']), 'severidad': 'alta',
                    'descripcion': (
                        f"Empresa '{row['nombre']}' tiene {total} postulaciones "
                        f"pero solo {tasa*100:.1f}% de tasa de respuesta"
                    ),
                    'recomendacion': "Contactar a la empresa o desactivarla temporalmente",
                })
                self.empresas_alertadas.add(row['id'])
        return anomalias

    def _detectar_requisitos_imposibles(self, db_conn):
        cursor = db_conn.cursor()
        cursor.execute("SELECT * FROM empresas WHERE activa = TRUE")
        rows = cursor.fetchall()
        cursor.close()

        anomalias = []
        for empresa in rows:
            problemas      = []
            exp_min        = float(empresa['experiencia_minima'] or 0)
            horas_req      = float(empresa['horas_requeridas'] or 0)
            salario        = float(empresa['salario'] or 0)
            num_requisitos = len(empresa['requisitos']) if empresa['requisitos'] else 0

            if empresa['tipo'] == 'practica' and exp_min > 24:
                problemas.append(f"Práctica requiere {int(exp_min)} meses de experiencia (>2 años)")
            if num_requisitos > 10:
                problemas.append(f"Requiere {num_requisitos} habilidades (muy alto)")
            if num_requisitos >= 8 and salario < 500:
                problemas.append(f"Requiere {num_requisitos} habilidades pero ofrece solo S/{salario:.0f}")
            if empresa['tipo'] == 'practica' and horas_req > 40:
                problemas.append(f"Requiere {int(horas_req)} horas/semana (excesivo)")

            if problemas:
                anomalias.append({
                    'tipo': 'requisitos_imposibles', 'entidad_tipo': 'empresa',
                    'entidad_id': int(empresa['id']), 'severidad': 'media',
                    'descripcion': f"Empresa '{empresa['nombre']}': {'; '.join(problemas)}",
                    'recomendacion': "Revisar y ajustar requisitos de la oferta",
                })
        return anomalias

    def _detectar_estudiantes_spam(self, db_conn):
        hace_7_dias = datetime.now() - timedelta(days=7)
        cursor = db_conn.cursor()
        cursor.execute("""
            SELECT e.id, e.nombre,
                   COUNT(p.id)              AS total_postulaciones,
                   COUNT(DISTINCT emp.area) AS areas_diferentes
            FROM estudiantes e
            JOIN postulaciones p  ON e.id = p.estudiante_id
            JOIN empresas emp     ON p.empresa_id = emp.id
            WHERE p.fecha_postulacion >= %s
            GROUP BY e.id, e.nombre
        """, (hace_7_dias,))
        rows = cursor.fetchall()
        cursor.close()

        anomalias = []
        for row in rows:
            total_post = int(row['total_postulaciones'])
            areas      = int(row['areas_diferentes'])
            problemas  = []

            if total_post > 20:
                problemas.append(f"Postuló {total_post} veces en 7 días")
            if areas > 5:
                problemas.append(f"Postuló a {areas} áreas diferentes")

            if problemas:
                anomalias.append({
                    'tipo': 'estudiante_spam', 'entidad_tipo': 'estudiante',
                    'entidad_id': int(row['id']), 'severidad': 'baja',
                    'descripcion': f"Estudiante '{row['nombre']}': {'; '.join(problemas)}",
                    'recomendacion': "Enviar recomendación de estrategia más enfocada",
                })
        return anomalias

    def _detectar_picos_anomalos(self, db_conn):
        cursor = db_conn.cursor()
        cursor.execute("""
            SELECT DATE(fecha_postulacion) AS fecha, COUNT(*) AS num_postulaciones
            FROM postulaciones
            WHERE fecha_postulacion >= CURRENT_DATE - INTERVAL '30 days'
            GROUP BY DATE(fecha_postulacion)
            ORDER BY fecha
        """)
        rows = cursor.fetchall()
        cursor.close()

        if len(rows) < 7:
            return []

        valores = [float(r['num_postulaciones']) for r in rows]
        media   = sum(valores) / len(valores)
        std     = (sum((v - media) ** 2 for v in valores) / len(valores)) ** 0.5

        if std == 0:
            return []

        anomalias = []
        for row, val in zip(rows, valores):
            if abs((val - media) / std) > self.umbral_zscore:
                anomalias.append({
                    'tipo': 'pico_anomalo_postulaciones', 'entidad_tipo': 'sistema',
                    'entidad_id': None, 'severidad': 'media',
                    'descripcion': f"Pico anómalo el {row['fecha']}: {int(val)} postulaciones (promedio: {media:.1f})",
                    'recomendacion': "Investigar causa del pico",
                })
        return anomalias

    def _detectar_scores_anomalos(self, db_conn):
        cursor = db_conn.cursor()
        cursor.execute("""
            SELECT m.id, m.score_final, e.nombre AS estudiante_nombre, emp.nombre AS empresa_nombre
            FROM matches m
            JOIN postulaciones p ON m.id = p.match_id
            JOIN estudiantes e   ON m.estudiante_id = e.id
            JOIN empresas emp    ON m.empresa_id = emp.id
            WHERE m.score_final < 40
            LIMIT 20
        """)
        rows = cursor.fetchall()
        cursor.close()

        return [{
            'tipo': 'postulacion_score_bajo', 'entidad_tipo': 'match',
            'entidad_id': int(r['id']), 'severidad': 'baja',
            'descripcion': (
                f"Estudiante '{r['estudiante_nombre']}' postuló a "
                f"'{r['empresa_nombre']}' con match de solo {float(r['score_final']):.1f}%"
            ),
            'recomendacion': "Puede ser una postulación desesperada o error del estudiante",
        } for r in rows]

    def _guardar_anomalia_db(self, anomalia, db_conn):
        cursor = db_conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO anomalias (tipo, entidad_tipo, entidad_id, descripcion, severidad)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                anomalia['tipo'], anomalia['entidad_tipo'], anomalia.get('entidad_id'),
                anomalia['descripcion'], anomalia['severidad']
            ))
            db_conn.commit()
        except Exception as e:
            print(f"Error guardando anomalía: {e}")
            db_conn.rollback()
        finally:
            cursor.close()

    def obtener_resumen_anomalias(self, db_conn, dias=7):
        cursor = db_conn.cursor()
        cursor.execute(f"""
            SELECT tipo, severidad, COUNT(*) AS total, MAX(fecha_deteccion) AS ultima_deteccion
            FROM anomalias
            WHERE fecha_deteccion >= CURRENT_DATE - INTERVAL '{dias} days'
              AND resuelta = FALSE
            GROUP BY tipo, severidad
            ORDER BY CASE severidad
                WHEN 'critica' THEN 1 WHEN 'alta' THEN 2 WHEN 'media' THEN 3 ELSE 4
            END, total DESC
        """)
        rows = cursor.fetchall()
        cursor.close()
        return [dict(r) for r in rows]

    def marcar_anomalia_resuelta(self, anomalia_id, db_conn):
        cursor = db_conn.cursor()
        cursor.execute("UPDATE anomalias SET resuelta = TRUE WHERE id = %s", (anomalia_id,))
        db_conn.commit()
        cursor.close()

    def generar_alerta_email(self, anomalias, destinatario='admin@sistema.com'):
        criticas = [a for a in anomalias if a['severidad'] in ['critica', 'alta']]
        if not criticas:
            return None
        items = "".join([
            f"<li><strong>[{a['severidad'].upper()}] {a['tipo']}</strong><br>"
            f"{a['descripcion']}<br><em>Recomendación: {a['recomendacion']}</em></li>"
            for a in criticas
        ])
        return {
            'destinatario': destinatario,
            'asunto': f" {len(criticas)} Anomalías Detectadas en el Sistema",
            'contenido_html': f"<h2> Alertas de Anomalías</h2><ul>{items}</ul>"
        }