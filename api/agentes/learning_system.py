"""
Agente 3: Learning System
Aprende de matches exitosos y mejora predicciones
"""

import numpy as np
import pandas as pd
from collections import defaultdict
from datetime import datetime
import json


class LearningSystem:
    """
    Agente de aprendizaje que mejora con el tiempo
    Analiza patrones de matches exitosos
    """
    
    def __init__(self):
        self.historial_matches = []
        self.patrones_exito = defaultdict(list)
        self.pesos_aprendidos = {}
        self.min_datos_aprendizaje = 5  # Mínimo de casos para aprender
    
    def registrar_resultado(self, match_data, resultado):
        """
        Registra el resultado de un match para aprendizaje
        
        Args:
            match_data (dict): Información del match
            resultado (str): 'contratado', 'rechazado', 'entrevista', 'sin_respuesta'
        """
        
        registro = {
            'match_id': match_data.get('match_id'),
            'estudiante': match_data.get('estudiante'),
            'empresa': match_data.get('empresa'),
            'score_match': match_data.get('score_final'),
            'resultado': resultado,
            'timestamp': datetime.now()
        }
        
        self.historial_matches.append(registro)
        
        # Si fue exitoso, analizar el patrón
        if resultado == 'contratado':
            self._analizar_patron_exitoso(match_data)
    
    def _analizar_patron_exitoso(self, match_data):
        """Identifica características comunes de matches exitosos"""
        
        estudiante = match_data.get('estudiante', {})
        empresa = match_data.get('empresa', {})
        area = empresa.get('area')
        
        patron = {
            'area_empresa': area,
            'carrera_estudiante': estudiante.get('carrera'),
            'universidad': estudiante.get('universidad'),
            'promedio': estudiante.get('promedio', 0),
            'habilidades_clave': estudiante.get('habilidades', []),
            'experiencia_meses': estudiante.get('meses_experiencia', 0),
            'score_match': match_data.get('score_final', 0)
        }
        
        self.patrones_exito[area].append(patron)
        
        # Si tenemos suficientes datos, recalcular pesos
        if len(self.patrones_exito[area]) >= self.min_datos_aprendizaje:
            self._actualizar_pesos_area(area)
    
    def _actualizar_pesos_area(self, area):
        """
        Recalcula pesos óptimos para un área basándose en éxitos históricos
        """
        
        patrones = self.patrones_exito[area]
        
        if len(patrones) < self.min_datos_aprendizaje:
            return
        
        # Convertir a DataFrame para análisis
        df = pd.DataFrame(patrones)
        
        # Analizar correlaciones
        # 1. Experiencia promedio de contratados
        exp_promedio = df['experiencia_meses'].mean()
        exp_std = df['experiencia_meses'].std()
        
        # 2. Universidades más exitosas
        top_universidades = df['universidad'].value_counts().head(3).index.tolist()
        
        # 3. Promedio académico promedio
        promedio_academico = df['promedio'].mean()
        
        # 4. Habilidades más valoradas
        todas_habilidades = [h for sublist in df['habilidades_clave'] for h in sublist]
        habilidades_frecuentes = pd.Series(todas_habilidades).value_counts().head(5).to_dict()
        
        # AJUSTAR PESOS dinámicamente
        nuevo_peso_exp = 0.25
        if exp_promedio > 12:  # Si los contratados tienen más de 1 año
            nuevo_peso_exp = 0.35
        elif exp_promedio < 6:  # Si tienen menos de 6 meses
            nuevo_peso_exp = 0.15
        
        self.pesos_aprendidos[area] = {
            'habilidades': 0.50 - (nuevo_peso_exp - 0.25),
            'experiencia': nuevo_peso_exp,
            'carrera': 0.15,
            'otros': 0.10,
            'metadata': {
                'exp_promedio': exp_promedio,
                'top_universidades': top_universidades,
                'promedio_academico': promedio_academico,
                'habilidades_clave': habilidades_frecuentes,
                'n_muestras': len(patrones)
            }
        }
        
        print(f"✅ Pesos actualizados para área '{area}' basado en {len(patrones)} casos exitosos")
    
    def predecir_probabilidad_exito(self, estudiante, empresa):
        """
        Predice la probabilidad de que un match sea exitoso
        basándose en patrones históricos
        
        Args:
            estudiante (dict): Datos del estudiante
            empresa (dict): Datos de la empresa
            
        Returns:
            float: Probabilidad 0-100
        """
        
        area = empresa.get('area')
        
        # Si no tenemos datos históricos, retornar probabilidad neutral
        if area not in self.patrones_exito or len(self.patrones_exito[area]) < self.min_datos_aprendizaje:
            return 50.0  # 50% probabilidad (sin información suficiente)
        
        patrones_similares = 0
        total_patrones = len(self.patrones_exito[area])
        
        for patron in self.patrones_exito[area]:
            similitud_total = 0
            
            # 1. COMPARAR CARRERA (30%)
            if patron['carrera_estudiante'] == estudiante.get('carrera'):
                similitud_total += 0.30
            
            # 2. COMPARAR UNIVERSIDAD (20%)
            if patron['universidad'] == estudiante.get('universidad'):
                similitud_total += 0.20
            
            # 3. COMPARAR HABILIDADES (30%)
            habilidades_estudiante = set(estudiante.get('habilidades', []))
            habilidades_patron = set(patron['habilidades_clave'])
            
            if habilidades_patron:
                interseccion = habilidades_estudiante & habilidades_patron
                similitud_hab = len(interseccion) / len(habilidades_patron)
                similitud_total += similitud_hab * 0.30
            
            # 4. COMPARAR EXPERIENCIA (20%)
            exp_estudiante = estudiante.get('meses_experiencia', 0)
            exp_patron = patron['experiencia_meses']
            
            diff_exp = abs(exp_estudiante - exp_patron)
            # Si la diferencia es menor a 6 meses, es similar
            if diff_exp <= 6:
                similitud_total += 0.20
            elif diff_exp <= 12:
                similitud_total += 0.10
            
            # Si la similitud total es alta (>60%), contar como patrón similar
            if similitud_total >= 0.6:
                patrones_similares += 1
        
        # Calcular probabilidad
        probabilidad = (patrones_similares / total_patrones) * 100
        
        # Ajustar por confianza (más datos = más confianza)
        factor_confianza = min(total_patrones / 20, 1.0)  # Máxima confianza con 20+ casos
        probabilidad_ajustada = 50 + (probabilidad - 50) * factor_confianza
        
        return round(probabilidad_ajustada, 2)
    
    def obtener_insights_area(self, area):
        """Obtiene insights de aprendizaje para un área específica"""
        
        if area not in self.pesos_aprendidos:
            return {
                'disponible': False,
                'mensaje': f"Aún no hay suficientes datos de '{area}' para generar insights"
            }
        
        metadata = self.pesos_aprendidos[area]['metadata']
        
        return {
            'disponible': True,
            'area': area,
            'n_casos_exitosos': metadata['n_muestras'],
            'experiencia_promedio_meses': round(metadata['exp_promedio'], 1),
            'universidades_top': metadata['top_universidades'],
            'promedio_academico_esperado': round(metadata['promedio_academico'], 2),
            'habilidades_mas_valoradas': metadata['habilidades_clave'],
            'recomendacion': self._generar_recomendacion_area(metadata)
        }
    
    def _generar_recomendacion_area(self, metadata):
        """Genera recomendación basada en metadata del área"""
        
        exp = metadata['exp_promedio']
        promedio = metadata['promedio_academico']
        
        recomendaciones = []
        
        if exp > 12:
            recomendaciones.append(f"Esta área valora la experiencia (promedio {exp:.0f} meses)")
        elif exp < 6:
            recomendaciones.append("Esta área es ideal para perfiles junior sin mucha experiencia")
        
        if promedio >= 15:
            recomendaciones.append(f"Se espera buen rendimiento académico (promedio >{promedio:.1f})")
        
        if metadata['habilidades_clave']:
            top_skill = list(metadata['habilidades_clave'].keys())[0]
            recomendaciones.append(f"Habilidad más valorada: {top_skill}")
        
        return " | ".join(recomendaciones) if recomendaciones else "Perfil competitivo general"
    
    def guardar_historial_db(self, db_conn):
        """Guarda historial en base de datos para persistencia"""
        
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
                        'carrera': registro['estudiante'].get('carrera'),
                        'universidad': registro['estudiante'].get('universidad'),
                        'habilidades': registro['estudiante'].get('habilidades', []),
                        'score_match': registro.get('score_match')
                    })
                ))
            except Exception as e:
                print(f"Error guardando registro: {e}")
                continue
        
        db_conn.commit()
        cursor.close()
    
    def cargar_historial_desde_db(self, db_conn):
        """Carga historial existente desde base de datos"""
        
        cursor = db_conn.cursor()
        
        cursor.execute("""
            SELECT ha.*, 
                   e.carrera, e.universidad, e.habilidades, e.meses_experiencia, e.promedio,
                   emp.area
            FROM historial_aprendizaje ha
            JOIN estudiantes e ON ha.estudiante_id = e.id
            JOIN empresas emp ON ha.empresa_id = emp.id
            WHERE ha.resultado = 'contratado'
        """)
        
        registros = cursor.fetchall()
        
        for registro in registros:
            match_data = {
                'match_id': registro['id'],
                'score_final': 0,  # No disponible en BD
                'estudiante': {
                    'id': registro['estudiante_id'],
                    'carrera': registro['carrera'],
                    'universidad': registro['universidad'],
                    'habilidades': registro['habilidades'],
                    'meses_experiencia': registro['meses_experiencia'],
                    'promedio': registro['promedio']
                },
                'empresa': {
                    'id': registro['empresa_id'],
                    'area': registro['area']
                }
            }
            
            self._analizar_patron_exitoso(match_data)
        
        cursor.close()
        
        print(f"✅ Cargados {len(registros)} casos exitosos desde BD")
    
    def obtener_estadisticas_generales(self):
        """Obtiene estadísticas generales del sistema de aprendizaje"""
        
        total_registros = len(self.historial_matches)
        
        if total_registros == 0:
            return {'mensaje': 'No hay datos históricos aún'}
        
        resultados_count = defaultdict(int)
        for match in self.historial_matches:
            resultados_count[match['resultado']] += 1
        
        areas_con_datos = len(self.patrones_exito)
        total_patrones_exitosos = sum(len(p) for p in self.patrones_exito.values())
        
        return {
            'total_registros': total_registros,
            'contratados': resultados_count.get('contratado', 0),
            'tasa_exito_global': round(resultados_count.get('contratado', 0) / total_registros * 100, 2),
            'areas_con_aprendizaje': areas_con_datos,
            'total_patrones_exitosos': total_patrones_exitosos,
            'distribucion_resultados': dict(resultados_count)
        }
    
    def recomendar_mejoras_estudiante(self, estudiante, area_objetivo):
        """
        Recomienda mejoras al estudiante basándose en patrones exitosos
        
        Args:
            estudiante (dict): Datos del estudiante
            area_objetivo (str): Área a la que quiere aplicar
            
        Returns:
            list: Lista de recomendaciones
        """
        
        if area_objetivo not in self.patrones_exito or len(self.patrones_exito[area_objetivo]) < 3:
            return ["No hay suficientes datos para generar recomendaciones específicas"]
        
        metadata = self.pesos_aprendidos.get(area_objetivo, {}).get('metadata', {})
        recomendaciones = []
        
        # 1. Experiencia
        exp_esperada = metadata.get('exp_promedio', 0)
        exp_actual = estudiante.get('meses_experiencia', 0)
        
        if exp_actual < exp_esperada - 6:
            diff_meses = int(exp_esperada - exp_actual)
            recomendaciones.append(
                f"💼 Adquiere {diff_meses} meses más de experiencia (promedio exitoso: {exp_esperada:.0f} meses)"
            )
        
        # 2. Habilidades
        habilidades_valoradas = set(metadata.get('habilidades_clave', {}).keys())
        habilidades_actuales = set(estudiante.get('habilidades', []))
        habilidades_faltantes = habilidades_valoradas - habilidades_actuales
        
        if habilidades_faltantes:
            top_3 = list(habilidades_faltantes)[:3]
            recomendaciones.append(
                f"🎯 Aprende estas habilidades valoradas: {', '.join(top_3)}"
            )
        
        # 3. Promedio
        promedio_esperado = metadata.get('promedio_academico', 0)
        promedio_actual = estudiante.get('promedio', 0)
        
        if promedio_actual and promedio_actual < promedio_esperado - 1:
            recomendaciones.append(
                f"📚 Mejora tu promedio académico (esperado: >{promedio_esperado:.1f})"
            )
        
        # 4. Universidad
        top_unis = metadata.get('top_universidades', [])
        universidad_actual = estudiante.get('universidad')
        
        if universidad_actual not in top_unis and top_unis:
            recomendaciones.append(
                f"🎓 Destaca otros aspectos (universidades comunes en contratados: {', '.join(top_unis[:2])})"
            )
        
        if not recomendaciones:
            recomendaciones.append("✅ Tu perfil está alineado con casos exitosos en esta área")
        
        return recomendaciones
