import re
import logging

logger = logging.getLogger(__name__)

def clean_text(text):
    """Limpia texto eliminando espacios extra"""
    if text:
        text = re.sub(r'\s+', ' ', text).strip()
    return text

def clean_race_type(race_type_text):
    """Limpia el tipo de carrera eliminando cantidades monetarias"""
    if not race_type_text or race_type_text == 'N/A':
        return race_type_text
    
    # Eliminar cantidades monetarias como $8,000, $10,000, $12, 500, etc.
    # Patrón más robusto para capturar cantidades con espacios y comas
    cleaned_text = re.sub(r'\$\s*[\d,\s]+', '', race_type_text)
    
    # Limpiar espacios extra y comas al inicio y final
    cleaned_text = re.sub(r'^[,\s]+', '', cleaned_text)
    cleaned_text = re.sub(r'[,\s]+$', '', cleaned_text)
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
    
    return cleaned_text

def extract_age_from_conditions(conditions_text):
    """Extrae la información de edad de las condiciones de la carrera"""
    if not conditions_text or conditions_text == 'N/A':
        return 'N/A'
    
    # Patrones para extraer edad
    age_patterns = [
        r'(\d+)\s+Year\s+Olds?\s+And\s+Up',  # "3 Year Olds And Up"
        r'(\d+)\s+Year\s+Olds?',             # "2 Year Olds"
        r'(\d+)\s+YO\s+And\s+Up',            # "3 YO And Up"
        r'(\d+)\s+YO',                       # "2 YO"
    ]
    
    for pattern in age_patterns:
        match = re.search(pattern, conditions_text, re.IGNORECASE)
        if match:
            age = match.group(1)
            if 'and up' in conditions_text.lower():
                return f"{age}+ años"
            else:
                return f"{age} años"
    
    # Si no encuentra patrón específico, buscar solo números seguidos de "year"
    general_match = re.search(r'(\d+).*year', conditions_text, re.IGNORECASE)
    if general_match:
        return f"{general_match.group(1)} años"
    
    return 'N/A'

def clean_conditions_remove_age(conditions_text):
    """Elimina la información de edad de las condiciones"""
    if not conditions_text or conditions_text == 'N/A':
        return conditions_text
    
    # Patrones para eliminar información de edad
    age_patterns = [
        r'\|\s*\d+\s+Year\s+Olds?\s+And\s+Up',  # "| 3 Year Olds And Up"
        r'\|\s*\d+\s+Year\s+Olds?',             # "| 2 Year Olds"
        r'\d+\s+Year\s+Olds?\s+And\s+Up\s*\|',  # "3 Year Olds And Up |"
        r'\d+\s+Year\s+Olds?\s*\|',             # "2 Year Olds |"
        r'\d+\s+Year\s+Olds?\s+And\s+Up',       # "3 Year Olds And Up" (sin |)
        r'\d+\s+Year\s+Olds?',                  # "2 Year Olds" (sin |)
    ]
    
    cleaned_text = conditions_text
    for pattern in age_patterns:
        cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE)
    
    # Limpiar espacios extra, comas y pipes duplicados
    cleaned_text = re.sub(r'\|\s*\|', '|', cleaned_text)  # || -> |
    cleaned_text = re.sub(r'^\s*\|\s*', '', cleaned_text)  # | al inicio
    cleaned_text = re.sub(r'\s*\|\s*$', '', cleaned_text)  # | al final
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
    
    return cleaned_text if cleaned_text else 'N/A'

def extract_purse_value(purse_text):
    """Extrae el valor numérico de la bolsa de premios"""
    if purse_text is None:
        return None
    match = re.search(r'[\$€£]?([\\d,]+(?:\\.\\d{2})?)', purse_text)
    if match:
        try:
            return int(match.group(1).replace(',', ''))
        except ValueError:
            logger.warning(f"No se pudo convertir la bolsa '{match.group(1)}' a entero.")
            return None
    return None 