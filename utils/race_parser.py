import re
import logging
from datetime import datetime
from utils.text_processing import clean_text

logger = logging.getLogger(__name__)

# Mapeos para construir race_id
TRACK_CODES = {
    "gulfstream-park": "GP",
    "santa-anita-park": "SA",
    "SANTA-ANIT": "SA",  # Variante abreviada usada en algunas URLs
    "keeneland": "KEE",
    "churchill-downs": "CD",
    "belmont-park": "BEL",
    "oaklawn-park": "OP",
    "del-mar": "DMR",
    "tampa-bay-downs": "TAM",
    "laurel-park": "LRL",
    "saratoga": "SAR",
    "monmouth-park": "MTH",
    "pimlico": "PIM",
    "aqueduct": "AQU",
    "woodbine": "WO",
    "thistledown": "TDN",
    # Añadir más mapeos según sea necesario
}

RACE_TYPE_ABBREVIATIONS = {
    "maiden special weight": "MSW",
    "allowance optional claiming": "AOC",
    "allowance": "ALW",
    "claiming": "CLM",
    "stakes": "STK",
    "handicap": "HCP",
    "starter optional claiming": "SOC",
    "starter allowance": "SA",
    "maiden claiming": "MCL",
    "optional claiming": "OC",
    "powder break s.": "PDRBS",
    "game face s.": "GFS",
    # Añadir más abreviaturas y ser lo más específico posible
}

def parse_race_url_data(url):
    """Parsea la URL para extraer track y fecha"""
    logger.info(f"Iniciando parse_race_url_data con URL: '{url}'")
    
    # Regex para .../entries-results/TRACK_SLUG/YYYY-MM-DD
    entries_regex = r'/entries-results/([^/]+)/(\d{4}-\d{2}-\d{2})'
    match_entries_page = re.search(entries_regex, url)
    logger.info(f"  Resultado de regex '{entries_regex}': {match_entries_page}")
    
    if match_entries_page:
        track_name_slug = match_entries_page.group(1)
        race_date_str = match_entries_page.group(2)
        logger.info(f"  URL parseada (entries): Slug='{track_name_slug}', DateStr='{race_date_str}'")
        
        # Convertir fecha string a objeto datetime
        try:
            race_date_obj = datetime.strptime(race_date_str, '%Y-%m-%d')
            return {'track_name_slug': track_name_slug, 'race_date_obj': race_date_obj}
        except ValueError as e:
            logger.error(f"Error al parsear fecha '{race_date_str}': {e}")
            return {'track_name_slug': track_name_slug, 'race_date_obj': None}

    # Regex para .../race/YYYY-MM-DD_TRACK_CODE_RACENUM
    specific_race_regex = r'/race/(\d{4}-\d{2}-\d{2})_([A-Z0-9]+)_(\d+)'
    match_specific_race = re.search(specific_race_regex, url)
    logger.info(f"  Resultado de regex '{specific_race_regex}': {match_specific_race}")
    
    if match_specific_race:
        race_date_str = match_specific_race.group(1)
        track_code = match_specific_race.group(2)
        # Intentar encontrar el track_name_slug desde el track_code (inverso de TRACK_CODES)
        track_name_slug = next((slug for slug, code in TRACK_CODES.items() if code == track_code), None)
        if not track_name_slug: # Fallback si no se encuentra
            track_name_slug = track_code # Usar el código como slug si no hay mapeo
            logger.info(f"    Track slug no encontrado en TRACK_CODES para '{track_code}', usando el código como slug.")
        logger.info(f"  URL parseada (specific race): DateStr='{race_date_str}', TrackCode='{track_code}' -> Slug='{track_name_slug}'")
        
        try:
            race_date_obj = datetime.strptime(race_date_str, '%Y-%m-%d')
            return {'track_name_slug': track_name_slug, 'race_date_obj': race_date_obj}
        except ValueError as e:
            logger.error(f"Error al parsear fecha '{race_date_str}': {e}")
            return {'track_name_slug': track_name_slug, 'race_date_obj': None}
        
    logger.warning(f"No se pudo parsear track/date de la URL: '{url}' con ninguno de los patrones.")
    return {'track_name_slug': None, 'race_date_obj': None}

