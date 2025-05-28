import logging
import urllib.parse
from utils.ipa_generator import generate_english_ipa
from utils.horse_ipa_generator import generate_horse_ipa
from datetime import datetime

logger = logging.getLogger(__name__)

def translate_ipa_to_spanish(ipa_text):
    """Traduce texto IPA a pronunciación en español"""
    if not ipa_text:
        return None
    
    # Mapeo básico de sonidos IPA a español
    ipa_to_spanish = {
        'θ': 'z',  # th sound -> z
        'ð': 'd',  # th sound -> d
        'ʃ': 'sh', # sh sound
        'ʒ': 'y',  # zh sound -> y
        'tʃ': 'ch', # ch sound
        'dʒ': 'y',  # j sound -> y
        'ŋ': 'ng',  # ng sound
        'ɹ': 'r',   # r sound
        'ɪ': 'i',   # short i
        'ɛ': 'e',   # short e
        'æ': 'a',   # short a
        'ʌ': 'a',   # short u -> a
        'ʊ': 'u',   # short u
        'ə': 'e',   # schwa -> e
        'ɔ': 'o',   # short o
        'ɑ': 'a',   # long a
        'i': 'i',   # long i
        'u': 'u',   # long u
        'o': 'o',   # long o
        'e': 'e',   # long e
    }
    
    spanish_pronunciation = ipa_text
    for ipa_sound, spanish_sound in ipa_to_spanish.items():
        spanish_pronunciation = spanish_pronunciation.replace(ipa_sound, spanish_sound)
    
    # Limpiar caracteres IPA restantes
    import re
    spanish_pronunciation = re.sub(r'[ˈˌ]', '', spanish_pronunciation)  # Remover acentos
    spanish_pronunciation = re.sub(r'[ː]', '', spanish_pronunciation)   # Remover longitud
    
    return spanish_pronunciation

def find_or_create_sire_horse_id(cursor, sire_name):
    """
    Busca o crea un horse_id para un sire (padre) en la tabla horses.
    Si no existe, lo crea con información básica.
    """
    if not sire_name or sire_name.strip() == '' or sire_name.lower() in ['unknown', 'n/a', 'none']:
        return None
    
    sire_name_clean = sire_name.strip()
    
    # Generar un horse_id basado en el nombre del sire
    sire_id = sire_name_clean.replace(' ', '_').replace("'", "").replace('.', '').replace(',', '')
    
    try:
        # Verificar si ya existe
        cursor.execute("SELECT horse_id FROM horses WHERE horse_id = %s", (sire_id,))
        result = cursor.fetchone()
        
        if result:
            return sire_id
        
        # Si no existe, crearlo
        current_time = datetime.now()
        insert_sire_query = """
        INSERT INTO horses (horse_id, horse_name, status, created_at)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (horse_id) DO NOTHING
        """
        cursor.execute(insert_sire_query, (sire_id, sire_name_clean, 'sire', current_time))
        
        logger.info(f"Sire creado: {sire_name_clean} -> {sire_id}")
        return sire_id
        
    except Exception as e:
        logger.error(f"Error al buscar/crear sire {sire_name}: {e}")
        return None

def find_or_create_trainer(cursor, trainer_name):
    """
    Busca o crea un entrenador en la tabla trainers con IPA.
    Si no existe, lo crea con información básica.
    """
    if not trainer_name or trainer_name.strip() == '' or trainer_name.lower() in ['unknown', 'n/a', 'none']:
        return None
    
    trainer_name_clean = trainer_name.strip()
    
    try:
        # Verificar si ya existe usando trainer_name como PRIMARY KEY
        cursor.execute("SELECT trainer_name FROM trainers WHERE trainer_name = %s", (trainer_name_clean,))
        result = cursor.fetchone()
        
        if result:
            return trainer_name_clean
        
        # Si no existe, crearlo
        trainer_ipa = generate_english_ipa(trainer_name_clean) if trainer_name_clean else None
        
        insert_trainer_query = """
        INSERT INTO trainers (trainer_name, trainer_name_ipa)
        VALUES (%s, %s)
        ON CONFLICT (trainer_name) DO NOTHING
        """
        cursor.execute(insert_trainer_query, (trainer_name_clean, trainer_ipa))
        
        logger.info(f"Trainer creado: {trainer_name_clean} (IPA: {trainer_ipa})")
        return trainer_name_clean
        
    except Exception as e:
        logger.error(f"Error al buscar/crear trainer {trainer_name}: {e}")
        return None

