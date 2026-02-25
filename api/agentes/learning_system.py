"""
Agente 3: Learning System
Aprende de matches exitosos y mejora predicciones.
Los pesos aprendidos se persisten en PostgreSQL para no perderse al reiniciar.
"""

# Usamos solo librerías estándar de Python (sin numpy/pandas)
# defaultdict: diccionario que crea automáticamente listas vacías para claves nuevas
from collections import defaultdict
from datetime import datetime
import json


class LearningSystem:
    """
    Agente de aprendizaje adaptativo.

    ¿Cómo funciona?
    1. Recibe resultados de matches (contratado, rechazado, etc.)
    2. Analiza qué características tienen los matches exitosos (contratados)
    3. Ajusta los pesos del algoritmo según lo aprendido
    4. Guarda esos pesos en PostgreSQL para que sobrevivan reinicios de Docker
    """

    def __init__(self):
        # Lista de todos los matches registrados en esta sesión (en memoria)
        self.historial_matches = []

        # Diccionario: área -> lista de patrones exitosos
        # Ejemplo: {'Desarrollo Software': [{carrera, habilidades, ...}, ...]}
        self.patrones_exito = defaultdict(list)

        # Diccionario: área -> pesos aprendidos
        # Ejemplo: {'Desarrollo Software': {'habilidades': 0.50, 'experiencia': 0.25, ...}}
        self.pesos_aprendidos = {}

        # Mínimo de casos exitosos necesarios para recalcular pesos
        self.min_datos_aprendizaje = 5

    # =========================================================
    # SECCIÓN 1: REGISTRAR Y ANALIZAR RESULTADOS
    # =========================================================

    def registrar_resultado(self, match_data, resultado):
        """
        Registra el resultado de un match para que el agente aprenda.

        Args:
            match_data (dict): Información del match (estudiante, empresa, score)
            resultado (str): 'contratado', 'rechazado', 'entrevista', 'sin_respuesta'
        """
        # Guardamos el registro en memoria para esta sesión
        registro = {
            'match_id':    match_data.get('match_id'),
            'estudiante':  match_data.get('estudiante'),
            'empresa':     match_data.get('empresa'),
            'score_match': match_data.get('score_final'),
            'resultado':   resultado,
            'timestamp':   datetime.now()
        }
        self.historial_matches.append(registro)

        # Solo aprendemos de los casos exitosos (contratados)
        if resultado == 'contratado':
            self._analizar_patron_exitoso(match_data)

    def _analizar_patron_exitoso(self, match_data):
        """
        Extrae las características del match exitoso y las guarda como patrón.
        Cuando hay suficientes patrones, recalcula los pesos del área.
        """
        estudiante = match_data.get('estudiante', {})
        empresa    = match_data.get('empresa', {})
        area       = empresa.get('area')  # Agrupamos patrones por área de empresa

        # Extraemos las características relevantes del match exitoso
        # Usamos float/int para evitar errores con valores None de la BD
        patron = {
            'area_empresa':       area,
            'carrera_estudiante': estudiante.get('carrera'),
            'universidad':        estudiante.get('universidad'),
            'promedio':           float(estudiante.get('promedio') or 0),
            'habilidades_clave':  estudiante.get('habilidades', []),
            'experiencia_meses':  int(estudiante.get('meses_experiencia') or 0),
            'score_match':        float(match_data.get('score_final') or 0)
        }

        # Agregamos el patrón al área correspondiente
        self.patrones_exito[area].append(patron)

        # Si tenemos suficientes casos, recalcular pesos para esta área
        if len(self.patrones_exito[area]) >= self.min_datos_aprendizaje:
            self._actualizar_pesos_area(area)

    def _actualizar_pesos_area(self, area):
        """
        Recalcula los pesos óptimos para un área basándose en casos exitosos.

        Lógica: Si los contratados en esta área tienen mucha experiencia,
        subimos el peso de experiencia. Si tienen poca, lo bajamos.
        """
        patrones = self.patrones_exito[area]

        if len(patrones) < self.min_datos_aprendizaje:
            return  # No hay suficientes datos aún

        # --- Calcular estadísticas de los casos exitosos ---

        # Promedio de experiencia de todos los contratados en esta área
        experiencias  = [p['experiencia_meses'] for p in patrones]
        promedios     = [p['promedio']           for p in patrones]
        universidades = [p['universidad']        for p in patrones if p['universidad']]

        exp_promedio       = sum(experiencias) / len(experiencias)
        promedio_academico = sum(promedios)    / len(promedios) if promedios else 0

        # Top 3 universidades más frecuentes entre los contratados
        uni_count = defaultdict(int)
        for u in universidades:
            uni_count[u] += 1
        top_universidades = sorted(uni_count, key=uni_count.get, reverse=True)[:3]

        # Top 5 habilidades más frecuentes entre los contratados
        todas_habilidades = [h for p in patrones for h in p['habilidades_clave']]
        hab_count = defaultdict(int)
        for h in todas_habilidades:
            hab_count[h] += 1
        habilidades_frecuentes = dict(
            sorted(hab_count.items(), key=lambda x: x[1], reverse=True)[:5]
        )

        # --- Ajustar peso de experiencia dinámicamente ---
        # Si los contratados tienen >12 meses de exp -> la experiencia importa más
        # Si tienen <6 meses -> la experiencia importa menos (área junior-friendly)
        if exp_promedio > 12:
            nuevo_peso_exp = 0.35
        elif exp_promedio < 6:
            nuevo_peso_exp = 0.15
        else:
            nuevo_peso_exp = 0.25  # Peso neutral

        # Los pesos deben sumar 1.0
        # Al subir experiencia, bajamos habilidades proporcionalmente
        self.pesos_aprendidos[area] = {
            'habilidades': round(0.50 - (nuevo_peso_exp - 0.25), 3),
            'experiencia': round(nuevo_peso_exp, 3),
            'carrera':     0.15,
            'otros':       0.10,
            # Guardamos metadata para mostrar insights y recomendaciones
            'metadata': {
                'exp_promedio':       round(exp_promedio, 1),
                'top_universidades':  top_universidades,
                'promedio_academico': round(promedio_academico, 2),
                'habilidades_clave':  habilidades_frecuentes,
                'n_muestras':         len(patrones)
            }
        }

        print(f"✅ Pesos actualizados para área '{area}' con {len(patrones)} casos exitosos")

    # =========================================================
    # SECCIÓN 2: PREDICCIÓN DE ÉXITO
    # =========================================================

    def predecir_probabilidad_exito(self, estudiante, empresa):
        """
        Predice qué tan probable es que este estudiante sea contratado
        por esta empresa, basándose en patrones históricos.

        Returns:
            float: Probabilidad 0-100 (50 = sin información suficiente)
        """
        area = empresa.get('area')

        # Sin datos históricos del área, retornamos 50% (neutral)
        if area not in self.patrones_exito or len(self.patrones_exito[area]) < self.min_datos_aprendizaje:
            return 50.0

        patrones_similares = 0
        total_patrones     = len(self.patrones_exito[area])

        # Comparamos el estudiante contra cada patrón exitoso del área
        for patron in self.patrones_exito[area]:
            sim = 0.0

            # Misma carrera = +30% similitud
            if patron['carrera_estudiante'] == estudiante.get('carrera'):
                sim += 0.30

            # Misma universidad = +20% similitud
            if patron['universidad'] == estudiante.get('universidad'):
                sim += 0.20

            # Habilidades en común = hasta +30% similitud
            habs_est    = set(estudiante.get('habilidades', []))
            habs_patron = set(patron['habilidades_clave'])
            if habs_patron:
                sim += (len(habs_est & habs_patron) / len(habs_patron)) * 0.30

            # Experiencia similar = hasta +20% similitud
            diff_exp = abs(int(estudiante.get('meses_experiencia') or 0) - patron['experiencia_meses'])
            sim += 0.20 if diff_exp <= 6 else (0.10 if diff_exp <= 12 else 0)

            # Si la similitud supera 60%, contamos como patrón similar
            if sim >= 0.6:
                patrones_similares += 1

        # Calculamos probabilidad base
        probabilidad = (patrones_similares / total_patrones) * 100

        # Ajustamos por confianza: con más datos, el resultado es más fiable
        # Con 20+ casos tenemos máxima confianza
        factor_confianza   = min(total_patrones / 20, 1.0)
        probabilidad_ajust = 50 + (probabilidad - 50) * factor_confianza

        return round(probabilidad_ajust, 2)

    # =========================================================
    # SECCIÓN 3: PERSISTENCIA DE PESOS EN POSTGRESQL
    # =========================================================

    def guardar_pesos_db(self, db_conn):
        """
        Guarda los pesos aprendidos en la tabla 'learning_pesos' de PostgreSQL.

        ¿Por qué es importante?
        Sin esto, cuando Docker se reinicia, el agente olvida todo lo aprendido
        y vuelve a los pesos por defecto. Con esto, el aprendizaje es permanente.

        La tabla se crea automáticamente si no existe.
        """
        cursor = db_conn.cursor()

        # Crear la tabla si aún no existe en la BD
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learning_pesos (
                id          SERIAL PRIMARY KEY,
                area        VARCHAR(100) UNIQUE NOT NULL,
                pesos       JSONB NOT NULL,
                n_muestras  INT DEFAULT 0,
                actualizado TIMESTAMP DEFAULT NOW()
            )
        """)

        # Guardar o actualizar los pesos de cada área
        for area, pesos in self.pesos_aprendidos.items():
            cursor.execute("""
                INSERT INTO learning_pesos (area, pesos, n_muestras, actualizado)
                VALUES (%s, %s, %s, NOW())
                ON CONFLICT (area) DO UPDATE SET
                    pesos       = EXCLUDED.pesos,
                    n_muestras  = EXCLUDED.n_muestras,
                    actualizado = NOW()
            """, (
                area,
                json.dumps(pesos),  # Convertimos el dict a JSON para guardarlo
                pesos.get('metadata', {}).get('n_muestras', 0)
            ))

        db_conn.commit()
        cursor.close()
        print(f"💾 Pesos guardados en BD para {len(self.pesos_aprendidos)} áreas")

    def cargar_pesos_db(self, db_conn):
        """
        Carga los pesos previamente aprendidos desde PostgreSQL.
        Se llama al iniciar la API para recuperar el conocimiento acumulado.
        """
        cursor = db_conn.cursor()

        try:
            cursor.execute("""
                SELECT area, pesos, n_muestras
                FROM learning_pesos
                ORDER BY actualizado DESC
            """)
            rows = cursor.fetchall()

            # Cargamos cada área y sus pesos en memoria
            for row in rows:
                # row['pesos'] ya viene como dict porque psycopg2 convierte JSONB
                self.pesos_aprendidos[row['area']] = row['pesos']

            if rows:
                print(f"✅ Pesos cargados desde BD para {len(rows)} áreas")
            else:
                print("ℹ️  Sin pesos previos en BD — comenzando desde cero")

        except Exception as e:
            # La tabla puede no existir aún si nunca se ha guardado nada
            print(f"⚠️  No se pudieron cargar pesos (tabla puede no existir aún): {e}")
        finally:
            cursor.close()

    # =========================================================
    # SECCIÓN 4: PERSISTENCIA DE HISTORIAL EN POSTGRESQL
    # =========================================================

    def guardar_historial_db(self, db_conn):
        """
        Guarda el historial de matches de esta sesión en la tabla
        'historial_aprendizaje'. Al final, también guarda los pesos actualizados.

        Se llama desde el endpoint /api/registrar-resultado de app.py.
        """
        cursor = db_conn.cursor()

        for registro in self.historial_matches:
            try:
                cursor.execute("""
                    INSERT INTO historial_aprendizaje (
                        match_id, estudiante_id, empresa_id, resultado, caracteristicas
                    ) VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (
                    registro.get('match_id'),
                    registro['estudiante'].get('id'),
                    registro['empresa'].get('id'),
                    registro['resultado'],
                    json.dumps({
                        'carrera':     registro['estudiante'].get('carrera'),
                        'universidad': registro['estudiante'].get('universidad'),
                        'habilidades': registro['estudiante'].get('habilidades', []),
                        'score_match': registro.get('score_match')
                    })
                ))
            except Exception as e:
                print(f"⚠️  Error guardando registro de historial: {e}")

        db_conn.commit()
        cursor.close()

        # IMPORTANTE: después de guardar el historial, persistimos los pesos
        # para que el aprendizaje de esta sesión no se pierda
        self.guardar_pesos_db(db_conn)

    def cargar_historial_desde_db(self, db_conn):
        """
        Carga el historial de casos exitosos desde PostgreSQL y
        reconstruye los patrones en memoria.

        Esto es necesario porque predecir_probabilidad_exito() y
        recomendar_mejoras_estudiante() trabajan con self.patrones_exito,
        que vive en memoria y se pierde al reiniciar.
        """
        cursor = db_conn.cursor()

        try:
            # Solo cargamos los casos exitosos (contratados) para reconstruir patrones
            cursor.execute("""
                SELECT ha.*,
                       e.carrera, e.universidad, e.habilidades,
                       e.meses_experiencia, e.promedio,
                       emp.area
                FROM historial_aprendizaje ha
                JOIN estudiantes e   ON ha.estudiante_id = e.id
                JOIN empresas emp    ON ha.empresa_id    = emp.id
                WHERE ha.resultado = 'contratado'
            """)
            registros = cursor.fetchall()

            # Reconstruimos los patrones como si acabaran de registrarse
            for r in registros:
                match_data = {
                    'match_id':    r['id'],
                    'score_final': 0,  # No guardamos el score en historial
                    'estudiante': {
                        'id':                r['estudiante_id'],
                        'carrera':           r['carrera'],
                        'universidad':       r['universidad'],
                        'habilidades':       r['habilidades'] or [],
                        'meses_experiencia': r['meses_experiencia'],
                        'promedio':          r['promedio']
                    },
                    'empresa': {
                        'id':   r['empresa_id'],
                        'area': r['area']
                    }
                }
                # Reutilizamos el mismo método que cuando se registra en tiempo real
                self._analizar_patron_exitoso(match_data)

            print(f"✅ {len(registros)} casos exitosos cargados desde BD")

        except Exception as e:
            print(f"⚠️  Error cargando historial: {e}")
        finally:
            cursor.close()

    def inicializar_desde_db(self, db_conn):
        """
        Método principal que se llama al arrancar la API (desde app.py).

        Orden de inicialización:
        1. Carga pesos guardados (para tener pesos correctos de inmediato)
        2. Carga historial para reconstruir patrones en memoria
           (necesario para predicciones y recomendaciones)
        """
        print("🧠 Inicializando LearningSystem desde BD...")
        self.cargar_pesos_db(db_conn)           # Paso 1: recuperar pesos
        self.cargar_historial_desde_db(db_conn) # Paso 2: reconstruir patrones
        print(f"🧠 LearningSystem listo — {len(self.pesos_aprendidos)} áreas con pesos persistidos")

    # =========================================================
    # SECCIÓN 5: INSIGHTS Y RECOMENDACIONES
    # =========================================================

    def obtener_insights_area(self, area):
        """
        Retorna información útil sobre qué perfil busca una área específica,
        basada en los patrones de contratados anteriores.
        """
        if area not in self.pesos_aprendidos:
            return {
                'disponible': False,
                'mensaje':    f"Sin suficientes datos para '{area}' (mínimo {self.min_datos_aprendizaje} casos)"
            }

        metadata = self.pesos_aprendidos[area]['metadata']
        return {
            'disponible':                  True,
            'area':                        area,
            'n_casos_exitosos':            metadata['n_muestras'],
            'experiencia_promedio_meses':  metadata['exp_promedio'],
            'universidades_top':           metadata['top_universidades'],
            'promedio_academico_esperado': metadata['promedio_academico'],
            'habilidades_mas_valoradas':   metadata['habilidades_clave'],
            'recomendacion':               self._generar_recomendacion_area(metadata)
        }

    def _generar_recomendacion_area(self, metadata):
        """Genera un texto de recomendación basado en la metadata del área."""
        exp      = metadata['exp_promedio']
        promedio = metadata['promedio_academico']
        recs     = []

        if exp > 12:
            recs.append(f"Esta área valora la experiencia (promedio {exp:.0f} meses entre contratados)")
        elif exp < 6:
            recs.append("Ideal para perfiles junior — no requieren mucha experiencia")

        if promedio >= 15:
            recs.append(f"Se espera buen rendimiento académico (>{promedio:.1f})")

        if metadata['habilidades_clave']:
            top = list(metadata['habilidades_clave'].keys())[0]
            recs.append(f"Habilidad más valorada entre contratados: {top}")

        return " | ".join(recs) if recs else "Perfil competitivo general"

    def recomendar_mejoras_estudiante(self, estudiante, area_objetivo):
        """
        Compara el perfil del estudiante contra los contratados en el área
        y genera recomendaciones personalizadas.

        Args:
            estudiante (dict): Datos del estudiante desde la BD
            area_objetivo (str): Área a la que quiere postular

        Returns:
            list: Lista de recomendaciones con emojis para mejor lectura
        """
        # Necesitamos al menos 3 casos para dar recomendaciones útiles
        if area_objetivo not in self.patrones_exito or len(self.patrones_exito[area_objetivo]) < 3:
            return ["No hay suficientes datos para recomendaciones específicas en esta área"]

        metadata = self.pesos_aprendidos.get(area_objetivo, {}).get('metadata', {})
        recs     = []

        # 1. Comparar experiencia
        exp_esperada = metadata.get('exp_promedio', 0)
        exp_actual   = int(estudiante.get('meses_experiencia') or 0)
        if exp_actual < exp_esperada - 6:
            recs.append(
                f"💼 Adquiere {int(exp_esperada - exp_actual)} meses más de experiencia "
                f"(promedio de contratados: {exp_esperada:.0f} meses)"
            )

        # 2. Comparar habilidades
        habs_val      = set(metadata.get('habilidades_clave', {}).keys())
        habs_actuales = set(estudiante.get('habilidades', []))
        faltantes     = list(habs_val - habs_actuales)[:3]
        if faltantes:
            recs.append(f"🎯 Aprende estas habilidades valoradas en el área: {', '.join(faltantes)}")

        # 3. Comparar promedio académico
        prom_esp = metadata.get('promedio_academico', 0)
        prom_act = float(estudiante.get('promedio') or 0)
        if prom_act and prom_act < prom_esp - 1:
            recs.append(f"📚 Mejora tu promedio académico (promedio de contratados: >{prom_esp:.1f})")

        # 4. Comparar universidad
        top_unis = metadata.get('top_universidades', [])
        if estudiante.get('universidad') not in top_unis and top_unis:
            recs.append(
                f"🎓 Destaca otros aspectos de tu perfil "
                f"(universidades frecuentes en contratados: {', '.join(top_unis[:2])})"
            )

        return recs if recs else ["✅ Tu perfil está bien alineado con los contratados en esta área"]

    def obtener_estadisticas_generales(self):
        """
        Retorna un resumen del estado actual del sistema de aprendizaje.
        Se usa en el endpoint /api/aprendizaje/estadisticas de app.py.
        """
        total = len(self.historial_matches)

        # Si no hay historial en memoria (sesión nueva o primer arranque)
        if total == 0:
            return {
                'mensaje':               'No hay datos en memoria en esta sesión',
                'areas_con_pesos_en_bd': len(self.pesos_aprendidos),
                'nota':                  'Los pesos sí están cargados desde BD si existen'
            }

        # Contar resultados por tipo
        resultados = defaultdict(int)
        for m in self.historial_matches:
            resultados[m['resultado']] += 1

        return {
            'total_registros':         total,
            'contratados':             resultados.get('contratado', 0),
            'tasa_exito_global':       round(resultados.get('contratado', 0) / total * 100, 2),
            'areas_con_aprendizaje':   len(self.patrones_exito),
            'areas_con_pesos_en_bd':   len(self.pesos_aprendidos),
            'total_patrones_exitosos': sum(len(p) for p in self.patrones_exito.values()),
            'distribucion_resultados': dict(resultados)
        }