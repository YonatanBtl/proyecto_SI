"""
Script para cargar dataset a PostgreSQL
Lee los CSV generados y los inserta en la base de datos
Carga: estudiantes, empresas, matches y postulaciones
"""

import csv
import json
import psycopg2
from psycopg2.extras import execute_batch, RealDictCursor
import os

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://admin:admin123@localhost:5432/practicas_db')


def conectar_bd():
    try:
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        print("Conexión a base de datos exitosa")
        return conn
    except Exception as e:
        print(f"Error conectando a BD: {e}")
        print("\n Asegúrate de que Docker esté corriendo: docker-compose up -d")
        return None


def limpiar_tablas(conn):
    cursor = conn.cursor()
    print("\n🧹 Limpiando tablas...")
    try:
        cursor.execute("DELETE FROM anomalias")
        cursor.execute("DELETE FROM metricas")
        cursor.execute("DELETE FROM notificaciones")
        cursor.execute("DELETE FROM postulaciones")
        cursor.execute("DELETE FROM matches")
        cursor.execute("DELETE FROM estudiantes")
        cursor.execute("DELETE FROM empresas")
        cursor.execute("ALTER SEQUENCE estudiantes_id_seq RESTART WITH 1")
        cursor.execute("ALTER SEQUENCE empresas_id_seq RESTART WITH 1")
        cursor.execute("ALTER SEQUENCE matches_id_seq RESTART WITH 1")
        cursor.execute("ALTER SEQUENCE postulaciones_id_seq RESTART WITH 1")
        conn.commit()
        print("Tablas limpiadas")
    except Exception as e:
        print(f"Error limpiando tablas: {e}")
        conn.rollback()
    finally:
        cursor.close()


def cargar_empresas(conn, archivo='empresas.csv'):
    cursor = conn.cursor()
    print(f"\nCargando empresas desde {archivo}...")

    with open(archivo, 'r', encoding='utf-8') as f:
        empresas = list(csv.DictReader(f))

    datos = []
    for emp in empresas:
        requisitos = emp['requisitos'].split('|') if emp['requisitos'] else []
        carreras   = emp['carreras_aceptadas'].split('|') if emp['carreras_aceptadas'] else []
        datos.append((
            emp['nombre'], emp['area'], emp['descripcion'],
            requisitos, carreras,
            int(emp['experiencia_minima']), int(emp['horas_requeridas']),
            float(emp['salario']), emp['ubicacion'],
            float(emp['lat']), float(emp['lng']),
            emp['modalidad'], emp['tipo'], emp['fecha_limite'],
            emp['activa'].lower() == 'true'
        ))

    query = """
        INSERT INTO empresas (
            nombre, area, descripcion, requisitos, carreras_aceptadas,
            experiencia_minima, horas_requeridas, salario, ubicacion,
            lat, lng, modalidad, tipo, fecha_limite, activa
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """
    try:
        execute_batch(cursor, query, datos, page_size=100)
        conn.commit()
        print(f"{len(datos)} empresas cargadas")
    except Exception as e:
        print(f"Error cargando empresas: {e}")
        conn.rollback()
    finally:
        cursor.close()


def cargar_estudiantes(conn, archivo='estudiantes.csv'):
    cursor = conn.cursor()
    print(f"\nCargando estudiantes desde {archivo}...")

    with open(archivo, 'r', encoding='utf-8') as f:
        estudiantes = list(csv.DictReader(f))

    datos = []
    for est in estudiantes:
        habilidades = est['habilidades'].split('|') if est['habilidades'] else []
        proyectos   = est['proyectos'].split('|') if est['proyectos'] else []
        fecha_reg   = est.get('fecha_registro') or None
        datos.append((
            est['nombre'], est['email'], est['telefono'],
            est['carrera'], est['universidad'],
            float(est['promedio']) if est['promedio'] else None,
            int(est['semestre']) if est['semestre'] else None,
            None, None,  # cv_url, cv_texto
            habilidades, int(est['meses_experiencia']),
            est['nivel_ingles'], proyectos,
            est['ubicacion'], float(est['lat']), float(est['lng']),
            int(est['horas_disponibles']),
            int(est['calidad_cv']), int(est['completitud']),
            fecha_reg
        ))

    query = """
        INSERT INTO estudiantes (
            nombre, email, telefono, carrera, universidad,
            promedio, semestre, cv_url, cv_texto,
            habilidades, meses_experiencia, nivel_ingles, proyectos,
            ubicacion, lat, lng, horas_disponibles,
            calidad_cv, completitud, fecha_registro
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """
    try:
        execute_batch(cursor, query, datos, page_size=100)
        conn.commit()
        print(f"{len(datos)} estudiantes cargados")
    except Exception as e:
        print(f"Error cargando estudiantes: {e}")
        conn.rollback()
    finally:
        cursor.close()