def find_or_create_jockey(cursor, jockey_name):
    """
    Busca o crea un jinete en la tabla jockeys con IPA.
    Si no existe, lo crea con información básica.
    """
    if not jockey_name or jockey_name.strip() == '' or jockey_name.lower() in ['unknown', 'n/a', 'none']:
        return None
    
    jockey_name_clean = jockey_name.strip()
    
    try:
        # Verificar si ya existe usando jockey_name como PRIMARY KEY
        cursor.execute("SELECT jockey_name FROM jockeys WHERE jockey_name = %s", (jockey_name_clean,))
        result = cursor.fetchone()
        
        if result:
            return jockey_name_clean
        
        # Si no existe, crearlo con IPA básico
        jockey_ipa = generate_english_ipa(jockey_name_clean) if jockey_name_clean else None
        
        insert_jockey_query = """
        INSERT INTO jockeys (jockey_name, jockey_name_ipa)
        VALUES (%s, %s)
        ON CONFLICT (jockey_name) DO NOTHING
        """
        cursor.execute(insert_jockey_query, (jockey_name_clean, jockey_ipa))
        
        logger.info(f"Jockey creado: {jockey_name_clean} (IPA: {jockey_ipa})")
        return jockey_name_clean
        
    except Exception as e:
        logger.error(f"Error al buscar/crear jockey {jockey_name}: {e}")
        return None

def find_or_create_owner(cursor, owner_name):
    """
    Busca o crea un propietario en la tabla owners con IPA.
    Si no existe, lo crea con información básica.
    Se llama durante el UPDATE del caballo (perfil individual).
    """
    if not owner_name or owner_name.strip() == '' or owner_name.lower() in ['unknown', 'n/a', 'none']:
        return None
    
    owner_name_clean = owner_name.strip()
    
    try:
        # Verificar si ya existe usando owner_name como PRIMARY KEY
        cursor.execute("SELECT owner_name FROM owners WHERE owner_name = %s", (owner_name_clean,))
        result = cursor.fetchone()
        
        if result:
            return owner_name_clean
        
        # Si no existe, crearlo con IPA básico
        owner_ipa = generate_english_ipa(owner_name_clean) if owner_name_clean else None
        
        insert_owner_query = """
        INSERT INTO owners (owner_name, owner_name_ipa)
        VALUES (%s, %s)
        ON CONFLICT (owner_name) DO NOTHING
        """
        cursor.execute(insert_owner_query, (owner_name_clean, owner_ipa))
        
        logger.info(f"Owner creado: {owner_name_clean} (IPA: {owner_ipa})")
        return owner_name_clean
        
    except Exception as e:
        logger.error(f"Error al buscar/crear owner {owner_name}: {e}")
        return None

