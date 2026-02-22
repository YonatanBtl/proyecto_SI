"""
Script para generar dataset ficticio
100 estudiantes + 50 empresas + postulaciones + matches + anomalías
Datos realistas para el sistema de prácticas preprofesionales
"""

import random
import csv
from datetime import datetime, timedelta

# Configuración
NUM_ESTUDIANTES = 100
NUM_EMPRESAS    = 50

# ============================================
# DATOS BASE - NOMBRES PERUANOS
# ============================================

NOMBRES = [
    "Juan", "María", "Carlos", "Ana", "Pedro", "Lucía", "Diego", "Sofía",
    "Luis", "Carmen", "José", "Isabel", "Miguel", "Patricia", "Jorge",
    "Laura", "Fernando", "Rosa", "Roberto", "Elena", "Ricardo", "Marta",
    "Antonio", "Paula", "Manuel", "Andrea", "Francisco", "Claudia",
    "Javier", "Daniela", "Raúl", "Mónica", "Andrés", "Valeria", "Sergio",
    "Gabriela", "Alberto", "Natalia", "Óscar", "Carolina", "Alejandro",
    "Mariana", "Guillermo", "Juliana", "Pablo", "Fernanda", "Eduardo",
    "Camila", "Enrique", "Beatriz", "Ximena", "Renzo", "Fiorella",
    "Giancarlo", "Alessandra", "Renato", "Kiara", "Bruno", "Ariana"
]

APELLIDOS = [
    "García", "Rodríguez", "Martínez", "López", "González", "Pérez",
    "Sánchez", "Ramírez", "Torres", "Flores", "Rivera", "Gómez",
    "Díaz", "Cruz", "Morales", "Reyes", "Jiménez", "Hernández",
    "Ruiz", "Mendoza", "Castro", "Vargas", "Romero", "Álvarez",
    "Chávez", "Vega", "Ramos", "Fernández", "Aguilar", "Medina",
    "Huanca", "Quispe", "Mamani", "Condori", "Ccallo", "Apaza",
    "Palomino", "Villanueva", "Carpio", "Lozano", "Paredes", "Salazar"
]

CARRERAS = [
    "Ing. Sistemas", "Ing. Software", "Ing. Industrial", "Ing. Civil",
    "Marketing", "Comunicaciones", "Administración", "Economía",
    "Diseño Gráfico", "Contabilidad", "Psicología", "Derecho"
]

UNIVERSIDADES = [
    "PUCP", "UNI", "UNMSM", "ULIMA", "UP", "UPC", "USIL", "UTP",
    "ESAN", "UAP"
]

HABILIDADES_POR_AREA = {
    "Tech":      ["python", "java", "javascript", "react", "angular", "vue", "node.js",
                  "sql", "mongodb", "postgresql", "git", "docker", "aws", "azure",
                  "machine learning", "data science", "django", "flask", "spring"],
    "Marketing": ["google ads", "facebook ads", "seo", "sem", "social media",
                  "google analytics", "mailchimp", "hubspot", "photoshop", "canva"],
    "Diseño":    ["photoshop", "illustrator", "figma", "sketch", "adobe xd",
                  "indesign", "canva"],
    "Negocios":  ["excel", "power bi", "tableau", "sql", "powerpoint", "sap", "erp"]
}

UBICACIONES_LIMA = [
    ("San Isidro",   -12.0931, -77.0465),
    ("Miraflores",   -12.1190, -77.0349),
    ("San Miguel",   -12.0773, -77.0924),
    ("Surco",        -12.1391, -77.0117),
    ("La Molina",    -12.0797, -76.9420),
    ("San Borja",    -12.0919, -77.0011),
    ("Jesús María",  -12.0725, -77.0484),
    ("Lince",        -12.0821, -77.0386),
    ("Magdalena",    -12.0907, -77.0747),
    ("Pueblo Libre", -12.0740, -77.0635),
    ("Barranco",     -12.1453, -77.0210),
    ("Chorrillos",   -12.1717, -77.0169),
]

