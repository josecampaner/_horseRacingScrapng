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
            updated_at TIMESTAMP
        );
        """
        
        # Crear tabla horses
        create_horses_table = """
        CREATE TABLE IF NOT EXISTS horses (
            horse_url TEXT PRIMARY KEY,
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
            profile_url TEXT,
            last_race_date DATE,
            last_scraped_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP
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
            updated_at TIMESTAMP
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
            updated_at TIMESTAMP
        );
        """
        
        # Crear tabla race_entries (sin columna id, race_id es la clave)
        create_entries_table = """
        CREATE TABLE IF NOT EXISTS race_entries (
            race_id VARCHAR(100) REFERENCES races(race_id) ON DELETE CASCADE,
            horse_id VARCHAR(255),
            horse_name VARCHAR(255),
            trainer VARCHAR(255),
            jockey VARCHAR(255),
            status VARCHAR(20) DEFAULT 'active',
            status_history TEXT,
            status_changed_at TIMESTAMP,
            post_position INTEGER,
            sire VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP,
            PRIMARY KEY(race_id, horse_id)
        );
        """
        
        # Crear tabla pedigree
        create_pedigree_table = """
        CREATE TABLE IF NOT EXISTS pedigree (
            horse_url TEXT PRIMARY KEY REFERENCES horses(horse_url) ON DELETE CASCADE,
            sire_id VARCHAR(255),
            dam_id VARCHAR(255),
            paternal_grandsire_id VARCHAR(255),
            paternal_granddam_id VARCHAR(255),
            maternal_grandsire_id VARCHAR(255),
            maternal_granddam_id VARCHAR(255),
            paternal_gg_sire_id VARCHAR(255),
            paternal_gg_dam_id VARCHAR(255),
            paternal_gd_sire_id VARCHAR(255),
            paternal_gd_dam_id VARCHAR(255),
            maternal_gg_sire_id VARCHAR(255),
            maternal_gg_dam_id VARCHAR(255),
            maternal_gd_sire_id VARCHAR(255),
            maternal_gd_dam_id VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP
        );
        """
        
        cur.execute(create_races_table)
        cur.execute(create_horses_table)
        cur.execute(create_trainers_table)
        cur.execute(create_jockeys_table)
        cur.execute(create_entries_table)
        cur.execute(create_pedigree_table)
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
    from database.entries import find_or_create_trainer, find_or_create_jockey, find_or_create_horse_with_id
    from utils.track_ipa_generator import generate_track_ipa_and_country
    from utils.race_parser import TRACK_CODES
    
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
        
        # ✅ CONSULTAR TABLA TRACKS PRIMERO
        track_query = """
        SELECT track_name, track_name_ipa, country 
        FROM tracks 
        WHERE track_code = %s AND active = true
        """
        cur.execute(track_query, (track_code_short,))
        track_info = cur.fetchone()
        
        if track_info:
            # ✅ Usar información de la tabla tracks
            track_name_base, track_ipa, country = track_info
        else:
            # ✅ AUTO-GENERAR: No existe en tabla tracks, usar track_ipa_generator
            from utils.track_ipa_generator import generate_track_ipa_and_country
            from utils.race_parser import TRACK_CODES
            
            # ✅ USAR MAPEO OFICIAL: buscar en códigos oficiales primero
            track_name_base = None
            for slug, code in TRACK_CODES.items():
                if code == track_code_short:
                    # Convertir slug a nombre: "santa-anita-park" → "Santa Anita Park"
                    track_name_base = slug.replace('-', ' ').title()
                    break
            
            # Fallback si no se encuentra en códigos oficiales
            if not track_name_base:
                track_name_mapping_fallback = {
                    'THISTLEDOW': 'Thistledown',
                    'Tdn': 'Thistledown',
                }
                track_name_base = track_name_mapping_fallback.get(track_code_short, None)
                
                # Si tampoco está en fallback, es un hipódromo COMPLETAMENTE NUEVO
                if not track_name_base:
                    # 🚨 DETECTAR HIPÓDROMO NUEVO
                    logger.warning(
                        f"🆕 HIPÓDROMO NUEVO DETECTADO: '{track_code_short}' - Generando nombre automáticamente"
                    )
                    logger.info(
                        f"🆕 HIPÓDROMO NUEVO: {track_code_short} - Revisa que el nombre sea correcto"
                    )
                    
                    # Reglas inteligentes para generar nombre desde código
                    if len(track_code_short) <= 3:
                        # Códigos cortos como "WO", "TAM", "FG" → usar como está pero capitalizado
                        track_name_base = track_code_short.upper()
                    else:
                        # Códigos largos como "BELMONT-PK" → convertir a nombre
                        track_name_base = track_code_short.replace('-', ' ').replace('_', ' ').title()
                        # Reemplazos comunes
                        track_name_base = track_name_base.replace('Pk', 'Park').replace('Downs', 'Downs').replace('Rc', 'Racecourse')
                    
                    logger.info(f"✅ Nombre generado: '{track_code_short}' → '{track_name_base}'")
            
            # Generar IPA automáticamente
            track_ipa, country = generate_track_ipa_and_country(track_name_base)
            
            # ✅ AUTO-INSERTAR en tabla tracks para futuros usos
            insert_track_query = """
            INSERT INTO tracks (track_code, track_name, track_name_ipa, country, active, created_at, updated_at)
            VALUES (%s, %s, %s, %s, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON CONFLICT (track_code) DO UPDATE SET
                track_name = EXCLUDED.track_name,
                track_name_ipa = EXCLUDED.track_name_ipa,
                country = EXCLUDED.country,
                updated_at = CURRENT_TIMESTAMP
            """
            cur.execute(insert_track_query, (track_code_short, track_name_base, track_ipa, country or 'USA'))
            
            logger.info(
                f"✅ Auto-agregado track: {track_code_short} -> {track_name_base} ({track_ipa})"
            )
        
        # Generar track_name final con formato "(País)"
        if country and country != 'Unknown':
            track_name = f"{track_name_base} ({country})"
        else:
            track_name = track_name_base
        
        race_values = (
            race_data.get('race_id'),
            race_data.get('title'),
            race_data.get('race_date'),
            track_name,
            track_ipa,
            track_code_short,
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
            for participant in race_data.get('participants', []):
                # Usar el horse_id real extraído del enlace, o generar uno si no está disponible
                horse_id = participant.get('horse_id', 'N/A')
                if horse_id == 'N/A':
                    # Fallback: generar horse_id basado en el nombre del caballo
                    horse_name = participant.get('horse_name', 'Unknown')
                    horse_id = f"{race_data.get('race_id')}_{horse_name.replace(' ', '_')}"
                
                # Detectar el status actual basado en el scraping
                current_status = 'scratched' if participant.get('status') == 'scratched' else 'active'
                current_timestamp = datetime.now()
                
                # Verificar si ya existe el caballo en esta carrera para detectar cambios
                check_existing_query = """
                SELECT status, status_history, status_changed_at 
                FROM race_entries 
                WHERE race_id = %s AND horse_id = %s
                """
                cur.execute(check_existing_query, (race_data.get('race_id'), horse_id))
                existing_entry = cur.fetchone()
                
                status_history = None
                status_changed_at = None
                
                if existing_entry:
                    previous_status, previous_history, previous_changed_at = existing_entry
                    
                    # Si el status cambió, actualizar el historial
                    if previous_status != current_status:
                        # Crear entrada de historial
                        new_history_entry = f"{current_timestamp.strftime('%Y-%m-%d %H:%M:%S')}: {previous_status} → {current_status}"
                        
                        if previous_history:
                            status_history = f"{previous_history}\n{new_history_entry}"
                        else:
                            status_history = new_history_entry
                        
                        status_changed_at = current_timestamp
                        logger.info(f"🔄 Status cambió para {participant.get('horse_name')}: {previous_status} → {current_status}")
                    else:
                        # Sin cambio, mantener historial existente
                        status_history = previous_history
                        status_changed_at = previous_changed_at
                else:
                    # Nuevo caballo, crear historial inicial
                    if current_status == 'scratched':
                        status_history = f"{current_timestamp.strftime('%Y-%m-%d %H:%M:%S')}: active → scratched (inicial)"
                        status_changed_at = current_timestamp
                    else:
                        # Caballo activo: crear registro inicial también
                        status_history = f"{current_timestamp.strftime('%Y-%m-%d %H:%M:%S')}: inicial → active"
                        status_changed_at = current_timestamp
                
                # Crear/encontrar trainer, jockey y caballo usando el MISMO horse_id
                find_or_create_trainer(cur, participant.get('trainer', 'Unknown'))
                find_or_create_jockey(cur, participant.get('jockey', 'Unknown'))
                find_or_create_horse_with_id(cur, horse_id, participant.get('horse_name', 'Unknown'), 
                                           participant.get('sire'), participant.get('trainer'))
                
                # Post position - convertir a entero si es posible
                post_position = None
                pp_str = participant.get('pp', 'N/A')
                if pp_str and pp_str != 'N/A':
                    try:
                        post_position = int(pp_str)
                    except (ValueError, TypeError):
                        post_position = None
                
                # Insert/Update con los nuevos campos
                insert_entry_query = """
                INSERT INTO race_entries (
                    race_id, horse_id, horse_name, trainer, jockey, 
                    status, status_history, status_changed_at, post_position, sire, updated_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (race_id, horse_id) DO UPDATE SET
                    horse_name = EXCLUDED.horse_name,
                    trainer = EXCLUDED.trainer,
                    jockey = EXCLUDED.jockey,
                    status = EXCLUDED.status,
                    status_history = EXCLUDED.status_history,
                    status_changed_at = EXCLUDED.status_changed_at,
                    post_position = EXCLUDED.post_position,
                    sire = EXCLUDED.sire,
                    updated_at = CURRENT_TIMESTAMP
                """
                
                entry_values = (
                    race_data.get('race_id'),
                    horse_id,
                    participant.get('horse_name'),
                    participant.get('trainer'),
                    participant.get('jockey'),
                    current_status,
                    status_history,
                    status_changed_at,
                    post_position,
                    participant.get('sire'),
                    current_timestamp
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