def find_or_create_breeder(cursor, breeder_name):
    """
    Busca o crea un criador en la tabla breeders con IPA.
    Si no existe, lo crea con información básica.
    Se llama durante el UPDATE del caballo (perfil individual).
    """
    if not breeder_name or breeder_name.strip() == '' or breeder_name.lower() in ['unknown', 'n/a', 'none']:
        return None
    
    breeder_name_clean = breeder_name.strip()
    
    try:
        # Verificar si ya existe usando breeder_name como PRIMARY KEY
        cursor.execute("SELECT breeder_name FROM breeders WHERE breeder_name = %s", (breeder_name_clean,))
        result = cursor.fetchone()
        
        if result:
            return breeder_name_clean
        
        # Si no existe, crearlo con IPA básico
        breeder_ipa = generate_english_ipa(breeder_name_clean) if breeder_name_clean else None
        
        insert_breeder_query = """
        INSERT INTO breeders (breeder_name, breeder_name_ipa)
        VALUES (%s, %s)
        ON CONFLICT (breeder_name) DO NOTHING
        """
        cursor.execute(insert_breeder_query, (breeder_name_clean, breeder_ipa))
        
        logger.info(f"Breeder creado: {breeder_name_clean} (IPA: {breeder_ipa})")
        return breeder_name_clean
        
    except Exception as e:
        logger.error(f"Error al buscar/crear breeder {breeder_name}: {e}")
        return None

def find_or_create_horse_with_id(cursor, horse_id, horse_name, sire_name=None, trainer_name=None):
    """
    Busca o crea un caballo en la tabla horses usando un horse_id específico.
    Esta función mantiene consistencia con los IDs usados en race_entries.
    """
    if not horse_id or horse_id.strip() == '' or horse_id.lower() in ['unknown', 'n/a', 'none']:
        return None
    
    if not horse_name or horse_name.strip() == '' or horse_name.lower() in ['unknown', 'n/a', 'none']:
        return None
    
    horse_id_clean = horse_id.strip()
    horse_name_clean = horse_name.strip()
    
    try:
        # Verificar si ya existe
        cursor.execute("SELECT horse_name FROM horses WHERE horse_id = %s", (horse_id_clean,))
        result = cursor.fetchone()
        
        if result:
            return horse_name_clean
        
        # Si no existe, crearlo con el horse_id específico
        trainer_ipa = generate_english_ipa(trainer_name) if trainer_name else None
        current_time = datetime.now()
        
        insert_horse_query = """
        INSERT INTO horses (horse_id, horse_name, trainer, trainer_ipa, status, created_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (horse_id) DO NOTHING
        """
        cursor.execute(insert_horse_query, (
            horse_id_clean, 
            horse_name_clean, 
            trainer_name, 
            trainer_ipa, 
            'active',
            current_time
        ))
        
        logger.info(f"Caballo creado con ID específico: {horse_name_clean} -> {horse_id_clean}")
        return horse_name_clean
        
    except Exception as e:
        logger.error(f"Error al buscar/crear caballo {horse_name} con ID {horse_id}: {e}")
        return None

def find_or_create_horse(cursor, horse_name, sire_name=None, trainer_name=None):
    """
    Busca o crea un caballo en la tabla horses con IPA.
    Si no existe, lo crea con información básica.
    """
    if not horse_name or horse_name.strip() == '' or horse_name.lower() in ['unknown', 'n/a', 'none']:
        return None
    
    horse_name_clean = horse_name.strip()
    
    try:
        # Generar horse_id basado en el nombre
        horse_id = horse_name_clean.replace(' ', '_').replace("'", "").replace('.', '').replace(',', '')
        
        # Verificar si ya existe
        cursor.execute("SELECT horse_name FROM horses WHERE horse_id = %s", (horse_id,))
        result = cursor.fetchone()
        
        if result:
            return horse_name_clean
        
        # Si no existe, crearlo sin IPA (se generará desde el perfil)
        trainer_ipa = generate_english_ipa(trainer_name) if trainer_name else None
        current_time = datetime.now()
        
        insert_horse_query = """
        INSERT INTO horses (horse_id, horse_name, trainer, trainer_ipa, status, created_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (horse_id) DO NOTHING
        """
        cursor.execute(insert_horse_query, (
            horse_id, 
            horse_name_clean, 
            trainer_name, 
            trainer_ipa, 
            'active',
            current_time
        ))
        
        logger.info(f"Caballo creado: {horse_name_clean} -> {horse_id} (IPA se generará desde perfil)")
        return horse_name_clean
        
    except Exception as e:
        logger.error(f"Error al buscar/crear caballo {horse_name}: {e}")
        return None