# Empresas con nombres más realistas y peruanos
EMPRESAS_FICTICIAS = [
    # Desarrollo Software
    ("Pragma Tech Peru",        "Desarrollo Software", "Consultora tecnológica líder en transformación digital"),
    ("Nubelo Solutions SAC",    "Desarrollo Software", "Desarrollo de software a medida para empresas"),
    ("InkaCode Labs",           "Desarrollo Software", "Startup de desarrollo web y móvil"),
    ("Syscom Peru SAC",         "Desarrollo Software", "Sistemas informáticos empresariales"),
    ("Evol Software",           "Desarrollo Software", "Soluciones de software escalables"),
    ("Auna Digital",            "Desarrollo Software", "Tecnología aplicada al sector salud"),
    ("Interbank Tech",          "Desarrollo Software", "Área tecnológica del sector financiero"),
    ("Rimac Digital",           "Desarrollo Software", "Transformación digital en seguros"),
    ("BCP Tecnología",          "Desarrollo Software", "Equipo de innovación bancaria"),
    ("Yape Developers",         "Desarrollo Software", "Billetera digital y pagos móviles"),
    # Data Science
    ("Datum Inteligencia",      "Data Science", "Analítica de datos y business intelligence"),
    ("Analytics Peru",          "Data Science", "Ciencia de datos aplicada a negocios"),
    ("AI Andina SAC",           "Data Science", "Inteligencia artificial para LATAM"),
    ("Datalab Lima",            "Data Science", "Laboratorio de datos y machine learning"),
    ("Predictiva Analytics",    "Data Science", "Modelos predictivos para retail y finanzas"),
    # Marketing
    ("Circus Grey Lima",        "Marketing", "Agencia de publicidad y marketing integrado"),
    ("McCann Lima",             "Marketing", "Agencia de comunicación estratégica"),
    ("Havas Media Peru",        "Marketing", "Planificación y compra de medios"),
    ("Wunderman Thompson PE",   "Marketing", "Marketing digital y CRM"),
    ("Tribal DDB Peru",         "Marketing", "Agencia digital creativa"),
    ("Socialmood Agency",       "Marketing", "Especialistas en redes sociales"),
    # Diseño
    ("Infinito Estudio",        "Diseño UX/UI", "Estudio de diseño de experiencias digitales"),
    ("Fábrica de Ideas SAC",    "Diseño UX/UI", "UX research y diseño de producto"),
    ("Brandlive Peru",          "Diseño Gráfico", "Branding y diseño gráfico corporativo"),
    ("Creativa Estudio",        "Diseño Gráfico", "Diseño editorial y packaging"),
    # Finanzas
    ("Credicorp Capital",       "Finanzas", "Gestión de inversiones y banca de inversión"),
    ("Scotiabank Peru",         "Finanzas", "Prácticas en área de riesgos y finanzas"),
    ("Compartamos Financiera",  "Finanzas", "Microfinanzas e inclusión financiera"),
    ("Renta4 Perú",             "Finanzas", "Mercado de capitales y fondos de inversión"),
    ("Konfío Peru",             "Finanzas", "Fintech de crédito para pymes"),
    # Consultoría
    ("EY Peru",                 "Consultoría", "Auditoría consultoría y servicios empresariales"),
    ("Deloitte Lima",           "Consultoría", "Servicios de consultoría estratégica"),
    ("KPMG Perú",               "Consultoría", "Auditoría y consultoría de negocios"),
    ("McKinsey Lima",           "Consultoría", "Consultoría estratégica de alto nivel"),
    # RRHH
    ("Manpower Peru",           "Recursos Humanos", "Soluciones de empleo y talento"),
    ("Adecco Peru",             "Recursos Humanos", "Gestión de recursos humanos y outsourcing"),
    # Retail / E-commerce
    ("Falabella Peru Tech",     "E-commerce", "Tecnología para retail y e-commerce"),
    ("Ripley Digital",          "E-commerce", "Transformación digital del retail"),
    ("InRetail Analytics",      "E-commerce", "Analítica para retail moderno"),
    ("Linio Peru",              "E-commerce", "Marketplace y comercio electrónico"),
    # Logística
    ("DHL Supply Chain Peru",   "Logística", "Cadena de suministro y logística global"),
    ("Ransa Comercial",         "Logística", "Operador logístico líder en Perú"),
    ("GH Supply Peru",          "Logística", "Soluciones logísticas integrales"),
    # EdTech / Educación
    ("Crehana Business",        "EdTech", "Plataforma de aprendizaje online para empresas"),
    ("Aprende Institute",       "EdTech", "Educación tech online en LATAM"),
    ("Laboratoria Lima",        "EdTech", "Bootcamp de programación para mujeres"),
    # HealthTech
    ("Auna Salud Digital",      "HealthTech", "Salud digital e historias clínicas"),
    ("Sanna Digital",           "HealthTech", "Transformación digital en clínicas"),
    ("Telemed Peru",            "HealthTech", "Telemedicina y salud conectada"),
    # Telecomunicaciones
    ("Entel Tech Peru",         "Telecomunicaciones", "Innovación en telecomunicaciones"),
]

