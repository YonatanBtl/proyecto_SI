"""
Agente 1: Matching Engine
Calcula compatibilidad bidireccional entre estudiantes y empresas
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np


class MatchingEngine:
    """
    Agente inteligente para calcular matches entre estudiantes y empresas.
    Implementa matching bidireccional con pesos ajustables por área.
    """

    def __init__(self):
        self.vectorizer = TfidfVectorizer()
        self.peso_base = {
            'habilidades':    0.35,
            'experiencia':    0.25,
            'carrera':        0.20,
            'ubicacion':      0.10,
            'disponibilidad': 0.10
        }
        self.desglose_detallado = {}

    # =========================================================
    # HELPERS
    # =========================================================

    def _limpiar_dict(self, d):
        """
        Convierte valores Decimal y otros tipos no-nativos a float/int
        para evitar errores de operación con valores de PostgreSQL.
        """
        limpio = {}
        for k, v in d.items():
            try:
                # Decimal, Decimal128, etc.
                if hasattr(v, '__float__'):
                    limpio[k] = float(v)
                else:
                    limpio[k] = v
            except Exception:
                limpio[k] = v
        return limpio

    # =========================================================
    # MÉTODO PRINCIPAL
    # =========================================================

    def calcular_match_completo(self, estudiante, empresa):
        """
        Calcula matching BIDIRECCIONAL.

        Args:
            estudiante (dict): Datos del estudiante
            empresa (dict):    Datos de la empresa

        Returns:
            dict: Scores y análisis completo
        """
        # Limpiar tipos Decimal de PostgreSQL
        estudiante = self._limpiar_dict(estudiante)
        empresa    = self._limpiar_dict(empresa)

        score_requisitos = self._calcular_score_requisitos(estudiante, empresa)
        score_atractivo  = self._calcular_score_atractivo(estudiante, empresa)

        # Score final: 60% requisitos + 40% atractivo
        score_final = (score_requisitos * 0.6) + (score_atractivo * 0.4)

        insight        = self._generar_insight(score_requisitos, score_atractivo, estudiante, empresa)
        recomendacion  = self._generar_recomendacion(score_final)

        return {
            'score_estudiante_empresa': round(score_requisitos, 2),
            'score_empresa_estudiante': round(score_atractivo, 2),
            'score_final':             round(score_final, 2),
            'desglose':                self.desglose_detallado.copy(),
            'insight':                 insight,
            'recomendacion':           recomendacion
        }

    # =========================================================
    # SCORE REQUISITOS (estudiante → empresa)
    # =========================================================

    def _calcular_score_requisitos(self, estudiante, empresa):
        """Calcula qué tan bien cumple el estudiante los requisitos de la empresa."""

        # 1. Similitud de habilidades con TF-IDF + Cosine Similarity
        habilidades_est = " ".join(estudiante.get('habilidades') or [])
        requisitos_emp  = " ".join(empresa.get('requisitos') or [])

        if habilidades_est and requisitos_emp:
            try:
                vectores       = self.vectorizer.fit_transform([habilidades_est, requisitos_emp])
                similitud_hab  = float(cosine_similarity(vectores[0:1], vectores[1:2])[0][0])
            except Exception:
                similitud_hab = 0.0
        else:
            similitud_hab = 0.0

        # 2. Experiencia
        exp_estudiante = float(estudiante.get('meses_experiencia') or 0)
        exp_requerida  = float(empresa.get('experiencia_minima') or 0)
        score_exp = min(exp_estudiante / max(exp_requerida, 1), 1.0) if exp_requerida > 0 else 1.0

        # 3. Carrera
        carrera_estudiante = estudiante.get('carrera', '')
        carreras_aceptadas = empresa.get('carreras_aceptadas') or []
        score_carrera = 1.0 if carrera_estudiante in carreras_aceptadas else 0.3

        # 4. Ubicación
        lat_est = float(estudiante.get('lat') or 0)
        lng_est = float(estudiante.get('lng') or 0)
        lat_emp = float(empresa.get('lat') or 0)
        lng_emp = float(empresa.get('lng') or 0)

        if lat_est and lng_est and lat_emp and lng_emp:
            distancia      = np.sqrt((lat_est - lat_emp)**2 + (lng_est - lng_emp)**2)
            score_ubicacion = max(0.0, 1.0 - (distancia / 0.1))
        else:
            score_ubicacion = 0.5

        # 5. Disponibilidad
        horas_disp = float(estudiante.get('horas_disponibles') or 0)
        horas_req  = float(empresa.get('horas_requeridas') or 0)
        score_disp = 1.0 if horas_disp >= horas_req else 0.5

        # Pesos ajustados por área
        pesos = self._ajustar_pesos_por_area(empresa.get('area', ''))

        score = (
            similitud_hab   * pesos['habilidades'] +
            score_exp       * pesos['experiencia'] +
            score_carrera   * pesos['carrera'] +
            score_ubicacion * pesos['ubicacion'] +
            score_disp      * pesos['disponibilidad']
        ) * 100

        # Guardar desglose
        self.desglose_detallado = {
            'habilidades':    round(similitud_hab * 100, 1),
            'experiencia':    round(score_exp * 100, 1),
            'carrera':        round(score_carrera * 100, 1),
            'ubicacion':      round(score_ubicacion * 100, 1),
            'disponibilidad': round(score_disp * 100, 1)
        }

        return score

    # =========================================================
    # SCORE ATRACTIVO (empresa → estudiante)
    # =========================================================

    def _calcular_score_atractivo(self, estudiante, empresa):
        """Calcula qué tan atractivo es el candidato para la empresa."""

        universidad_tier = {
            'PUCP': 100, 'UNI': 100, 'UNMSM': 95,
            'ULIMA': 90, 'UP': 90,   'UPC': 85,
            'USIL': 80,  'UTP': 75,  'ESAN': 85
        }
        score_universidad = universidad_tier.get(
            estudiante.get('universidad', ''), 60
        )

        promedio      = float(estudiante.get('promedio') or 0)
        score_promedio = (promedio / 20.0) * 100 if promedio else 50.0

        num_proyectos  = len(estudiante.get('proyectos') or [])
        score_proyectos = min(num_proyectos * 20, 100)

        calidad_cv = float(estudiante.get('calidad_cv') or 50)

        if empresa.get('area') == 'Desarrollo Software':
            score = (
                score_universidad * 0.25 +
                score_promedio    * 0.20 +
                score_proyectos   * 0.40 +
                calidad_cv        * 0.15
            )
        else:
            score = (
                score_universidad * 0.35 +
                score_promedio    * 0.35 +
                score_proyectos   * 0.20 +
                calidad_cv        * 0.10
            )

        return score

    # =========================================================
    # PESOS POR ÁREA
    # =========================================================

    def _ajustar_pesos_por_area(self, area_empresa):
        """Ajusta los pesos de scoring según el área de la empresa."""
        if area_empresa == 'Desarrollo Software':
            return {'habilidades': 0.50, 'experiencia': 0.20,
                    'carrera': 0.15, 'ubicacion': 0.10, 'disponibilidad': 0.05}
        elif area_empresa == 'Marketing':
            return {'habilidades': 0.30, 'experiencia': 0.30,
                    'carrera': 0.20, 'ubicacion': 0.15, 'disponibilidad': 0.05}
        elif area_empresa == 'Finanzas':
            return {'habilidades': 0.25, 'experiencia': 0.25,
                    'carrera': 0.35, 'ubicacion': 0.10, 'disponibilidad': 0.05}
        elif area_empresa == 'Data Science':
            return {'habilidades': 0.50, 'experiencia': 0.20,
                    'carrera': 0.15, 'ubicacion': 0.05, 'disponibilidad': 0.10}
        else:
            return self.peso_base

    # =========================================================
    # INSIGHT Y RECOMENDACIÓN
    # =========================================================

    def _generar_insight(self, score_req, score_atr, estudiante, empresa):
        """Genera un insight personalizado del match."""
        nombre_empresa = empresa.get('nombre', 'esta empresa')

        if score_req >= 80 and score_atr >= 80:
            return f"¡Excelente match! Cumples perfectamente los requisitos y eres muy atractivo para {nombre_empresa}."
        elif score_req >= 80 and score_atr < 60:
            return "Cumples los requisitos técnicos, pero considera mejorar tu perfil académico (proyectos, promedio)."
        elif score_req < 60 and score_atr >= 80:
            requisitos = (empresa.get('requisitos') or [])[:3]
            return f"Eres un candidato atractivo, pero te faltan habilidades clave: {', '.join(requisitos)}."
        else:
            return "Match moderado. Puedes postular, pero prepárate para destacar otros aspectos de tu perfil."

    def _generar_recomendacion(self, score_final):
        """Genera recomendación de acción según el score final."""
        if score_final >= 75:
            return "ALTA - Postula inmediatamente"
        elif score_final >= 60:
            return "MEDIA - Considera postular"
        else:
            return "BAJA - Mejora tu perfil antes de postular"

    # =========================================================
    # CALCULAR MATCHES PARA UN ESTUDIANTE
    # =========================================================

    def calcular_matches_para_estudiante(self, estudiante_id, db_conn):
        """
        Calcula matches para un estudiante con todas las empresas activas.

        Args:
            estudiante_id (int): ID del estudiante
            db_conn: Conexión a PostgreSQL

        Returns:
            list: Lista de matches ordenados por score_final DESC
        """
        cursor = db_conn.cursor()

        cursor.execute("SELECT * FROM estudiantes WHERE id = %s", (estudiante_id,))
        estudiante = cursor.fetchone()

        if not estudiante:
            cursor.close()
            raise ValueError(f"Estudiante con ID {estudiante_id} no encontrado")

        cursor.execute("SELECT * FROM empresas WHERE activa = TRUE")
        empresas = cursor.fetchall()

        matches = []
        for empresa in empresas:
            match_result = self.calcular_match_completo(dict(estudiante), dict(empresa))
            matches.append({
                'empresa_id':     empresa['id'],
                'empresa_nombre': empresa['nombre'],
                'empresa_area':   empresa['area'],
                **match_result
            })

        matches.sort(key=lambda x: x['score_final'], reverse=True)
        cursor.close()

        return matches