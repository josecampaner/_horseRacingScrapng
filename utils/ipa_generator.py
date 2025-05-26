# utils/ipa_generator.py - Generador de pronunciaciones IPA con traducción automática

import re
import logging

logger = logging.getLogger(__name__)

# Importar eng-to-ipa para traducción automática de inglés americano (CMU Dictionary)
try:
    import eng_to_ipa as ipa_converter
    ENG_TO_IPA_AVAILABLE = True
    logger.info("eng-to-ipa cargado exitosamente para traducción automática de IPA (inglés americano)")
except ImportError:
    ENG_TO_IPA_AVAILABLE = False
    logger.warning("eng-to-ipa no disponible, usando solo traducciones manuales")

def generate_english_ipa(text):
    """Generar pronunciación IPA para inglés americano usando CMU Dictionary"""
    if not text:
        return None
    
    # Diccionario de pronunciaciones comunes en inglés americano (sin barras)
    english_ipa_dict = {
        'Andrea': 'ænˈdriːə',
        'Thunder': 'ˈθʌndər',
        'Lightning': 'ˈlaɪtnɪŋ',
        'Storm': 'stɔːrm',
        'Spirit': 'ˈspɪrɪt',
        'Champion': 'ˈtʃæmpiən',
        'Victory': 'ˈvɪktəri',
        'Joseph': 'ˈdʒoʊzəf',
        'Scott': 'skɒt',
        'Pierce': 'pɪərs',
        'Smith': 'smɪθ',
        'Johnson': 'ˈdʒɑːnsən',
        'Williams': 'ˈwɪljəmz',
        'Brown': 'braʊn',
        'Jones': 'dʒoʊnz',
        'Amador': 'æmædɑːr',
        'Merey': 'mereɪ',
        'Sanchez': 'sænchez',
        'Michael': 'mɪchæel',
        'Lerman': 'lermæn',
        'John': 'jɑːhn',
        'Vinson': 'vɪnsɑːn',
        'Michelle': 'mɪchell',
        'Hemingway': 'hemɪngwæy'
    }
    
    # Primero buscar en el diccionario manual
    if text in english_ipa_dict:
        return f'/{english_ipa_dict[text]}/'
    
    # Si eng-to-ipa está disponible, usar traducción automática (inglés americano)
    if ENG_TO_IPA_AVAILABLE:
        try:
            # eng-to-ipa ya devuelve IPA sin barras y con espacios correctos
            auto_ipa = ipa_converter.convert(text, stress_marks='both')
            if auto_ipa and auto_ipa.strip() and not auto_ipa.endswith('*'):
                # Limpiar cualquier asterisco y espacios extra
                clean_ipa = auto_ipa.replace('*', '').strip()
                return f'/{clean_ipa}/'
        except Exception as e:
            logger.warning(f"Error en traducción automática para '{text}': {e}")
    
    # Fallback: generar IPA básico palabra por palabra
    words = text.split()
    ipa_parts = []
    
    for word in words:
        # Buscar cada palabra en el diccionario
        if word in english_ipa_dict:
            ipa_parts.append(english_ipa_dict[word])
        else:
            # Generar IPA básico para palabras desconocidas
            basic_ipa = generate_basic_english_ipa(word)
            ipa_parts.append(basic_ipa)
    
    # Unir todas las partes con espacios y agregar barras solo al principio y final
    return f'/{" ".join(ipa_parts)}/'

def generate_basic_english_ipa(word):
    """Generar IPA básico para palabras en inglés no encontradas en el diccionario"""
    if not word:
        return ""
    
    # Conversiones básicas de inglés a IPA
    ipa_word = word.lower()
    
    # Reglas básicas de conversión
    replacements = [
        ('ch', 'tʃ'),
        ('sh', 'ʃ'),
        ('th', 'θ'),
        ('ng', 'ŋ'),
        ('ph', 'f'),
        ('ck', 'k'),
        ('qu', 'kw'),
        ('x', 'ks'),
        ('c', 'k'),
        ('y', 'i'),
        ('j', 'dʒ'),
        ('w', 'w'),
        ('r', 'r'),
        ('l', 'l'),
        ('m', 'm'),
        ('n', 'n'),
        ('p', 'p'),
        ('b', 'b'),
        ('t', 't'),
        ('d', 'd'),
        ('k', 'k'),
        ('g', 'g'),
        ('f', 'f'),
        ('v', 'v'),
        ('s', 's'),
        ('z', 'z'),
        ('h', 'h'),
        ('a', 'æ'),
        ('e', 'e'),
        ('i', 'ɪ'),
        ('o', 'ɑː'),
        ('u', 'ʌ')
    ]
    
    for old, new in replacements:
        ipa_word = ipa_word.replace(old, new)
    
    return ipa_word

def generate_french_ipa(text):
    """Generar pronunciación IPA para francés"""
    if not text:
        return None
    
    # Diccionario de pronunciaciones francesas
    french_ipa_dict = {
        'Pierre': 'pjɛʁ',
        'Jean': 'ʒɑ̃',
        'Marie': 'maʁi',
        'Antoine': 'ɑ̃twan',
        'François': 'fʁɑ̃swa'
    }
    
    # Primero buscar en el diccionario manual
    if text in french_ipa_dict:
        return f'/{french_ipa_dict[text]}/'
    
    # Fallback básico
    return f'/fʁɑ̃sɛ {text.lower()}/'

def generate_japanese_ipa(text):
    """Generar pronunciación IPA para japonés"""
    if not text:
        return None
    
    # Diccionario de pronunciaciones japonesas
    japanese_ipa_dict = {
        'Takeshi': 'takeʃi',
        'Hiroshi': 'hiɾoʃi',
        'Yuki': 'juki'
    }
    
    if text in japanese_ipa_dict:
        return f'/{japanese_ipa_dict[text]}/'
    
    # Fallback básico para japonés
    return f'/dʒæpəniːz {text.lower()}/'