REQUISITOS_POR_AREA = {
    "Desarrollo Software": ["python", "javascript", "react", "sql", "git", "docker", "aws", "node.js", "django", "flask"],
    "Data Science":        ["python", "sql", "machine learning", "pandas", "tableau", "power bi", "numpy", "scikit-learn"],
    "Marketing":           ["google ads", "seo", "social media", "google analytics", "facebook ads", "canva", "hubspot"],
    "Diseño UX/UI":        ["figma", "photoshop", "sketch", "adobe xd", "illustrator"],
    "Diseño Gráfico":      ["photoshop", "illustrator", "indesign", "canva", "figma"],
    "Finanzas":            ["excel", "power bi", "sql", "tableau"],
    "Consultoría":         ["excel", "powerpoint", "sql", "power bi"],
    "Recursos Humanos":    ["excel", "power bi", "powerpoint"],
    "E-commerce":          ["excel", "google analytics", "social media", "sql"],
    "Logística":           ["excel", "erp", "sap", "sql"],
    "EdTech":              ["javascript", "react", "sql", "python"],
    "HealthTech":          ["python", "sql", "data science"],
    "Telecomunicaciones":  ["python", "sql", "aws", "docker"],
}

CARRERAS_POR_AREA = {
    "Desarrollo Software": ["Ing. Sistemas", "Ing. Software"],
    "Data Science":        ["Ing. Sistemas", "Ing. Industrial", "Economía"],
    "Marketing":           ["Marketing", "Comunicaciones", "Administración"],
    "Diseño UX/UI":        ["Diseño Gráfico", "Comunicaciones"],
    "Diseño Gráfico":      ["Diseño Gráfico", "Comunicaciones"],
    "Finanzas":            ["Economía", "Administración", "Contabilidad"],
    "Consultoría":         ["Administración", "Economía", "Ing. Industrial"],
    "Recursos Humanos":    ["Psicología", "Administración"],
    "E-commerce":          ["Marketing", "Administración", "Ing. Sistemas"],
    "Logística":           ["Ing. Industrial", "Administración"],
    "EdTech":              ["Ing. Sistemas", "Ing. Software"],
    "HealthTech":          ["Ing. Sistemas", "Ing. Software"],
    "Telecomunicaciones":  ["Ing. Sistemas", "Ing. Software", "Ing. Industrial"],
}

# ============================================
# GENERADOR DE ESTUDIANTES
# ============================================

