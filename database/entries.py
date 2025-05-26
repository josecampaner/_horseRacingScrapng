import logging
import urllib.parse
from utils.ipa_generator import generate_english_ipa

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
        insert_sire_query = """
        INSERT INTO horses (horse_id, horse_name, status)
        VALUES (%s, %s, %s)
        ON CONFLICT (horse_id) DO NOTHING
        """
        cursor.execute(insert_sire_query, (sire_id, sire_name_clean, 'sire'))
        
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
        # Generar trainer_id basado en el nombre
        trainer_id = trainer_name_clean.replace(' ', '_').replace("'", "").replace('.', '').replace(',', '')
        
        # Verificar si ya existe
        cursor.execute("SELECT trainer_name FROM trainers WHERE trainer_id = %s", (trainer_id,))
        result = cursor.fetchone()
        
        if result:
            return trainer_name_clean
        
        # Si no existe, crearlo con IPA básico
        trainer_ipa = generate_english_ipa(trainer_name_clean) if trainer_name_clean else None
        
        insert_trainer_query = """
        INSERT INTO trainers (trainer_id, trainer_name, trainer_name_ipa)
        VALUES (%s, %s, %s)
        ON CONFLICT (trainer_id) DO NOTHING
        """
        cursor.execute(insert_trainer_query, (trainer_id, trainer_name_clean, trainer_ipa))
        
        logger.info(f"Trainer creado: {trainer_name_clean} -> {trainer_id} (IPA: {trainer_ipa})")
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
        # Generar jockey_id basado en el nombre
        jockey_id = jockey_name_clean.replace(' ', '_').replace("'", "").replace('.', '').replace(',', '')
        
        # Verificar si ya existe
        cursor.execute("SELECT jockey_name FROM jockeys WHERE jockey_id = %s", (jockey_id,))
        result = cursor.fetchone()
        
        if result:
            return jockey_name_clean
        
        # Si no existe, crearlo con IPA básico
        jockey_ipa = generate_english_ipa(jockey_name_clean) if jockey_name_clean else None
        
        insert_jockey_query = """
        INSERT INTO jockeys (jockey_id, jockey_name, jockey_name_ipa)
        VALUES (%s, %s, %s)
        ON CONFLICT (jockey_id) DO NOTHING
        """
        cursor.execute(insert_jockey_query, (jockey_id, jockey_name_clean, jockey_ipa))
        
        logger.info(f"Jockey creado: {jockey_name_clean} -> {jockey_id} (IPA: {jockey_ipa})")
        return jockey_name_clean
        
    except Exception as e:
        logger.error(f"Error al buscar/crear jockey {jockey_name}: {e}")
        return None 