def cargar_matches(conn, archivo='matches.csv'):
    """Carga matches resolviendo IDs por email/nombre"""
    cursor = conn.cursor()
    print(f"\nCargando matches desde {archivo}...")

    # Construir mapas email→id y nombre→id
    cursor.execute("SELECT id, email FROM estudiantes")
    mapa_est = {r['email']: r['id'] for r in cursor.fetchall()}

    cursor.execute("SELECT id, nombre FROM empresas")
    mapa_emp = {r['nombre']: r['id'] for r in cursor.fetchall()}

    with open(archivo, 'r', encoding='utf-8') as f:
        matches = list(csv.DictReader(f))

    datos   = []
    omitidos = 0
    for m in matches:
        est_id = mapa_est.get(m['estudiante_email'])
        emp_id = mapa_emp.get(m['empresa_nombre'])
        if not est_id or not emp_id:
            omitidos += 1
            continue

        # Parsear desglose JSON
        try:
            desglose = json.loads(m['desglose'].replace("'", '"'))
        except Exception:
            desglose = {}

        fecha = m.get('fecha_match') or None
        datos.append((
            est_id, emp_id,
            float(m['score_requisitos']),
            float(m['score_atractivo']),
            float(m['score_final']),
            json.dumps(desglose),
            m.get('estado', 'generado'),
            fecha
        ))

    query = """
        INSERT INTO matches (
            estudiante_id, empresa_id, score_requisitos,
            score_atractivo, score_final, desglose, estado, fecha_match
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (estudiante_id, empresa_id) DO NOTHING
    """
    try:
        execute_batch(cursor, query, datos, page_size=100)
        conn.commit()
        print(f"{len(datos)} matches cargados ({omitidos} omitidos por ID no encontrado)")
    except Exception as e:
        print(f"Error cargando matches: {e}")
        conn.rollback()
    finally:
        cursor.close()


def cargar_postulaciones(conn, archivo='postulaciones.csv'):
    """Carga postulaciones resolviendo IDs por email/nombre"""
    cursor = conn.cursor()
    print(f"\nCargando postulaciones desde {archivo}...")

    cursor.execute("SELECT id, email FROM estudiantes")
    mapa_est = {r['email']: r['id'] for r in cursor.fetchall()}

    cursor.execute("SELECT id, nombre FROM empresas")
    mapa_emp = {r['nombre']: r['id'] for r in cursor.fetchall()}

    # Mapa de matches para relacionar match_id
    cursor.execute("SELECT id, estudiante_id, empresa_id FROM matches")
    mapa_match = {(r['estudiante_id'], r['empresa_id']): r['id'] for r in cursor.fetchall()}

    with open(archivo, 'r', encoding='utf-8') as f:
        postulaciones = list(csv.DictReader(f))

    datos    = []
    omitidos = 0
    for p in postulaciones:
        est_id = mapa_est.get(p['estudiante_email'])
        emp_id = mapa_emp.get(p['empresa_nombre'])
        if not est_id or not emp_id:
            omitidos += 1
            continue

        match_id       = mapa_match.get((est_id, emp_id))
        fecha_resp     = p['fecha_respuesta'] if p.get('fecha_respuesta') else None
        fecha_post     = p.get('fecha_postulacion') or None

        datos.append((
            match_id, est_id, emp_id,
            p.get('estado', 'postulado'),
            p.get('prioridad', 'media'),
            fecha_post, fecha_resp,
            p.get('notas', '')
        ))

    query = """
        INSERT INTO postulaciones (
            match_id, estudiante_id, empresa_id,
            estado, prioridad, fecha_postulacion, fecha_respuesta, notas
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
    """
    try:
        execute_batch(cursor, query, datos, page_size=100)
        conn.commit()
        print(f"{len(datos)} postulaciones cargadas ({omitidos} omitidas)")
    except Exception as e:
        print(f"Error cargando postulaciones: {e}")
        conn.rollback()
    finally:
        cursor.close()


def verificar_carga(conn):
    cursor = conn.cursor()
    print("\n" + "=" * 60)
    print("RESUMEN DE CARGA")
    print("=" * 60)

    for tabla in ['estudiantes', 'empresas', 'matches', 'postulaciones']:
        cursor.execute(f"SELECT COUNT(*) as total FROM {tabla}")
        total = cursor.fetchone()['total']
        print(f"   {tabla}: {total} registros")

    # Tasa de éxito
    cursor.execute("SELECT estado, COUNT(*) as total FROM postulaciones GROUP BY estado ORDER BY total DESC")
    print("\n   Postulaciones por estado:")
    for row in cursor.fetchall():
        print(f"     {row['estado']}: {row['total']}")

    # Score promedio
    cursor.execute("SELECT ROUND(AVG(score_final)::numeric, 2) as avg FROM matches")
    avg = cursor.fetchone()['avg']
    print(f"\n   Score promedio de matches: {avg}")

    cursor.close()
    print("=" * 60)


def main():
    print("=" * 60)
    print("CARGADOR DE DATASET A POSTGRESQL")
    print("=" * 60)

    conn = conectar_bd()
    if not conn:
        return

    print("\n ¿Limpiar tablas antes de cargar? (s/n)")
    respuesta = input("   Esto borrará TODOS los datos existentes: ").lower()
    if respuesta == 's':
        limpiar_tablas(conn)

    # Cargar en orden por dependencias
    cargar_empresas(conn)
    cargar_estudiantes(conn)

    if os.path.exists('matches.csv'):
        cargar_matches(conn)
    else:
        print("\n  matches.csv no encontrado, omitiendo...")

    if os.path.exists('postulaciones.csv'):
        cargar_postulaciones(conn)
    else:
        print("\n  postulaciones.csv no encontrado, omitiendo...")

    verificar_carga(conn)
    conn.close()

    print("\n Proceso completado")
    print("   Prueba los endpoints:")
    print("   Invoke-RestMethod http://localhost:5000/api/kpis")
    print("   Invoke-RestMethod http://localhost:5000/api/empresas")


if __name__ == '__main__':
    main()