def generar_estudiantes(num=100):
    estudiantes = []
    emails_usados = set()

    for i in range(1, num + 1):
        nombre    = random.choice(NOMBRES)
        apellido1 = random.choice(APELLIDOS)
        apellido2 = random.choice(APELLIDOS)
        nombre_completo = f"{nombre} {apellido1} {apellido2}"

        # Email único
        email = f"{nombre.lower()}.{apellido1.lower()}{random.randint(1, 99)}@gmail.com"
        while email in emails_usados:
            email = f"{nombre.lower()}.{apellido1.lower()}{random.randint(1, 999)}@gmail.com"
        emails_usados.add(email)

        carrera      = random.choice(CARRERAS)
        universidad  = random.choice(UNIVERSIDADES)
        promedio     = round(random.uniform(12.0, 18.5), 1)
        semestre     = random.randint(5, 10)

        # Habilidades según carrera
        if "Ing. Sistemas" in carrera or "Ing. Software" in carrera:
            pool = HABILIDADES_POR_AREA["Tech"]
        elif "Marketing" in carrera or "Comunicaciones" in carrera:
            pool = HABILIDADES_POR_AREA["Marketing"]
        elif "Diseño" in carrera:
            pool = HABILIDADES_POR_AREA["Diseño"]
        else:
            pool = HABILIDADES_POR_AREA["Negocios"]

        habilidades       = random.sample(pool, random.randint(3, min(8, len(pool))))
        meses_experiencia = random.choice([0, 0, 3, 6, 6, 12, 12, 18, 24, 36])
        nivel_ingles      = random.choice(["Basico", "Basico", "Intermedio", "Intermedio", "Avanzado"])
        num_proyectos     = random.randint(0, 5)
        proyectos         = [f"Proyecto{j+1}" for j in range(num_proyectos)]
        ubicacion, lat, lng = random.choice(UBICACIONES_LIMA)
        horas_disponibles = random.choice([20, 25, 30, 35, 40])
        telefono          = f"9{random.randint(10000000, 99999999)}"
        calidad_cv        = random.randint(40, 100)

        completitud = 0
        if email:                       completitud += 25
        if telefono:                    completitud += 25
        if len(habilidades) >= 3:       completitud += 30
        if meses_experiencia > 0:       completitud += 20

        # Fecha registro: últimos 90 días
        dias_atras = random.randint(1, 90)
        fecha_registro = (datetime.now() - timedelta(days=dias_atras)).strftime("%Y-%m-%d %H:%M:%S")

        estudiantes.append({
            'nombre':            nombre_completo,
            'email':             email,
            'telefono':          telefono,
            'carrera':           carrera,
            'universidad':       universidad,
            'promedio':          promedio,
            'semestre':          semestre,
            'habilidades':       '|'.join(habilidades),
            'meses_experiencia': meses_experiencia,
            'nivel_ingles':      nivel_ingles,
            'proyectos':         '|'.join(proyectos),
            'ubicacion':         ubicacion,
            'lat':               lat,
            'lng':               lng,
            'horas_disponibles': horas_disponibles,
            'calidad_cv':        calidad_cv,
            'completitud':       completitud,
            'fecha_registro':    fecha_registro,
        })

    return estudiantes


# ============================================
# GENERADOR DE EMPRESAS
# ============================================

def generar_empresas(num=50):
    empresas = []

    for nombre, area, descripcion in EMPRESAS_FICTICIAS[:num]:
        base_req  = REQUISITOS_POR_AREA.get(area, ["excel"])
        requisitos = random.sample(base_req, random.randint(2, min(5, len(base_req))))
        carreras   = CARRERAS_POR_AREA.get(area, ["Administración"])

        exp_minima       = random.choice([0, 0, 3, 6, 12])
        horas_requeridas = random.choice([20, 25, 30, 35])

        if area in ["Desarrollo Software", "Data Science", "HealthTech", "EdTech", "Telecomunicaciones"]:
            salario = random.randint(1200, 2500)
        elif area in ["Finanzas", "Consultoría"]:
            salario = random.randint(1000, 2000)
        else:
            salario = random.randint(800, 1500)

        ubicacion, lat, lng = random.choice(UBICACIONES_LIMA)
        modalidad   = random.choice(["presencial", "remoto", "remoto", "hibrido", "hibrido"])
        dias        = random.randint(30, 120)
        fecha_limite = (datetime.now() + timedelta(days=dias)).strftime("%Y-%m-%d")

        empresas.append({
            'nombre':              nombre,
            'area':                area,
            'descripcion':         descripcion,
            'requisitos':          '|'.join(requisitos),
            'carreras_aceptadas':  '|'.join(carreras),
            'experiencia_minima':  exp_minima,
            'horas_requeridas':    horas_requeridas,
            'salario':             salario,
            'ubicacion':           ubicacion,
            'lat':                 lat,
            'lng':                 lng,
            'modalidad':           modalidad,
            'tipo':                'practica',
            'fecha_limite':        fecha_limite,
            'activa':              True,
        })

    return empresas


# ============================================
# GENERADOR DE MATCHES
# ============================================

