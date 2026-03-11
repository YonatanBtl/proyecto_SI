"""
Agente 2: NLP Analyzer
Analiza CVs y extrae información estructurada usando NLP real con spaCy
"""

import re
import spacy
import PyPDF2
import docx
from datetime import datetime


class NLPAnalyzer:
    """
    Agente inteligente para procesar CVs en PDF, DOCX o texto plano.
    Combina spaCy (NER) + regex para extraer información estructurada.
    """

    def __init__(self):
        # Cargar modelo spaCy para español
        try:
            self.nlp = spacy.load("es_core_news_sm")
            print("Modelo spaCy cargado correctamente")
        except Exception:
            print("spaCy no encontrado. Ejecuta: python -m spacy download es_core_news_sm")
            self.nlp = None

        # Base de conocimiento de habilidades técnicas
        self.habilidades_tech = {
            # Lenguajes de programación
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'ruby',
            'php', 'swift', 'kotlin', 'go', 'rust', 'r', 'matlab', 'scala',
            # Frameworks y librerías
            'react', 'angular', 'vue', 'django', 'flask', 'spring', 'laravel',
            'node.js', 'nodejs', 'express', 'fastapi', '.net', 'tensorflow', 'pytorch',
            # Bases de datos
            'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'oracle',
            'sqlite', 'cassandra', 'elasticsearch',
            # Cloud y DevOps
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins',
            'git', 'gitlab', 'github', 'terraform', 'ansible',
            # Data Science / ML
            'machine learning', 'deep learning', 'data science', 'pandas',
            'numpy', 'scikit-learn', 'tableau', 'power bi',
            # Marketing
            'google ads', 'facebook ads', 'seo', 'sem', 'social media',
            'google analytics', 'mailchimp', 'hubspot',
            # Diseño
            'photoshop', 'illustrator', 'figma', 'sketch', 'adobe xd',
            'canva', 'indesign',
            # Office
            'excel', 'word', 'powerpoint', 'outlook'
        }

        # Patrones de nivel de inglés
        self.patrones_ingles = {
            'Avanzado':   ['fluent', 'advanced', 'c1', 'c2', 'proficient', 'native', 'avanzado'],
            'Intermedio': ['intermediate', 'b2', 'b1', 'conversational', 'intermedio'],
            'Basico':     ['basic', 'a2', 'a1', 'beginner', 'elementary', 'básico', 'basico']
        }

        # Meses en español para calcular experiencia con precisión
        self.meses_es = {
            'enero': 1, 'febrero': 2, 'marzo': 3, 'abril': 4,
            'mayo': 5, 'junio': 6, 'julio': 7, 'agosto': 8,
            'septiembre': 9, 'octubre': 10, 'noviembre': 11, 'diciembre': 12,
            'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'ago': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dic': 12
        }

        # Universidades peruanas
        self.universidades_peru = {
            'PUCP':  ['pucp', 'pontificia universidad católica', 'pontificia universidad catoli', 'católica del perú'],
            'UNI':   ['uni', 'universidad nacional de ingeniería', 'nacional de ingenieria'],
            'UNMSM': ['unmsm', 'san marcos', 'universidad nacional mayor'],
            'ULIMA': ['ulima', 'universidad de lima'],
            'UP':    ['universidad del pacífico', 'universidad del pacifico'],
            'UPC':   ['upc', 'ciencias aplicadas'],
            'USIL':  ['usil', 'san ignacio de loyola'],
            'UTP':   ['utp', 'universidad tecnológica del perú', 'tecnologica del peru']
        }

    # =========================================================
    # MÉTODO PRINCIPAL
    # =========================================================

    def analizar_cv_completo(self, texto_cv):
        """
        Análisis completo del CV usando spaCy + regex.
        Args:
            texto_cv (str): Texto extraído del CV
        Returns:
            dict: Información estructurada del CV
        """
        if not texto_cv or not texto_cv.strip():
            return {'error': 'El texto del CV está vacío'}

        texto_lower = texto_cv.lower()

        # spaCy: extraer entidades nombradas (personas, orgs, fechas, lugares)
        entidades = self._extraer_entidades_spacy(texto_cv)

        # Extracción de datos
        nombre            = self._extraer_nombre(texto_cv, entidades)
        habilidades       = self._extraer_habilidades(texto_lower)
        email             = self._extraer_email(texto_cv)
        telefono          = self._extraer_telefono(texto_cv)
        meses_experiencia = self._calcular_experiencia(texto_cv)
        nivel_ingles      = self._detectar_nivel_ingles(texto_lower)
        universidad       = self._extraer_universidad(texto_cv, entidades)
        calidad_cv        = self._evaluar_calidad_cv(texto_cv, habilidades)
        completitud       = self._calcular_completitud(email, telefono, habilidades, meses_experiencia)

        cargo = self._extraer_cargo(texto_cv, nombre)

        return {
            'nombre':                    nombre,
            'cargo':                     cargo,
            'email':                     email,
            'telefono':                  telefono,
            'universidad':               universidad,
            'habilidades':               sorted(list(habilidades)),
            'num_habilidades':           len(habilidades),
            'meses_experiencia':         meses_experiencia,
            'nivel_ingles':              nivel_ingles,
            'calidad_cv':                calidad_cv,
            'completitud':               completitud,
            'organizaciones_detectadas': entidades.get('organizaciones', []),
            'recomendaciones':           self._generar_recomendaciones(habilidades, email, telefono, calidad_cv)
        }

    # =========================================================
    # spaCy: EXTRACCIÓN DE ENTIDADES NOMBRADAS (NER)
    # =========================================================

    def _extraer_entidades_spacy(self, texto):
        """
        Usa spaCy NER para detectar personas, organizaciones, fechas y lugares.
        Si spaCy no está disponible retorna dict vacío.
        """
        if not self.nlp:
            return {'personas': [], 'organizaciones': [], 'fechas': [], 'lugares': []}

        # Limitar texto para evitar timeout en CVs muy largos
        doc = self.nlp(texto[:50_000])

        entidades = {
            'personas':       [],
            'organizaciones': [],
            'fechas':         [],
            'lugares':        []
        }

        mapa_etiquetas = {
            'PER':  'personas',
            'ORG':  'organizaciones',
            'DATE': 'fechas',
            'LOC':  'lugares',
            'GPE':  'lugares'
        }

        falsas_organizaciones = {
            'idiomas', 'tecnicas', 'técnicas', 'ci', 'perfil', 'educacion',
            'educación', 'experiencia', 'habilidades', 'proyectos', 'objetivo',
            'certificaciones', 'miembro', 'apasionado', 'visualizacion',
            'visualización', 'pandas', 'numpy', 'scala', 'python', 'java',
            'github', 'gitlab', 'linux', 'windows', 'resumen', 'logros',
            'referencias', 'actividades', 'voluntariado', 'intereses'
        }

        vistas = set()
        for ent in doc.ents:
            clave     = mapa_etiquetas.get(ent.label_)
            texto_ent = ent.text.strip()

            if not clave or not texto_ent or texto_ent in vistas:
                continue

            # Filtros para organizaciones falsas
            if clave == 'organizaciones':
                texto_lower = texto_ent.lower()

                # Ignorar palabras muy cortas (menos de 3 caracteres)
                if len(texto_ent) < 3:
                    continue

                # Ignorar secciones del CV y librerías conocidas
                if texto_lower in falsas_organizaciones:
                    continue

                # Ignorar si es completamente en mayúsculas y corto
                # (son titulos de sección: "IDIOMAS", "CI", "TECNICAS")
                if texto_ent.isupper() and len(texto_ent) <= 12:
                    continue

                # Ignorar si no tiene al menos 2 caracteres alfabéticos seguidos
                if not re.search(r'[a-záéíóúñA-ZÁÉÍÓÚÑ]{2,}', texto_ent):
                    continue

            entidades[clave].append(texto_ent)
            vistas.add(texto_ent)

        return entidades

    # =========================================================
    # EXTRAER NOMBRE DEL CANDIDATO
    # =========================================================

    def _extraer_nombre(self, texto, entidades_spacy):
        """
        Extrae el nombre del candidato.
        Prioridad:
          1) spaCy PER limpio (quita cargos pegados)
          2) Línea en mayúsculas de 2-4 palabras (ej: "EDGAR QUISPE")
          3) Heurística en primeras líneas con capitalización normal

        Casos que maneja:
          - "Carlos Mendoza QuispeDesarrollador" → "Carlos Mendoza Quispe"
          - "EDGAR QUISPE" (todo mayúsculas en DOCX con columnas) → "Edgar Quispe"
          - Nombre en posición no estándar (DOCX con sidebar lateral)
        """
        # Palabras de cargo que NO son parte del nombre
        palabras_cargo = {
            'desarrollador', 'ingeniero', 'analista', 'diseñador', 'gerente',
            'coordinador', 'director', 'jefe', 'asistente', 'practicante',
            'estudiante', 'consultor', 'programador', 'arquitecto', 'especialista',
            'developer', 'engineer', 'manager', 'designer', 'analyst',
            'software', 'senior', 'junior', 'fullstack', 'frontend', 'backend',
            'contáctame', 'contactame', 'resumen', 'educación', 'educacion',
            'experiencia', 'habilidades', 'idiomas', 'certificaciones', 'herramientas'
        }

        # 1. spaCy PER: limpiar cargos pegados al nombre
        personas = entidades_spacy.get('personas', [])
        if personas:
            candidato = personas[0].strip()
            partes = re.findall(r'[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+', candidato)
            nombre_limpio = []
            for parte in partes:
                if parte.lower() in palabras_cargo:
                    break
                nombre_limpio.append(parte)
            if len(nombre_limpio) >= 2:
                return ' '.join(nombre_limpio)

        # Buscar en TODAS las líneas del texto (DOCX con columnas tiene el nombre en posición variable)
        lineas = [l.strip() for l in texto.split('\n') if l.strip()]

        # 2. Buscar línea completamente en MAYÚSCULAS que parezca nombre (2-4 palabras)
        # Ej: "EDGAR QUISPE", "CARLOS MENDOZA QUISPE"
        patron_mayus = re.compile(r'^[A-ZÁÉÍÓÚÑ]{2,}(?: [A-ZÁÉÍÓÚÑ]{2,}){1,3}$')
        for linea in lineas:
            if patron_mayus.match(linea):
                # Verificar que no sea un título de sección
                if linea.lower() not in palabras_cargo and len(linea) < 50:
                    # Convertir a Title Case: "EDGAR QUISPE" → "Edgar Quispe"
                    return linea.title()

        # 3. Heurística: 2-4 palabras con capitalización normal en primeras 8 líneas
        patron_normal = re.compile(r'^[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?: [A-ZÁÉÍÓÚÑ][a-záéíóúñ]+){1,3}$')
        for linea in lineas[:8]:
            if any(p in linea.lower() for p in palabras_cargo):
                continue
            if patron_normal.match(linea):
                return linea

        return 'No detectado'

    # =========================================================
    # EXTRAER CARGO DEL CANDIDATO
    # =========================================================

    def _extraer_cargo(self, texto, nombre_detectado):
        """
        Extrae el cargo/título profesional del candidato.

        Estrategia: buscar la línea inmediatamente después del nombre.
        En la mayoría de CVs bien estructurados el cargo va justo debajo:
          Carlos Mendoza Quispe
          Desarrollador Full Stack   ← esto extraemos

        Si no encuentra nada confiable, retorna None para no mostrar nada.
        """
        if not nombre_detectado or nombre_detectado == 'No detectado':
            return None

        # Palabras que indican que es un cargo (no una sección ni dato de contacto)
        palabras_cargo = {
            'desarrollador', 'ingeniero', 'analista', 'diseñador', 'gerente',
            'coordinador', 'director', 'jefe', 'asistente', 'practicante',
            'consultor', 'programador', 'arquitecto', 'especialista', 'técnico',
            'developer', 'engineer', 'manager', 'designer', 'analyst', 'architect',
            'scientist', 'lead', 'senior', 'junior', 'fullstack', 'frontend',
            'backend', 'devops', 'data', 'bi', 'business', 'intelligence',
            'marketing', 'ventas', 'finanzas', 'contable', 'administrativo',
            'sistemas', 'redes', 'seguridad', 'soporte', 'qa', 'tester', 'data','Analista'
        }

        # Palabras que indican que NO es un cargo (secciones, datos de contacto)
        no_es_cargo = {
            'email', 'teléfono', 'telefono', 'linkedin', 'github', 'http',
            'www', '@', 'lima', 'perú', 'peru', 'chorrillos', 'miraflores',
            'educación', 'educacion', 'experiencia', 'habilidades', 'idiomas',
            'certificaciones', 'proyectos', 'contacto', 'contáctame', 'perfil',
            'resumen', 'objetivo', 'referencias', 'herramientas'
        }

        lineas = [l.strip() for l in texto.split('\n') if l.strip()]

        # Buscar el nombre en las líneas y tomar la siguiente línea válida
        nombre_lower = nombre_detectado.lower()
        for i, linea in enumerate(lineas):
            # ¿Esta línea contiene el nombre detectado?
            if nombre_lower in linea.lower() or linea.upper() == nombre_detectado.upper():
                # Revisar las siguientes 3 líneas buscando el cargo
                for j in range(i + 1, min(i + 4, len(lineas))):
                    candidato = lineas[j].strip()
                    candidato_lower = candidato.lower()

                    # Ignorar líneas muy largas (párrafos, no cargos)
                    if len(candidato) > 60:
                        continue

                    # Ignorar líneas con datos de contacto o secciones
                    if any(p in candidato_lower for p in no_es_cargo):
                        continue

                    # Ignorar líneas con números (teléfonos, fechas)
                    if re.search(r'\d{4,}', candidato):
                        continue

                    # ¿Contiene al menos una palabra de cargo?
                    palabras = candidato_lower.split()
                    if any(p in palabras_cargo for p in palabras):
                        # Limpiar y retornar
                        return candidato.strip()

        return None

    # =========================================================
    # EXTRAER HABILIDADES TÉCNICAS
    # =========================================================

    def _extraer_habilidades(self, texto_lower):
        """
        Extrae habilidades técnicas del diccionario.
        Usa word boundary para habilidades cortas (evita falsos positivos).
        """
        habilidades_encontradas = set()

        for habilidad in self.habilidades_tech:
            if len(habilidad) <= 2:
                # Para 'r', 'go', etc. — verificar que sea palabra completa
                patron = r'\b' + re.escape(habilidad) + r'\b'
                if re.search(patron, texto_lower):
                    habilidades_encontradas.add(habilidad)
            else:
                if habilidad in texto_lower:
                    habilidades_encontradas.add(habilidad)

        return habilidades_encontradas

    # =========================================================
    # EXTRAER CONTACTO
    # =========================================================

    def _extraer_email(self, texto):
        """Extrae email usando regex."""
        patron = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
        emails = re.findall(patron, texto)
        return emails[0] if emails else None

    def _extraer_telefono(self, texto):
        """Extrae teléfono peruano usando regex."""
        patrones = [
            r'\+?51\s?9\d{8}',
            r'\b9\d{8}\b',
            r'\d{3}[-\s]?\d{3}[-\s]?\d{3}'
        ]
        for patron in patrones:
            match = re.search(patron, texto)
            if match:
                return match.group(0)
        return None

    # =========================================================
    # CALCULAR EXPERIENCIA (con meses reales)
    # =========================================================

    def _calcular_experiencia(self, texto):
        """
        Calcula meses de experiencia detectando rangos de fechas.
        Soporta:
          - "2020 - 2023"
          - "Ene 2020 - Mar 2022"
          - "enero 2021 - actualidad"
        """
        texto_lower = texto.lower()
        total_meses = 0
        año_actual  = datetime.now().year
        mes_actual  = datetime.now().month

        # Patrón 1: mes año - mes año  (ej: "ene 2020 - mar 2022")
        meses_patron = '|'.join(self.meses_es.keys())
        patron_mes_año = (
            rf'({meses_patron})\.?\s+(\d{{4}})\s*[-–]\s*'
            rf'({meses_patron}|presente|actualidad|actual)\.?\s*(\d{{4}})?'
        )
        for m in re.finditer(patron_mes_año, texto_lower):
            mes_ini     = self.meses_es.get(m.group(1), 1)
            año_ini     = int(m.group(2))
            fin_str     = m.group(3)
            año_fin_str = m.group(4)

            if fin_str in ('presente', 'actualidad', 'actual'):
                mes_fin = mes_actual
                año_fin = año_actual
            else:
                mes_fin = self.meses_es.get(fin_str, mes_actual)
                año_fin = int(año_fin_str) if año_fin_str else año_actual

            meses = (año_fin - año_ini) * 12 + (mes_fin - mes_ini)
            if 0 < meses < 600:
                total_meses += meses

        # Patrón 2: MM/YYYY – MM/YYYY  (ej: "09/2023 – 09/2024", "03/2022-11/2022")
        # Muy común en CVs peruanos con formato numérico de fecha
        patron_mmyyyy = (
            r'(\d{1,2})/(\d{4})\s*[-–]\s*'
            r'(\d{1,2})/(\d{4}|presente|actualidad|actual)'
        )
        for m in re.finditer(patron_mmyyyy, texto_lower):
            mes_ini = int(m.group(1))
            año_ini = int(m.group(2))
            fin_str = m.group(4)
            if fin_str in ('presente', 'actualidad', 'actual'):
                mes_fin = mes_actual
                año_fin = año_actual
            else:
                mes_fin = int(m.group(3))
                año_fin = int(fin_str)
            meses = (año_fin - año_ini) * 12 + (mes_fin - mes_ini)
            if 0 < meses < 600:
                total_meses += meses

        # Patrón 3: año - año  (ej: "2020 - 2023") — fallback
        if total_meses == 0:
            patron_año = r'(\d{4})\s*[-–]\s*(\d{4}|presente|actualidad|actual)'
            for m in re.finditer(patron_año, texto_lower):
                año_ini = int(m.group(1))
                fin_str = m.group(2)
                año_fin = año_actual if fin_str in ('presente', 'actualidad', 'actual') else int(fin_str)
                meses   = (año_fin - año_ini) * 12
                if 0 < meses < 600:
                    total_meses += meses

        return total_meses

    # =========================================================
    # DETECTAR NIVEL DE INGLÉS
    # =========================================================

    def _detectar_nivel_ingles(self, texto_lower):
        """Detecta nivel de inglés mencionado en el CV."""
        for nivel, palabras in self.patrones_ingles.items():
            for palabra in palabras:
                if palabra in texto_lower:
                    return nivel
        return 'No especificado'

    # =========================================================
    # EXTRAER UNIVERSIDAD
    # =========================================================

    def _extraer_universidad(self, texto, entidades_spacy):
        """
        Extrae universidad.
        Prioridad: 1) diccionario  2) organizaciones detectadas por spaCy
        """
        texto_lower = texto.lower()

        for sigla, variantes in self.universidades_peru.items():
            for variante in variantes:
                if variante in texto_lower:
                    return sigla

        # Fallback: buscar entre organizaciones de spaCy
        for org in entidades_spacy.get('organizaciones', []):
            if 'universidad' in org.lower():
                return org

        return 'Otra'

    # =========================================================
    # EVALUAR CALIDAD DEL CV
    # =========================================================

    def _evaluar_calidad_cv(self, texto, habilidades):
        """Evalúa la calidad general del CV (0-100)."""
        score = 0

        # 1. Longitud apropiada (15 pts)
        longitud = len(texto)
        if 500 < longitud < 3000:
            score += 15
        elif 300 < longitud < 5000:
            score += 10
        else:
            score += 5

        # 2. Secciones clave presentes (30 pts)
        secciones = [
            'educación', 'educacion', 'experiencia', 'habilidades',
            'proyectos', 'certificaciones', 'idiomas', 'perfil', 'objetivo'
        ]
        texto_lower = texto.lower()
        encontradas = sum(1 for s in secciones if s in texto_lower)
        score += min(encontradas * 5, 30)

        # 3. Cantidad de habilidades (25 pts)
        n = len(habilidades)
        if n >= 8:
            score += 25
        elif n >= 5:
            score += 20
        elif n >= 3:
            score += 15
        else:
            score += 5

        # 4. Datos de contacto (15 pts)
        tiene_email    = bool(self._extraer_email(texto))
        tiene_telefono = bool(self._extraer_telefono(texto))
        if tiene_email and tiene_telefono:
            score += 15
        elif tiene_email or tiene_telefono:
            score += 8

        # 5. Estructura visual (15 pts)
        tiene_bullets = any(c in texto for c in ['•', '-', '*', '–'])
        tiene_fechas  = bool(re.search(r'\d{4}', texto))
        if tiene_bullets and tiene_fechas:
            score += 15
        elif tiene_bullets or tiene_fechas:
            score += 8

        return min(score, 100)

    # =========================================================
    # CALCULAR COMPLETITUD
    # =========================================================

    def _calcular_completitud(self, email, telefono, habilidades, experiencia):
        """Calcula qué tan completo está el perfil (0-100)."""
        completitud = 0
        if email:
            completitud += 25
        if telefono:
            completitud += 25
        if len(habilidades) >= 3:
            completitud += 30
        if experiencia > 0:
            completitud += 20
        return completitud

    # =========================================================
    # GENERAR RECOMENDACIONES
    # =========================================================

    def _generar_recomendaciones(self, habilidades, email, telefono, calidad_cv):
        """Genera recomendaciones personalizadas para mejorar el CV."""
        recomendaciones = []

        if not email:
            recomendaciones.append("Agrega tu email de contacto")
        if not telefono:
            recomendaciones.append("Agrega tu número de teléfono")
        if len(habilidades) < 5:
            recomendaciones.append("Agrega más habilidades técnicas (mínimo 5 recomendadas)")
        if calidad_cv < 50:
            recomendaciones.append("Mejora la estructura: agrega secciones claras (Educación, Experiencia, Habilidades)")
        elif calidad_cv < 70:
            recomendaciones.append("Considera agregar una sección de Proyectos o Certificaciones")

        if not recomendaciones:
            recomendaciones.append("Tu CV está bien estructurado")

        return recomendaciones

    # =========================================================
    # LEER ARCHIVOS (PDF / DOCX)
    # =========================================================

    def analizar_cv_desde_archivo(self, ruta_archivo):
        """
        Analiza un CV desde un archivo PDF o DOCX.

        Args:
            ruta_archivo (str): Ruta al archivo

        Returns:
            dict: Información extraída del CV
        """
        if ruta_archivo.endswith('.pdf'):
            texto = self._leer_pdf(ruta_archivo)
        elif ruta_archivo.endswith('.docx'):
            texto = self._leer_docx(ruta_archivo)
        else:
            raise ValueError("Formato no soportado. Usa PDF o DOCX.")

        if not texto.strip():
            return {
                'error': 'No se pudo extraer texto del archivo. '
                         'Verifica que el PDF no sea una imagen escaneada.'
            }

        return self.analizar_cv_completo(texto)

    def _leer_pdf(self, ruta_pdf):
        """Extrae texto de un PDF usando PyPDF2."""
        try:
            texto = ""
            with open(ruta_pdf, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    contenido = page.extract_text()
                    if contenido:
                        texto += contenido + "\n"
            return texto.strip()
        except Exception as e:
            print(f"Error leyendo PDF: {e}")
            return ""

    def _leer_docx(self, ruta_docx):
        """Extrae texto de un DOCX usando python-docx."""
        try:
            doc   = docx.Document(ruta_docx)
            texto = "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
            return texto.strip()
        except Exception as e:
            print(f"Error leyendo DOCX: {e}")
            return ""