def parse_race_title_data(race_title_full):
    """Parsea el título de la carrera para extraer número y tipo"""
    logger.info(f"Iniciando parse_race_title_data con título: '{race_title_full}'")
    
    # Nuevo patrón para el formato "Gulfstream Park Race # 1, 6:50 PM"
    # Busca "Race #" seguido de un número, posiblemente seguido de coma y tiempo
    match_new_format = re.search(r'Race\s*#\s*(\d+)', race_title_full, re.IGNORECASE)
    if match_new_format:
        race_number_str = match_new_format.group(1)
        # Para este formato, no hay descripción específica del tipo de carrera en el título
        logger.info(f"  Título parseado (formato nuevo): Num='{race_number_str}', Tipo='N/A'")
        return {'number': race_number_str, 'type_name': 'N/A'}
    
    # Intenta hacer match con "RACE #X - DESCRIPCIÓN" o "RACE X - DESCRIPCIÓN"
    # El (?:RACE|CARRERA) permite flexibilidad en el idioma. #? hace el # opcional.
    match_with_desc = re.search(r'(?:RACE|CARRERA)\s*#?\s*(\d+)\s*-\s*(.+)', race_title_full, re.IGNORECASE)
    if match_with_desc:
        race_number_str = match_with_desc.group(1)
        race_type_description = clean_text(match_with_desc.group(2))
        logger.info(f"  Título parseado (con descripción): Num='{race_number_str}', Tipo='{race_type_description}'")
        return {'number': race_number_str, 'type_name': race_type_description}

    # Si no, intenta hacer match solo con "RACE #X" o "RACE X" para obtener el número
    # Esto captura la parte como "Race #1" o "CARRERA 5"
    match_num_part = re.search(r'((?:RACE|CARRERA)\s*#?\s*\d+)', race_title_full, re.IGNORECASE)
    if match_num_part:
        race_number_section_str = match_num_part.group(1) # ej: "Race # 1"
        
        # Extrae solo los dígitos del número de la sección encontrada
        num_extract_match = re.search(r'\d+', race_number_section_str)
        race_number_str = num_extract_match.group(0) if num_extract_match else None

        if race_number_str:
            # Para la descripción, elimina la parte "RACE #X" del título completo y limpia los caracteres residuales.
            # El '1' en replace asegura que solo se reemplace la primera ocurrencia.
            description = clean_text(race_title_full.replace(race_number_section_str, '', 1).strip(" ,-"))
            if not description and race_title_full != race_number_section_str : # Si la descripción quedó vacía pero el título original era más largo
                 description = clean_text(race_title_full) #Fallback a título completo si la eliminación no dejó nada útil y había más texto

            logger.info(f"  Título parseado (solo número): Num='{race_number_str}', Tipo construido='{description}' (original: '{race_title_full}', parte removida: '{race_number_section_str}')")
            return {'number': race_number_str, 'type_name': description}
        else:
            # Esto no debería ocurrir si match_num_part tuvo éxito y contenía dígitos.
            logger.warning(f"  No se pudo extraer el número de '{race_number_section_str}' en el título '{race_title_full}'")
            # Devuelve None para el número, y el título completo como descripción.
            return {'number': None, 'type_name': clean_text(race_title_full)}

    # Si no se encuentra el patrón "RACE X" (ej. para nombres de Stakes como "THE PEGASUS STAKES")
    logger.info(f"  No se encontró patrón de número de carrera en el título: '{race_title_full}'. Se devuelve el título completo como descripción.")
    return {'number': None, 'type_name': clean_text(race_title_full)}

def generate_race_id(track_name_slug, race_date_obj, race_number, race_type):
    """Genera un ID único para la carrera"""
    try:
        track_code = TRACK_CODES.get(track_name_slug, track_name_slug.upper()[:10])  # Limitar a 10 caracteres
        date_str = race_date_obj.strftime('%Y%m%d') if race_date_obj else 'NODATE'
        race_num_str = str(race_number) if race_number and race_number != 'N/A' else 'UNK'
        
        # Simplificar el tipo de carrera para el ID
        race_type_abbr = 'UNK'
        if race_type and race_type != 'N/A':
            race_type_lower = race_type.lower()
            for full_type, abbr in RACE_TYPE_ABBREVIATIONS.items():
                if full_type in race_type_lower:
                    race_type_abbr = abbr
                    break
        
        race_id = f"{track_code}_{date_str}_R{race_num_str}_{race_type_abbr}"
        logger.info(f"Race ID generado: {race_id}")
        return race_id
    except Exception as e:
        logger.error(f"Error generando race_id: {e}")
        return None 