def generar_matches(estudiantes, empresas, num_matches=300):
    """
    Genera matches entre estudiantes y empresas con scores realistas.
    Calcula compatibilidad básica según habilidades compartidas.
    """
    matches = []
    pares_vistos = set()

    intentos = 0
    while len(matches) < num_matches and intentos < num_matches * 10:
        intentos += 1
        est  = random.choice(estudiantes)
        emp  = random.choice(empresas)
        par  = (est['email'], emp['nombre'])

        if par in pares_vistos:
            continue
        pares_vistos.add(par)

        # Calcular score básico por habilidades compartidas
        habs_est = set(est['habilidades'].split('|'))
        habs_emp = set(emp['requisitos'].split('|'))
        interseccion = habs_est & habs_emp

        if habs_emp:
            score_hab = len(interseccion) / len(habs_emp)
        else:
            score_hab = 0.5

        # Score de experiencia
        exp_est = est['meses_experiencia']
        exp_emp = emp['experiencia_minima']
        score_exp = min(exp_est / max(exp_emp, 1), 1.0) if exp_emp > 0 else 1.0

        # Score carrera
        carrera_ok = est['carrera'] in emp['carreras_aceptadas'].split('|')
        score_carrera = 1.0 if carrera_ok else 0.3

        # Score final (ponderado)
        score_req  = (score_hab * 0.50 + score_exp * 0.30 + score_carrera * 0.20) * 100
        score_atr  = random.uniform(50, 95)  # Atractivo del candidato
        score_final = round(score_req * 0.6 + score_atr * 0.4, 2)

        # Desglose
        desglose = {
            'habilidades':    round(score_hab * 100, 1),
            'experiencia':    round(score_exp * 100, 1),
            'carrera':        round(score_carrera * 100, 1),
            'ubicacion':      round(random.uniform(40, 100), 1),
            'disponibilidad': round(random.uniform(50, 100), 1),
        }

        # Fecha del match: últimos 60 días
        dias_atras  = random.randint(1, 60)
        fecha_match = (datetime.now() - timedelta(days=dias_atras)).strftime("%Y-%m-%d %H:%M:%S")

        matches.append({
            'estudiante_email': est['email'],
            'empresa_nombre':   emp['nombre'],
            'score_requisitos': round(score_req, 2),
            'score_atractivo':  round(score_atr, 2),
            'score_final':      score_final,
            'desglose':         str(desglose).replace("'", '"'),
            'estado':           'generado',
            'fecha_match':      fecha_match,
        })

    return matches


# ============================================
# GENERADOR DE POSTULACIONES
# ============================================

