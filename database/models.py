import psycopg2
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

# Configuración de la base de datos
DB_NAME = "caballos_db"
DB_USER = os.getenv("DB_USER", "macm1")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")

def get_db_connection():
    """Obtiene conexión a la base de datos PostgreSQL"""
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        return conn
    except psycopg2.Error as e:
        logger.error(f"Error al conectar a PostgreSQL: {e}")
        return None

def create_database_tables():
    """Crea las tablas necesarias en la base de datos si no existen"""
    conn = get_db_connection()
    if not conn:
        logger.error("No se pudo conectar a la base de datos para crear tablas")
        return False
    
    try:
        cur = conn.cursor()
        
        # Crear tabla races
        create_races_table = """
        CREATE TABLE IF NOT EXISTS races (
            race_id VARCHAR(100) PRIMARY KEY,
            race_name VARCHAR(255),
            race_date DATE,
            track_name VARCHAR(100),
            track_ipa VARCHAR(255),
            track_code VARCHAR(10),
            race_number INTEGER,
            race_type VARCHAR(100),
            distance VARCHAR(50),
            surface VARCHAR(50),
            conditions_clean TEXT,
            age_restriction VARCHAR(50),
            specific_race_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # Crear tabla horses
        create_horses_table = """
        CREATE TABLE IF NOT EXISTS horses (
            horse_id VARCHAR(255) PRIMARY KEY,
            horse_name VARCHAR(255),
            horse_name_ipa VARCHAR(255),
            owner VARCHAR(255),
            owner_ipa VARCHAR(255),
            trainer VARCHAR(255),
            trainer_ipa VARCHAR(255),
            breeder VARCHAR(255),
            breeder_ipa VARCHAR(255),
            country VARCHAR(100),
            country_of_birth VARCHAR(100),
            age INTEGER,
            status VARCHAR(50),
            sex VARCHAR(50),
            color VARCHAR(50),
            url TEXT,
            profile_url TEXT,
            last_race_date DATE,
            last_scraped_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # Crear tabla trainers con IPA unificado
        create_trainers_table = """
        CREATE TABLE IF NOT EXISTS trainers (
            trainer_id VARCHAR(255) PRIMARY KEY,
            trainer_name VARCHAR(255),
            trainer_name_ipa VARCHAR(255),
            profile_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # Crear tabla jockeys con IPA unificado
        create_jockeys_table = """
        CREATE TABLE IF NOT EXISTS jockeys (
            jockey_id VARCHAR(255) PRIMARY KEY,
            jockey_name VARCHAR(255),
            jockey_name_ipa VARCHAR(255),
            profile_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # Crear tabla race_entries (sin columna id, race_id es la clave)
        create_entries_table = """
        CREATE TABLE IF NOT EXISTS race_entries (
            race_id VARCHAR(100) REFERENCES races(race_id) ON DELETE CASCADE,
            horse_id VARCHAR(255),
            horse_name VARCHAR(255),
            sire VARCHAR(255),
            trainer VARCHAR(255),
            jockey VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY(race_id, horse_id)
        );
        """
        
        cur.execute(create_races_table)
        cur.execute(create_horses_table)
        cur.execute(create_trainers_table)
        cur.execute(create_jockeys_table)
        cur.execute(create_entries_table)
        conn.commit()
        
        logger.info("Tablas creadas/verificadas exitosamente")
        return True
        
    except psycopg2.Error as e:
        logger.error(f"Error al crear tablas: {e}")
        conn.rollback()
        return False
    except Exception as e:
        logger.error(f"Error general al crear tablas: {e}")
        conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def save_race_data_to_db(race_data, main_page_url):
    """Guarda los datos de una carrera y sus participantes en la base de datos"""
    from utils.text_processing import clean_conditions_remove_age
    from database.entries import find_or_create_trainer, find_or_create_jockey
    from utils.track_ipa_generator import generate_track_ipa_and_country
    
    conn = get_db_connection()
    if not conn:
        logger.error(f"No se pudo conectar a la base de datos para guardar carrera {race_data.get('race_id', 'unknown')}")
        return False
    
    try:
        cur = conn.cursor()
        
        # Insertar datos de la carrera
        insert_race_query = """
        INSERT INTO races (
            race_id, race_name, race_date, track_name, track_ipa, track_code, 
            race_number, race_type, distance, surface, conditions_clean,
            age_restriction, specific_race_url
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (race_id) DO UPDATE SET
            race_name = EXCLUDED.race_name,
            race_date = EXCLUDED.race_date,
            track_name = EXCLUDED.track_name,
            track_ipa = EXCLUDED.track_ipa,
            track_code = EXCLUDED.track_code,
            race_number = EXCLUDED.race_number,
            race_type = EXCLUDED.race_type,
            distance = EXCLUDED.distance,
            surface = EXCLUDED.surface,
            conditions_clean = EXCLUDED.conditions_clean,
            age_restriction = EXCLUDED.age_restriction,
            specific_race_url = EXCLUDED.specific_race_url,
            updated_at = CURRENT_TIMESTAMP;
        """
        
        # Limpiar condiciones para separar edad
        conditions_text = race_data.get('conditions', 'N/A')
        conditions_clean = clean_conditions_remove_age(conditions_text) if conditions_text != 'N/A' else 'N/A'
        age_restriction = race_data.get('age_restriction_scraped', 'N/A')
        
        # Extraer track_code real (solo las primeras 2-3 letras del race_id)
        race_id = race_data.get('race_id', '')
        track_code_short = race_id.split('_')[0] if '_' in race_id else 'UNK'
        
        # Asegurar que track_code no exceda 10 caracteres
        if len(track_code_short) > 10:
            track_code_short = track_code_short[:10]
        
        # Generar pronunciación IPA y país para la pista
        track_name_base = "Gulfstream Park"  # nombre base de la pista
        track_ipa, country = generate_track_ipa_and_country(track_name_base)
        
        # Agregar país al nombre de la pista
        track_name_with_country = f"{track_name_base} ({country})" if country and country != 'Unknown' else track_name_base
        
        race_values = (
            race_data.get('race_id'),
            race_data.get('title'),
            race_data.get('race_date'),
            track_name_with_country,  # track_name - nombre con país
            track_ipa,   # track_ipa - solo pronunciación IPA
            track_code_short,  # track_code - solo código corto como "GP"
            int(race_data.get('race_number')) if race_data.get('race_number') and race_data.get('race_number') != 'N/A' else None,
            race_data.get('race_type_from_detail'),
            race_data.get('distance'),
            race_data.get('surface'),
            conditions_clean,
            age_restriction,
            race_data.get('specific_race_url')
        )
        
        cur.execute(insert_race_query, race_values)
        
        # Insertar participantes
        if race_data.get('participants'):
            insert_entry_query = """
            INSERT INTO race_entries (race_id, horse_id, horse_name, sire, trainer, jockey)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (race_id, horse_id) DO UPDATE SET
                horse_name = EXCLUDED.horse_name,
                sire = EXCLUDED.sire,
                trainer = EXCLUDED.trainer,
                jockey = EXCLUDED.jockey
            """
            
            for participant in race_data.get('participants', []):
                # Usar el horse_id real extraído del enlace, o generar uno si no está disponible
                horse_id = participant.get('horse_id', 'N/A')
                if horse_id == 'N/A':
                    # Fallback: generar horse_id basado en el nombre del caballo
                    horse_name = participant.get('horse_name', 'Unknown')
                    horse_id = f"{race_data.get('race_id')}_{horse_name.replace(' ', '_')}"
                
                # Crear/encontrar trainer y jockey (esto los guarda en sus tablas con IPAs)
                find_or_create_trainer(cur, participant.get('trainer', 'Unknown'))
                find_or_create_jockey(cur, participant.get('jockey', 'Unknown'))
                
                entry_values = (
                    race_data.get('race_id'),
                    horse_id,
                    participant.get('horse_name'),
                    participant.get('sire'),
                    participant.get('trainer'),
                    participant.get('jockey')
                )
                cur.execute(insert_entry_query, entry_values)
        
        conn.commit()
        logger.info(f"Carrera {race_data.get('race_id')} guardada exitosamente con {len(race_data.get('participants', []))} participantes")
        return True
        
    except psycopg2.Error as e:
        logger.error(f"Error al guardar carrera {race_data.get('race_id', 'unknown')} en PostgreSQL: {e}")
        conn.rollback()
        return False
    except Exception as e:
        logger.error(f"Error general al guardar carrera {race_data.get('race_id', 'unknown')}: {e}")
        conn.rollback()
        return False
    finally:
        if conn:
            conn.close() 