def generar_postulaciones(matches, num_postulaciones=150):
    """
    Genera postulaciones a partir de los matches.
    Los matches con score alto tienen más probabilidad de ser postulados.
    Incluye algunos casos anómalos a propósito.
    """
    postulaciones = []

    # Ordenar matches por score para dar más probabilidad a los altos
    matches_altos = [m for m in matches if m['score_final'] >= 60]
    matches_bajos = [m for m in matches if m['score_final'] < 60]

    # 80% de postulaciones vienen de matches con score alto
    pool = (matches_altos * 3) + matches_bajos
    random.shuffle(pool)

    seleccionados = pool[:num_postulaciones]

    ESTADOS = ['postulado', 'postulado', 'postulado', 'en_revision',
               'entrevista', 'contratado', 'rechazado', 'sin_respuesta']

    for i, match in enumerate(seleccionados):
        estado    = random.choice(ESTADOS)
        prioridad = 'alta' if match['score_final'] >= 75 else ('media' if match['score_final'] >= 55 else 'baja')

        # Fecha de postulación: después del match
        dias_post   = random.randint(1, 7)
        fecha_match = datetime.strptime(match['fecha_match'], "%Y-%m-%d %H:%M:%S")
        fecha_post  = (fecha_match + timedelta(days=dias_post)).strftime("%Y-%m-%d %H:%M:%S")

        # Fecha de respuesta solo si hay respuesta
        fecha_respuesta = None
        if estado in ['contratado', 'rechazado', 'entrevista', 'en_revision']:
            dias_resp       = random.randint(3, 21)
            fecha_respuesta = (datetime.strptime(fecha_post, "%Y-%m-%d %H:%M:%S") + timedelta(days=dias_resp)).strftime("%Y-%m-%d %H:%M:%S")

        postulaciones.append({
            'estudiante_email': match['estudiante_email'],
            'empresa_nombre':   match['empresa_nombre'],
            'estado':           estado,
            'prioridad':        prioridad,
            'fecha_postulacion': fecha_post,
            'fecha_respuesta':   fecha_respuesta or '',
            'notas':            '',
        })

    # ---- CASOS ANÓMALOS A PROPÓSITO ----
    # 1. Estudiante spam: un estudiante que postula a muchas empresas (>20 en 7 días)
    if len(matches) >= 25:
        est_spam = matches[0]['estudiante_email']
        fecha_reciente = (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d %H:%M:%S")
        empresas_spam  = random.sample(matches, min(25, len(matches)))
        for m in empresas_spam:
            postulaciones.append({
                'estudiante_email':  est_spam,
                'empresa_nombre':    m['empresa_nombre'],
                'estado':            'postulado',
                'prioridad':         'baja',
                'fecha_postulacion': fecha_reciente,
                'fecha_respuesta':   '',
                'notas':             'postulacion_masiva',
            })

    return postulaciones


# ============================================
# GUARDAR EN CSV
# ============================================

def guardar_csv(datos, nombre_archivo, campos):
    with open(nombre_archivo, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        # Solo escribir los campos especificados
        for fila in datos:
            writer.writerow({k: fila.get(k, '') for k in campos})
    print(f"✅ '{nombre_archivo}' creado con {len(datos)} registros")


# ============================================
# MAIN
# ============================================

if __name__ == '__main__':
    print("=" * 60)
    print("GENERADOR DE DATASET")
    print("=" * 60)

    print(f"\n📊 Generando {NUM_ESTUDIANTES} estudiantes...")
    estudiantes = generar_estudiantes(NUM_ESTUDIANTES)

    print(f"📊 Generando {NUM_EMPRESAS} empresas...")
    empresas = generar_empresas(NUM_EMPRESAS)

    print(f"📊 Generando matches...")
    matches = generar_matches(estudiantes, empresas, num_matches=300)

    print(f"📊 Generando postulaciones...")
    postulaciones = generar_postulaciones(matches, num_postulaciones=150)

    print("\n💾 Guardando archivos CSV...")

    guardar_csv(estudiantes, 'estudiantes.csv', [
        'nombre', 'email', 'telefono', 'carrera', 'universidad',
        'promedio', 'semestre', 'habilidades', 'meses_experiencia',
        'nivel_ingles', 'proyectos', 'ubicacion', 'lat', 'lng',
        'horas_disponibles', 'calidad_cv', 'completitud', 'fecha_registro'
    ])

    guardar_csv(empresas, 'empresas.csv', [
        'nombre', 'area', 'descripcion', 'requisitos', 'carreras_aceptadas',
        'experiencia_minima', 'horas_requeridas', 'salario', 'ubicacion',
        'lat', 'lng', 'modalidad', 'tipo', 'fecha_limite', 'activa'
    ])

    guardar_csv(matches, 'matches.csv', [
        'estudiante_email', 'empresa_nombre', 'score_requisitos',
        'score_atractivo', 'score_final', 'desglose', 'estado', 'fecha_match'
    ])

    guardar_csv(postulaciones, 'postulaciones.csv', [
        'estudiante_email', 'empresa_nombre', 'estado', 'prioridad',
        'fecha_postulacion', 'fecha_respuesta', 'notas'
    ])

    print("\n" + "=" * 60)
    print("✅ DATASET GENERADO EXITOSAMENTE")
    print("=" * 60)
    print(f"  👤 {len(estudiantes)} estudiantes  → estudiantes.csv")
    print(f"  🏢 {len(empresas)} empresas       → empresas.csv")
    print(f"  🔗 {len(matches)} matches         → matches.csv")
    print(f"  📨 {len(postulaciones)} postulaciones → postulaciones.csv")
    print("\n💡 Ahora ejecuta:")
    print("   python cargar_dataset.py")
    print("=" * 60)